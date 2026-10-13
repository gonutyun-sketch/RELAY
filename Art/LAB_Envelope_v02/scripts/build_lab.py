"""RELAY laboratory envelope. Standalone Blender authoring; never writes Unity.

Dimensions are expressed in Unity metres. P swaps Y/Z, matching existing RELAY
art exports. Unity instance uses yaw 180; source coordinates remain inspectable.
"""
import bpy, bmesh, math, json, hashlib, random
from pathlib import Path
from mathutils import Vector, Matrix

assert bpy.app.background
OUT = Path(__file__).resolve().parents[1]
PROJECT = Path(r'C:\Users\gonut\School_p2')
assert not OUT.is_relative_to(PROJECT)
for folder in ('exports', 'previews', 'checks'):
    (OUT / folder).mkdir(parents=True, exist_ok=True)
scene_path = PROJECT / 'Assets/Scenes/Startup_Graybox.unity'
scene_hash = hashlib.sha256(scene_path.read_bytes()).hexdigest()
layout = json.loads((OUT / 'checks/scene_layout.json').read_text(encoding='utf8'))
assert scene_hash == layout['sha256'], 'Saved scene changed after dimensional audit'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
P = Matrix(((1,0,0),(0,0,1),(0,1,0)))
source = bpy.data.collections.new('01_EDITABLE_LAB_SURFACES')
scene.collection.children.link(source)
exports = bpy.data.collections.new('02_GAME_EXPORTS')
scene.collection.children.link(exports)
materials = []
material_specs = []

def srgb(h):
    rgb = [int(h[i:i+2], 16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb)

def material(name, color, metallic, roughness, texture=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*srgb(color),1)
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = m.diffuse_color
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = roughness
    spec = dict(name=name, color='#'+color, metallic=metallic, smoothness=1-roughness, surface='Opaque')
    if texture:
        for kind, socket, space in [('BaseColor','Base Color','sRGB'),('Roughness','Roughness','Non-Color'),('Normal','Normal','Non-Color')]:
            file = OUT / 'textures' / (name+'_'+kind+'.png')
            assert file.exists(), file
            im = bpy.data.images.load(str(file), check_existing=True)
            im.colorspace_settings.name = space
            tex = m.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = im
            tex.extension = 'REPEAT'
            if kind == 'Normal':
                normal = m.node_tree.nodes.new('ShaderNodeNormalMap')
                normal.inputs['Strength'].default_value = .6
                m.node_tree.links.new(tex.outputs['Color'], normal.inputs['Color'])
                m.node_tree.links.new(normal.outputs['Normal'], bs.inputs['Normal'])
            else:
                m.node_tree.links.new(tex.outputs['Color'], bs.inputs[socket])
        spec['base_map'] = 'textures/'+name+'_BaseColor.png'
        spec['normal_map'] = 'textures/'+name+'_Normal.png'
        spec['metallic_smoothness_map'] = 'textures/'+name+'_MetallicSmoothness.png'
    material_specs.append(spec)
    materials.append(m)
    return len(materials)-1

concrete = material('RLYR_Concrete','85847C',0,.88,True)
floor = material('RLYR_Floor','4C524F',0,.68,True)
paint = material('RLYR_Paint','616A61',.03,.69,True)
steel = material('RLYR_Steel','414947',.88,.59,True)
dark = material('RLYR_Seam','1C2422',0,.92)
edge = material('RLYR_BareMetal','828780',.80,.38)
ochre = material('RLYR_Ochre','A28A53',.02,.66)

class Part:
    def __init__(self, name, bevel=.002):
        self.name=name; self.verts=[]; self.faces=[]; self.mats=[]; self.elements=[]; self.bevel=bevel
    def mesh(self, name, verts, faces, mat):
        start=len(self.verts)
        self.verts.extend(tuple(v) for v in verts)
        self.faces.extend(tuple(start+i for i in f) for f in faces)
        self.mats.extend([mat]*len(faces))
        self.elements.append(dict(name=name, first_face=len(self.faces)-len(faces), face_count=len(faces),
                                  min=[min(v[i] for v in verts) for i in range(3)],
                                  max=[max(v[i] for v in verts) for i in range(3)]))
    def box(self,name,pos,size,mat):
        x,y,z=pos; a,b,c=(s/2 for s in size)
        self.mesh(name,[(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                        (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)],mat)
    def tube(self,name,points,radius,mat,sides=10,closed=False):
        points=[Vector(p) for p in points]; verts=[]
        for i,p in enumerate(points):
            tangent=(points[(i+1)%len(points)]-points[(i-1)%len(points)]).normalized() if closed else (points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
            ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
            u=tangent.cross(ref).normalized(); w=tangent.cross(u).normalized()
            for j in range(sides):
                a=j*math.tau/sides; verts.append(p+radius*(u*math.cos(a)+w*math.sin(a)))
        faces=[] if closed else [tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+j for j in range(sides))]
        for i in range(len(points) if closed else len(points)-1):
            ni=(i+1)%len(points)
            for j in range(sides): faces.append((i*sides+j,i*sides+(j+1)%sides,ni*sides+(j+1)%sides,ni*sides+j))
        self.mesh(name,verts,faces,mat)
    def cyl(self,name,pos,r,depth,mat,axis=(0,1,0),sides=10):
        a=Vector(axis)*depth/2; p=Vector(pos)
        self.tube(name,[p-a,p+a],r,mat,sides)
    def bolt(self,name,pos,axis=(0,1,0),r=.010):
        self.cyl(name, pos, r*1.4, .003, steel,axis,10)
        p=Vector(pos)+Vector(axis)*.004
        self.cyl(name+'_hex',p,r,.007,edge,axis,6)
    def finish(self):
        me=bpy.data.meshes.new(self.name+'_editable')
        me.from_pydata([P@Vector(v) for v in self.verts],[],self.faces); me.update()
        for m in materials: me.materials.append(m)
        for p,mi in zip(me.polygons,self.mats): p.material_index=mi
        bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
        # Dominant-axis mapping in world metres, consistent 2 m textile scale.
        uv=me.uv_layers.new(name='UV_Metre_2m')
        for poly in me.polygons:
            n=P@poly.normal; a=max(range(3),key=lambda i:abs(n[i]))
            for li in poly.loop_indices:
                q=P@me.vertices[me.loops[li].vertex_index].co
                if a==1: u,w=q.x,q.z
                elif a==0: u,w=q.z,q.y
                else: u,w=q.x,q.y
                uv.data[li].uv=(u/2,w/2)
        o=bpy.data.objects.new(self.name,me); source.objects.link(o)
        o['role']='Visual replacement only. Keep existing Unity colliders.'
        if self.bevel:
            # Radius on visible manufactured corners only. Do not bevel thousands
            # of tiny bolt/cylinder edges that contribute no visible silhouette.
            edgefaces={}
            for poly in me.polygons:
                vv=list(poly.vertices)
                for i in range(len(vv)):
                    key=tuple(sorted((vv[i],vv[(i+1)%len(vv)])))
                    edgefaces.setdefault(key,[]).append(poly.normal.copy())
            weights=me.attributes.new('bevel_weight_edge','FLOAT','EDGE')
            for e in me.edges:
                normals=edgefaces.get(tuple(sorted(e.vertices)),[])
                length=(me.vertices[e.vertices[0]].co-me.vertices[e.vertices[1]].co).length
                if length>.08 and len(normals)==2 and normals[0].dot(normals[1])<.4:
                    weights.data[e.index].value=1
            b=o.modifiers.new('Small manufactured edge radius','BEVEL'); b.width=self.bevel; b.segments=1; b.use_clamp_overlap=True; b.limit_method='WEIGHT'
            n=o.modifiers.new('Corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True; n.weight=40
        o['logical_piece_count']=len(self.elements)
        return o

parts=[]
def new(name, bevel=.002):
    p=Part(name,bevel); parts.append(p); return p

# FLOOR: full solid backplate below the top; exact Y=0 walking plane.
f=new('LAB_Floor',.0018)
f.box('Continuous solid floor backing',(0,-.29,-2),(16,.42,16),dark)
# Break outer strips and centre into real rectangular slabs. No floating decals.
xedges=[-8,-7.24,-6.64,-4.98,-3.32,-1.72,0,1.72,3.32,4.98,6.64,7.24,8]
zedges=[-10,-9.48]+[-9.48+i*1.523 for i in range(1,11)]+[6]
for ix,(x0,x1) in enumerate(zip(xedges,xedges[1:])):
    for iz,(z0,z1) in enumerate(zip(zedges,zedges[1:])):
        x=(x0+x1)/2; z=(z0+z1)/2
        if abs(x)>6.64 and abs(x)<7.24: continue
        # Existing doorway apron is retained; overlap is put safely below it.
        if z1<=-9.48 and x0<1.72 and x1>-1.72: continue
        f.box('Floor slab %02d_%02d'%(ix,iz),(x,-.018,z),(x1-x0-.012,.036,z1-z0-.012),floor)
for side in (-1,1):
    x=side*6.94
    f.box('Service channel shadow bed',(x,-.054,-2),(.60,.028,16),dark)
    for dx in (-.285,.285): f.box('Channel edge rail',(x+dx,-.009,-2),(.025,.018,16),steel)
    for dx in (-.270,.270): f.box('Continuous grate seating ledge',(x+dx,-.032,-2),(.080,.032,16),steel)
    for k in range(16):
        z=-9.5+k
        for dx in (-.255,.255): f.box('Removable grate longitudinal bearer',(x+dx,-.022,z),(.030,.040,.978),steel)
        for dz in (-.477,.477): f.box('Removable grate end',(x,-.008,z+dz),(.54,.016,.022),steel)
        for j in range(11):
            f.box('Cast grate tread',(x,-.010,z-.425+j*.085),(.535,.020,.018),steel)
        for dx in (-.23,.23):
            for dz in (-.437,.437): f.bolt('Grate captive screw',(x+dx,-.008,z+dz),r=.006)

# WALLS: backing fills seam depth; lower removable service panels; upper concrete.
def wall(name,axis,at,intervals,normal):
    p=new(name,.0035)
    def coord(u,y,d): return (at+normal*d,y,u) if axis=='X' else (u,y,at+normal*d)
    def size(w,h,t): return (t,h,w) if axis=='X' else (w,h,t)
    direction=(normal,0,0) if axis=='X' else (0,0,normal)
    for a,b in intervals:
        width=b-a
        p.box('Solid wall backing',coord((a+b)/2,3,-.262),size(width,6,.476),dark)
        count=max(1,math.ceil(width/2))
        for i in range(count):
            u0=a+i*width/count; u1=a+(i+1)*width/count; u=(u0+u1)/2; w=u1-u0-.014
            for y,h in ((2.8,2.80),(5.10,1.77)):
                p.box('Cast concrete bay',coord(u,y,-.104),size(w,h,.22),concrete)
                for du in (-w*.34,w*.34):
                    p.cyl('Formwork tie recess',coord(u+du,y-.28,.0075),.014,.003,dark,direction,12)
            p.box('Lower removable service skin',coord(u,.85,.013),size(w-.012,1.04,.028),paint)
            for du in (-w/2+.08,w/2-.08):
                for y in (.40,1.30): p.bolt('Panel captive fastener',coord(u+du,y,.028),direction,.007)
        p.box('Skirting plinth',coord((a+b)/2,.15,.022),size(width,.30,.050),steel)
        p.box('Lower panel cap rail',coord((a+b)/2,1.40,.023),size(width,.045,.052),steel)
        p.box('Concrete construction joint rail',coord((a+b)/2,4.215,.014),size(width,.026,.030),steel)
        p.box('Ceiling closure angle',coord((a+b)/2,5.955,.035),size(width,.09,.078),steel)
    return p,coord,size

left,lc,ls=wall('LAB_Wall_Left','X',-7.75,[(-10,6)],1)
right,rc,rs=wall('LAB_Wall_Right','X',7.75,[(-10,6)],-1)
back,bc,bs=wall('LAB_Wall_Back','Z',5.75,[(-7.75,7.75)],-1)
front,fc,fs=wall('LAB_Wall_Exit','Z',-9.75,[(-8,-1.2),(1.2,8)],1)
# Door lintel above 3 m; not a solid full-width wall over the doorway.
front.box('Lintel recessed backing',(0,4.5,-9.99),(2.4,3,.48),dark)
front.box('Lintel concrete',(0,4.5,-9.854),(2.388,2.99,.22),concrete)
for x in (-1.26,1.26):
    front.box('Door jamb folded edge',(x,1.5,-9.715),(.12,3,.070),steel)
    for y in (.20,.65,1.25,1.85,2.45,2.80): front.bolt('Jamb bolt',(x,y,-9.679),(0,0,1),.011)
front.box('Lintel face edge',(0,3.06,-9.715),(2.64,.12,.070),steel)
front.box('Lintel ceiling closure',(0,5.955,-9.715),(2.4,.09,.078),steel)

# Side-wall air return housings: shallow and above the player head height.
for p,coord,size,normal in ((left,lc,ls,1),(right,rc,rs,-1)):
    for z in (-6.9,1.05):
        p.box('Wall return outer frame',coord(z,2.65,.033),size(1.12,.72,.066),steel)
        p.box('Vent shadow',coord(z,2.65,.069),size(.98,.58,.008),dark)
        for j in range(9): p.box('Vent louvre',coord(z,2.39+j*.065,.079),size(.98,.035,.018),paint)
        for dz in (-.51,.51):
            for y in (2.34,2.96): p.bolt('Return grille bolt',coord(z+dz,y,.067),(normal,0,0),.008)

# CEILING: exact top datum Y=6, six light footprints remain clear at x +/-4.
c=new('LAB_Ceiling',.0025)
c.box('Sealed ceiling plate',(0,6.164,-2),(16,.272,16),dark)
for ix in range(8):
    for iz in range(8):
        x=-7+2*ix; z=-9+2*iz
        c.box('Overhead steel cassette',(x,6.014,z),(1.985,.028,1.985),paint)
        for dx in (-.88,.88):
            for dz in (-.88,.88):
                xx,zz=x+dx,z+dz
                if any(abs(xx-lx)<.32 and abs(zz-lz)<.96 for lx in (-4,4) for lz in (-6.5,-2,2.5)): continue
                c.bolt('Overhead cassette screw',(xx,6.000,z+dz),(0,-1,0),.006)
# Long perimeter ledges close corners without another row of false lamps.
for x in (-7.68,7.68): c.box('Ceiling side closure',(x,5.93,-2),(.14,.14,15.5),steel)
for z in (-9.68,5.68): c.box('Ceiling end closure',(0,5.93,z),(15.5,.14,.14),steel)

# STRUCTURE: same footprint as existing four posts and two beams.
s=new('LAB_Structure',.004)
for x in (-7.55,7.55):
    for z in (-5,5):
        s.box('Pillar web',(x,3,z),(.10,6,.56),steel)
        for dx in (-.165,.165): s.box('Pillar flange',(x+dx,3,z),(.07,6,.65),steel)
        s.box('Pillar shoe',(x,.055,z),(.43,.11,.70),steel)
        for dz in (-.25,.25):
            for dx in (-.17,.17): s.bolt('Pillar base anchor',(x+dx,.111,z+dz),r=.015)
        for y in (.46,1.42,2.65,3.85,5.48):
            s.box('Column joint plate',(x, y,z-.336),(.35,.27,.022),paint)
            for dx in (-.125,.125):
                for dy in (-.084,.084): s.bolt('Column splice bolt',(x+dx,y+dy,z-.348),(0,0,-1),.010)
for z in (-5,5):
    s.box('Cross girder web',(0,5.85,z),(14.7,.23,.06),steel)
    for y in (5.7175,5.9825): s.box('Cross girder flange',(0,y,z),(14.7,.035,.65),steel)
    for x in (-7.15,-5.6,-3.7,-1.8,0,1.8,3.7,5.6,7.15):
        s.box('Girder transverse stiffener',(x,5.85,z),(.035,.23,.57),steel)

# SERVICES: side overhead trays, pipes, brackets and restrained ochre couplings.
t=new('LAB_Services',.0016)
def smooth_path(points, radius=.25, steps=6):
    ps=[Vector(a) for a in points]; out=[ps[0]]
    for i in range(1,len(ps)-1):
        p=ps[i]; d=min(radius,(p-ps[i-1]).length*.4,(ps[i+1]-p).length*.4)
        a=p+(ps[i-1]-p).normalized()*d; b=p+(ps[i+1]-p).normalized()*d
        out.append(a)
        for j in range(1,steps+1):
            q=j/steps; out.append((1-q)**2*a+2*q*(1-q)*p+q*q*b)
    return out+[ps[-1]]
network = dict(closed_runs=[], terminated_runs=[], support_checks=[])

def rounded_rectangle(x, z0, z1, y, radius, steps=12):
    """Closed planar centreline, no coincident start/end rings or cap seam."""
    points=[]
    for cx,cz,start in [(x-radius,z0+radius,-90),(x-radius,z1-radius,0),
                        (-x+radius,z1-radius,90),(-x+radius,z0+radius,180)]:
        for i in range(steps+1):
            a=math.radians(start+90*i/steps)
            points.append(Vector((cx+radius*math.cos(a),y,cz+radius*math.sin(a))))
    return points

def closed_tube(name, points, radius, mat, sides=16):
    t.tube(name,points,radius,mat,sides,closed=True)
    network['closed_runs'].append(dict(name=name,points=[list(p) for p in points],radius=radius))

def rectangular_run(name, points, width, height, mat, closed=False):
    points=[Vector(p) for p in points]; vv=[]; ff=[]
    for i,p in enumerate(points):
        tangent=(points[(i+1)%len(points)]-points[(i-1)%len(points)]).normalized() if closed else (points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        across=tangent.cross(Vector((0,1,0))).normalized()
        for w,h in [(-1,-1),(1,-1),(1,1),(-1,1)]: vv.append(p+across*(w*width/2)+Vector((0,h*height/2,0)))
    for i in range(len(points) if closed else len(points)-1):
        j=(i+1)%len(points)
        for k in range(4): ff.append((4*i+k,4*i+(k+1)%4,4*j+(k+1)%4,4*j+k))
    if not closed: ff.extend([(3,2,1,0),tuple(4*(len(points)-1)+k for k in range(4))])
    t.mesh(name,vv,ff,mat)

def bounds(pos,size): return [[pos[i]-size[i]/2 for i in range(3)],[pos[i]+size[i]/2 for i in range(3)]]

def terminal_tube(name,points,radius,mat,receiver_a,receiver_b):
    t.tube(name,points,radius,mat,12)
    network['terminated_runs'].append(dict(name=name,points=[list(p) for p in points],radius=radius,
        receiver_start=receiver_a,receiver_end=receiver_b))

# Two continuous ring mains. The back and entrance walls are connected by
# rounded elbows, and no pipe terminates in the room or inside an arbitrary wall.
for line in range(2):
    x=7.05-line*.27; y=4.78+line*.27; z0=-9.06+line*.27; z1=4.76-line*.27
    rr=.055 if line==0 else .038
    points=rounded_rectangle(x,z0,z1,y,.42)
    closed_tube('Continuous ring main %d'%line,points,rr,paint)
    for side in (-1,1):
        for z in (-7.5,-4.1,-.7,2.7):
            t.cyl('Pipe sleeve coupling',(side*x,y,z),rr+.015,.13,steel,(0,0,1),16)
            t.cyl('Coupling witness band',(side*x,y,z),rr+.016,.018,ochre,(0,0,1),16)
    for z in (z0,z1):
        for xx in (-4,0,4):
            t.cyl('End wall pipe coupling',(xx,y,z),rr+.015,.13,steel,(1,0,0),16)

# A wall-mounted utility manifold supplies the rings through proper tee takeoffs.
manifold_pos=(-7.555,3.78,-6.35); manifold_size=(.38,.82,1.02)
t.box('Utility manifold mounted enclosure',manifold_pos,manifold_size,paint)
t.box('Manifold service cover',(-7.351,3.78,-6.35),(.030,.72,.90),steel)
for y in (3.48,4.08):
    for z in (-6.73,-5.97): t.bolt('Manifold cover screw',(-7.335,y,z),(1,0,0),.008)
for line,z in [(0,-6.60),(1,-6.10)]:
    x=-7.05+line*.27; y=4.78+line*.27; yy=4.04-line*.39; rr=.055 if line==0 else .038
    path=smooth_path([(x,y,z),(x,yy,z),(-7.40,yy,z)],.16,10)
    terminal_tube('Ring manifold branch %d'%line,path,rr,paint,
                  dict(kind='pipe_tee',position=[x,y,z],radius=rr),
                  dict(kind='enclosure',bounds=bounds(manifold_pos,manifold_size)))
    t.cyl('Tee body sleeve',(x,y,z),rr+.018,.20,steel,(0,0,1),16)
    t.cyl('Manifold wall port',(-7.35,yy,z),rr+.023,.13,edge,(1,0,0),16)

# Anchored wall brackets support both pipe heights. Brackets at the two columns
# mount to the column face; other brackets mount directly into the concrete.
for side in (-1,1):
    for z in (-8,-5,-2,1,3.4):
        wall_x=7.335 if z==-5 else 7.727
        t.box('Pipe support anchor plate',(side*wall_x,4.92,z),(.042,.64,.18),steel)
        t.box('Pipe support cantilever',(side*(wall_x+6.64)/2,4.64,z),(wall_x-6.64,.05,.13),steel)
        for yy in (4.70,5.14): t.bolt('Pipe support anchor bolt',(side*(wall_x-.022),yy,z),(-side,0,0),.011)
        for line in range(2):
            x=side*(7.05-line*.27); y=4.78+line*.27; r=.068 if line==0 else .050
            top=y-r+.003
            t.box('Pipe clamp pedestal',(x,(4.66+top)/2,z),(.10,top-4.66,.09),steel)
            t.cyl('Pipe captive saddle',(x,y,z),r,.075,steel,(0,0,1),16)
            network['support_checks'].append(dict(name='pipe_saddle',gap=top-(y-r),must='overlap'))
# Cross-wall pipe supports provide load paths for the newly connected sections.
for end in ('front','back'):
    wall_z=-9.727 if end=='front' else 5.727
    for x in (-4,0,4):
        positions=[-9.06,-8.79] if end=='front' else [4.76,4.49]
        tip=min(positions)-.15 if end=='back' else max(positions)+.15
        t.box('End wall anchor plate',(x,4.92,wall_z),(.18,.64,.042),steel)
        t.box('End wall pipe cantilever',(x,4.64,(wall_z+tip)/2),(.13,.05,abs(wall_z-tip)),steel)
        for line,z in enumerate(positions):
            y=4.78+line*.27; r=.068 if line==0 else .050; top=y-r+.003
            t.box('End wall clamp pedestal',(x,(4.66+top)/2,z),(.09,top-4.66,.10),steel)
            t.cyl('End wall saddle',(x,y,z),r,.075,steel,(1,0,0),16)

# Closed cable ladder with real curved rails and rungs; four continuous cable
# loops lie on the rung top (5.435) instead of hovering above them.
for offset in (-.23,.23):
    path=rounded_rectangle(6.30+offset,-8.78-offset,4.15+offset,5.46,.65+offset)
    rail_name='Continuous formed cable tray rail '+str(offset)
    rectangular_run(rail_name,path,.025,.10,steel,True)
    network['closed_runs'].append(dict(name=rail_name,points=[list(p) for p in path],profile='rectangle'))
tray_path=rounded_rectangle(6.30,-8.78,4.15,5.42,.65,20)
segments=[(tray_path[(i+1)%len(tray_path)]-a).length for i,a in enumerate(tray_path)]
total=sum(segments); count=math.ceil(total/.28)
for sample in range(count):
    distance=sample*total/count
    for i,length in enumerate(segments):
        if distance<=length:
            a=tray_path[i]; direction=(tray_path[(i+1)%len(tray_path)]-a).normalized()
            p=a+direction*distance; across=direction.cross(Vector((0,1,0)))
            rectangular_run('Tray attached cross rung',[p-across*.243,p+across*.243],.04,.03,steel)
            break
        distance-=length
for offset in (-.15,-.05,.05,.15):
    path=rounded_rectangle(6.30+offset,-8.78-offset,4.15+offset,5.459,.65+offset)
    closed_tube('Continuous insulated cable '+str(offset),path,.024,dark,8)
network['support_checks'].append(dict(name='cables_rest_on_rungs',gap=(5.459-.024)-(5.42+.015),must='contact'))

def tray_hanger(x,z,along_x=False):
    anchor_y=5.700 if abs(z+5)<.33 else 6.0
    t.box('Tray support crossbar',(x,5.40,z),(.70 if not along_x else .09,.03,.70 if along_x else .09),steel)
    for off in (-.295,.295):
        xx=x+(0 if along_x else off); zz=z+(off if along_x else 0)
        t.cyl('Tray threaded suspension rod',(xx,(anchor_y+5.40)/2,zz),.009,anchor_y-5.40,steel,(0,1,0),8)
        t.box('Ceiling hanger anchor plate',(xx,anchor_y-.009,zz),(.11,.018,.11),steel)
        t.cyl('Lower hanger locknut',(xx,5.422,zz),.016,.015,edge,(0,1,0),6)
    network['support_checks'].append(dict(name='hanger_at_'+str((x,z)),gap=0,must='contact'))
for side in (-1,1):
    for z in (-8,-5,-2,1,3): tray_hanger(side*6.30,z)
for z in (-8.78,4.15):
    for x in (-4,0,4): tray_hanger(x,z,True)

# Wall electrical boxes feed actual tray terminal enclosures. Both ends of each
# conduit enter a gland/enclosure; no conduit is stopped arbitrarily in the air.
for side in (-1,1):
    wall_case=(side*7.665,2.70,-3.4); case_size=(.16,.52,.40)
    tray_case=(side*6.30,5.535,-3.4); tray_case_size=(.34,.17,.34)
    t.box('Wall junction case',wall_case,case_size,paint)
    t.box('Junction recessed cover',(side*7.575,2.70,-3.4),(.025,.45,.34),steel)
    t.box('Cable tray sealed terminal enclosure',tray_case,tray_case_size,paint)
    t.box('Tray terminal lid',(side*6.30,5.628,-3.4),(.35,.016,.35),steel)
    path=smooth_path([(side*7.65,2.945,-3.4),(side*7.65,4.14,-3.4),
                      (side*6.30,4.14,-3.4),(side*6.30,5.49,-3.4)],.18,10)
    terminal_tube('Terminated junction conduit '+str(side),path,.023,steel,
                  dict(kind='enclosure',bounds=bounds(wall_case,case_size)),
                  dict(kind='enclosure',bounds=bounds(tray_case,tray_case_size)))
    for x,y in ((side*7.65,2.988),(side*6.30,5.442)):
        t.cyl('Conduit gland locknut',(x,y,-3.4),.040,.076,edge,(0,1,0),12)
    for y in (3.26,3.78):
        t.box('Conduit wall standoff',(side*7.704,y,-3.4),(.084,.065,.085),steel)
        t.cyl('Conduit retaining clamp',(side*7.65,y,-3.4),.030,.04,steel,(0,1,0),12)
    for dx in (-.12,.12):
        for dz in (-.12,.12): t.bolt('Tray terminal lid screw',(side*6.30+dx,5.637,-3.4+dz),r=.005)

(OUT/'checks/service_network.json').write_text(json.dumps(network,indent=2),encoding='utf8')

objects=[p.finish() for p in parts]
manifest=dict(asset='RELAY Laboratory Envelope v02 - continuous services', scene_sha256=scene_hash,
              units='metres', source_dimension_axes='Unity X,Y,Z mapped to Blender X,Z,Y',
              unity_instance_transform=dict(parent='Environment',position=[0,0,0],rotation=[0,180,0],scale=[1,1,1]),
              clear_room=layout['room'],door_opening=layout['door_opening'],
              collision='Visual only: preserve original colliders; Generate Colliders OFF',
              materials=material_specs,parts=[])
export_objects=[]
depsgraph=bpy.context.evaluated_depsgraph_get()
for p,o in zip(parts,objects):
    evaluated=o.evaluated_get(depsgraph)
    me=bpy.data.meshes.new_from_object(evaluated,depsgraph=depsgraph)
    eo=bpy.data.objects.new(p.name+'_GAME',me); exports.objects.link(eo)
    # Reduce per-mesh material slots to only those used.
    used=sorted({f.material_index for f in me.polygons}); indices=[used.index(f.material_index) for f in me.polygons]
    mats=[me.materials[i] for i in used]; me.materials.clear()
    for m in mats: me.materials.append(m)
    for poly,mi in zip(me.polygons,indices): poly.material_index=mi
    me.calc_loop_triangles()
    export_objects.append(eo)
    coords=[P@vert.co for vert in me.vertices]
    manifest['parts'].append(dict(name=p.name,vertices=len(me.vertices),triangles=len(me.loop_triangles),
        min=[min(v[i] for v in coords) for i in range(3)],max=[max(v[i] for v in coords) for i in range(3)],
        materials=[m.name for m in mats],uv_layers=len(me.uv_layers),logical_pieces=len(p.elements)))
manifest['triangles_total']=sum(p['triangles'] for p in manifest['parts'])
manifest['source_element_count']=sum(len(p.elements) for p in parts)
manifest['fbx']='exports/LAB_Envelope.fbx'
bpy.ops.object.select_all(action='DESELECT')
for o in export_objects: o.select_set(True)
bpy.context.view_layer.objects.active=export_objects[0]
bpy.ops.export_scene.fbx(filepath=str(OUT/'exports/LAB_Envelope.fbx'),use_selection=True,object_types={'MESH'},
    axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
    add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
exports.hide_render=True; exports.hide_viewport=True
for o in export_objects: o.hide_set(True)
for im in bpy.data.images:
    if im.filepath:
        im.pack()
        im.filepath=bpy.path.relpath(im.filepath,start=str(OUT))
scene.cursor.location=(0,0,0)
bpy.ops.object.select_all(action='DESELECT')
objects[0].select_set(True); bpy.context.view_layer.objects.active=objects[0]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_end=150
            area.spaces.active.region_3d.view_location=P@Vector((0,2,-2))
            area.spaces.active.region_3d.view_distance=24
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_Laboratory.blend'),compress=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(OUT/'checks/source_elements.json').write_text(json.dumps({p.name:p.elements for p in parts},indent=2),encoding='utf8')
assert hashlib.sha256(scene_path.read_bytes()).hexdigest()==scene_hash
print('LAB_BUILD_OK',json.dumps(dict(parts=len(parts),triangles=manifest['triangles_total'],elements=manifest['source_element_count'])),flush=True)
