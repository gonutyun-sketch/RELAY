"""RELAY stationary mine shaft. Art output only; never writes to the Unity project."""
import bpy, bmesh, math, random, json, hashlib, bisect
from pathlib import Path
from mathutils import Vector, Matrix, noise

assert bpy.app.background
OUT = Path(__file__).resolve().parent
PROJECT = Path('C:/Users/gonut/School_p2').resolve()
assert not OUT.resolve().is_relative_to(PROJECT)
for name in ('exports', 'textures', 'previews', 'checks'):
    (OUT / name).mkdir(parents=True, exist_ok=True)
watched = [PROJECT / 'Assets/Scenes/Startup_Graybox.unity'] + list((PROJECT / 'Assets/RELAY/Scripts').glob('*.cs'))
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
P = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
def v(p): return P @ Vector(p)
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
rock_col = coll('01_ROCK_AND_EARTH')
steel_col = coll('02_FIXED_STEELWORK')
detail_col = coll('03_CABLES_ROOTS_RUBBLE')
export_col = coll('04_EXPORT_MESHES')
R = random.Random(94107)

def linear(h):
    vals = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in vals)
def material(name, color, metallic, roughness, texture=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.diffuse_color = (*linear(color), 1)
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = m.diffuse_color
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if texture:
        for suffix, colorspace in (('BaseColor', 'sRGB'), ('Normal', 'Non-Color')):
            path = OUT / 'textures' / (texture + '_' + suffix + '.png')
            if not path.exists(): raise RuntimeError('Missing texture: ' + str(path))
            im = bpy.data.images.load(str(path), check_existing=True)
            im.colorspace_settings.name = colorspace; im.pack()
            tex = m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = im
            tex.extension = 'REPEAT'; tex.label = suffix
            if suffix == 'BaseColor':
                m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
            else:
                normal = m.node_tree.nodes.new('ShaderNodeNormalMap')
                normal.inputs['Strength'].default_value = .65
                m.node_tree.links.new(tex.outputs['Color'], normal.inputs['Color'])
                m.node_tree.links.new(normal.outputs['Normal'], p.inputs['Normal'])
    return m
rock = material('RLYS_Rock', '66645D', 0, .86, 'RLYS_Rock')
earth = material('RLYS_Earth', '6C5741', 0, .95, 'RLYS_Earth')
iron = material('RLYS_Steel', '3E433D', .65, .72)
rust = material('RLYS_Oxide', '694E36', .12, .9)
cable = material('RLYS_Cable', '262923', 0, .84)

def mesh(name, points, faces, mats, collection, face_materials=None, bevel=0, closed=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([v(p) for p in points], [], faces); me.update()
    if closed:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    if face_materials:
        for p, index in zip(me.polygons, face_materials): p.material_index = index
    uv = me.uv_layers.new(name='UVMap')
    for face in me.polygons:
        normal = P @ face.normal
        ax = max(range(3), key=lambda j: abs(normal[j]))
        for li in face.loop_indices:
            q = P @ me.vertices[me.loops[li].vertex_index].co
            # Two metres per tile. Do not use giant stretched per-object UVs.
            u, w = ((q.z, q.y) if ax == 0 else (q.x, q.z) if ax == 1 else (q.x, q.y))
            uv.data[li].uv = (u / 2, w / 2)
    o = bpy.data.objects.new(name, me); collection.objects.link(o)
    if bevel:
        mod = o.modifiers.new('Worn edge radius', 'BEVEL'); mod.width = bevel; mod.segments = 2
        mod = o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL'); mod.keep_sharp = True
    return o

def box(name, pos, size, mat, collection=steel_col, bevel=.003):
    pos, size = Vector(pos), Vector(size) * .5
    pts = [tuple(pos + Vector((sx*size.x, sy*size.y, sz*size.z))) for sx,sy,sz in
           ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    return mesh(name, pts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)], [mat], collection, bevel=bevel)

def rod(name, a, b, radius, mat, collection=steel_col, sides=8):
    a,b = Vector(a),Vector(b); axis = (b-a).normalized()
    ref = Vector((0,1,0)) if abs(axis.y) < .9 else Vector((0,0,1))
    u = axis.cross(ref).normalized()*radius; w = axis.cross(u).normalized()*radius
    pts = [tuple(c + u*math.cos(j*math.tau/sides)+w*math.sin(j*math.tau/sides)) for c in (a,b) for j in range(sides)]
    faces = [(j,(j+1)%sides,(j+1)%sides+sides,j+sides) for j in range(sides)]
    faces += [tuple(range(sides-1,-1,-1)),tuple(range(sides,sides*2))]
    return mesh(name, pts, faces, [mat], collection)

def polyline(name, points, radius, mat, collection=detail_col):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions='3D'
    cu.resolution_u=1; cu.bevel_depth=radius; cu.bevel_resolution=0; cu.resolution_u=2
    sp=cu.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,q in zip(sp.points,points): p.co=(*v(q),1)
    cu.materials.append(mat); o=bpy.data.objects.new(name,cu); collection.objects.link(o); return o

levels=[-2.]
while levels[-1] < 37: levels.append(levels[-1]+R.uniform(.32,1.15))
def n(u,y,k): return noise.noise(Vector((u*.8,y*.8,k)), noise_basis='PERLIN_ORIGINAL')
def relief(u,y,k):
    tilted=y+.13*u+.18*n(u*.38,y*.34,k+3)
    i=max(0,min(len(levels)-2,bisect.bisect_right(levels,tilted)-1))
    t=(tilted-levels[i])/(levels[i+1]-levels[i])
    joint=.07*math.exp(-min(t,1-t)*32)
    return .10*n(u,y,k)+.065*n(u*2.8,y*2.1,k+7)+.024*n(u*8,y*5,k+19)+joint
def axis_values(lo,hi,step,extras=()):
    return sorted(set([lo,hi]+[round(i*step,6) for i in range(math.ceil(lo/step),math.floor(hi/step)+1)] + [a for a in extras if lo<a<hi]))

def rock_wall(name, direction, u0,u1,y0,y1,seed):
    us=axis_values(u0,u1,.32, (.1,)); ys=axis_values(y0,y1,.32,(6.3,))
    points=[]; nu=len(us); ny=len(ys)
    for iy,y in enumerate(ys):
        for iu,u in enumerate(us):
            uu=u if iu in (0,nu-1) or u==.1 else u+.085*n(u*2,y*2,seed+11)
            yy=y if iy in (0,ny-1) else y+.065*n(u*2,y*2,seed+31)
            depth=relief(uu,yy,seed)
            if direction=='L': q=(-max(2.66,2.88+depth),yy,uu)
            elif direction=='R': q=(max(2.66,2.88+depth),yy,uu)
            elif direction=='B': q=(uu,yy,-max(3.47,3.68+depth))
            else: q=(uu,yy,max(.70,.86+depth))
            points.append(q)
    count=len(points)
    for q in points[:count]:
        if direction=='L': p=(-3.45,q[1],q[2])
        elif direction=='R': p=(3.45,q[1],q[2])
        elif direction=='B': p=(q[0],q[1],-4.3)
        else:p=(q[0],q[1],1.30)
        points.append(p)
    faces=[]; mi=[]
    for iy in range(ny-1):
        for iu in range(nu-1):
            a=iy*nu+iu;b=a+1;c=a+nu+1;d=a+nu
            mid=(points[a][1]+points[c][1])/2
            organic=mid > 23.5+3.8*n(us[iu]*.6,mid*.35,seed+12)
            seams=abs(mid-(8.8+1.3*n(us[iu],0,20)))<.20
            mat=1 if organic or seams else 0
            tri=[(a,b,c),(a,c,d)] if (iy+iu)%2 else [(a,b,d),(b,c,d)]
            faces.extend(tri); mi.extend([mat,mat])
            faces.append((d+count,c+count,b+count,a+count));mi.append(0)
    edge=list(range(nu))+[j*nu+nu-1 for j in range(1,ny)]+list(range(ny*nu-2,(ny-1)*nu-1,-1))+[j*nu for j in range(ny-2,0,-1)]
    for a,b in zip(edge,edge[1:]+edge[:1]): faces.append((a,b,b+count,a+count));mi.append(0)
    o=mesh(name,points,faces,[rock,earth],rock_col,mi)
    # Angle weighted smoothing retains the large cut faces while the normal texture handles grain.
    for f in o.data.polygons: f.use_smooth=False
    return o

for direction in ('L','R'):
    seed=4 if direction=='L' else 21
    rock_wall('Rock_'+direction+'_Lower',direction,-4.2,.10,-1,6.3,seed)
    rock_wall('Rock_'+direction+'_Upper',direction,-4.2,1.30,6.3,34.05,seed)
rock_wall('Rock_Rear','B',-3.45,3.45,-1,34.05,45)
rock_wall('Rock_Front_Mid','F',-3.45,3.45,6.3,30,67)
# Closed pit and roof, clear of the cabin underside and lifting eyes.
box('Pit_rock_bed',(0,-1.23,-1.45),(6.9,.46,5.5),rock,rock_col,.02)
box('Roof_rock_cap',(0,34.25,-1.45),(6.9,.40,5.5),earth,rock_col,.04)

# Narrow steel perimeter sets. The door track is 5.06m wide: keep x >= 2.61m clear.
sets=[.85,4.05,7.7,11.1,14.6,18.0,21.7,25.3,28.7,33.35]
for idx,y in enumerate(sets):
    front=-.32 if y<6.3 else .69
    rear=-3.55; length=front-rear
    for sign in (-1,1):
        x=sign*2.69
        # Three strips form a believable channel, rather than a solid rectangular beam.
        box('Side_set_%02d_web'%idx,(x,y,(rear+front)/2),(.06,.20,length),iron)
        for dy in (-.105,.105): box('Side_set_flange',(x,y+dy,(rear+front)/2),(.16,.027,length),iron)
        for z in (rear+.10,front-.10):
            box('Set_splice_plate',(sign*2.595,y,z),(.025,.30,.36),rust,bevel=.003)
            for dy in (-.09,.09):
                for dz in (-.1,.1):rod('Set_hex_bolt',(sign*2.565,y+dy,z+dz),(sign*2.59,y+dy,z+dz),.014,iron,sides=6)
        # Short diagonal wall ties stay beyond the entire swept track width.
        a=(sign*2.72,y+.13,rear+.05);b=(sign*2.74,y+.66,rear+.53)
        rod('Rock_anchor_strut',a,b,.026,iron)
    box('Rear_set_web',(0,y,-3.47),(5.40,.20,.06),iron)
    for dy in (-.105,.105):box('Rear_set_flange',(0,y+dy,-3.47),(5.40,.027,.16),iron)
    if y>6.3 and y<30:
        box('Front_set_web',(0,y,.66),(5.40,.20,.05),iron)
        for dy in (-.105,.105):box('Front_set_flange',(0,y+dy,.66),(5.40,.027,.12),iron)

# Rear T guide rails: continuous vertical members and staggered bolted brackets.
for x in (-1.05,1.05):
    box('Guide_rail_flange',(x,16.48,-3.42),(.14,34.96,.045),iron,bevel=.002)
    box('Guide_rail_face',(x,16.48,-3.365),(.045,34.96,.07),iron,bevel=.001)
    for y in sets:
        box('Guide_bracket',(x,y,-3.51),(.38,.14,.12),rust,bevel=.002)
        for dx in (-.125,.125):rod('Guide_anchor',(x+dx,y,-3.415),(x+dx,y,-3.39),.013,iron,sides=6)

# Fixed cables against the left wall, with slightly unequal routes and small clamps.
for j,z in enumerate((-1.83,-1.95,-2.11)):
    pts=[]
    for i in range(71):
        y=-.9+i*.495
        pts.append((-2.655-.017*math.sin(y*.33+j),y,z+.025*math.sin(y*.20+j*.8)))
    polyline('Fixed_service_cable_%d'%j,pts,.018 if j<2 else .027,cable)
for y in (1.8,5.2,8.7,12.2,15.7,19.2,22.7,26.2,29.7,33):
    box('Cable_saddle',(-2.70,y,-1.97),(.10,.06,.47),iron,detail_col,.003)
    rod('Saddle_fastener',(-2.635,y,-1.77),(-2.665,y,-1.77),.012,rust,detail_col,6)

# Small angular rubble is restricted to the pit, never the cabin or door path.
for i in range(115):
    x=R.uniform(-2.58,2.58);z=R.uniform(-3.4,.5)
    rx=R.uniform(.04,.24);rz=R.uniform(.035,.20);h=R.uniform(.04,.25)
    y=-.97;points=[]
    for ring,yy in ((0,y),(1,y+h)):
        for j in range(6):
            a=math.tau*j/6+(.25 if ring else 0)
            f=R.uniform(.7,1.2)*(1 if ring==0 else .72)
            points.append((x+math.cos(a)*rx*f,yy+R.uniform(-.015,.015),z+math.sin(a)*rz*f))
    faces=[(j,(j+1)%6,(j+1)%6+6,j+6) for j in range(6)]+[tuple(range(5,-1,-1)),tuple(range(6,12))]
    mesh('Pit_fragment_%03d'%i,points,faces,[earth if i%4==0 else rock],detail_col)

# Sparse roots in the upper soil layer, not repeated vines all the way down.
for side in (-1,1):
    for i in range(14):
        y0=R.uniform(29.0,33.85);length=R.uniform(.6,3.1);z0=R.uniform(-3.3,-.4)
        pts=[]
        for j in range(13):
            t=j/12
            pts.append((side*(2.77+.08*math.sin(t*4+i)),y0-t*length,z0+.15*math.sin(t*5+i)))
        polyline('Upper_root',pts,R.uniform(.007,.017),earth)
        if i%2==0:
            a=Vector(pts[7]);ps=[tuple(a+Vector((side*.02,-t*.70,t*.30))) for t in (0,.25,.5,.75,1)]
            polyline('Root_branch',ps,.006,earth)

# Aggregate evaluated meshes with explicit material and UV remapping.
manifest={'package':'RELAY mine shaft v01','units':'metres','mount_parent':'Environment/EXIT_Module/ElevatorShaft',
          'mount_local_position':[0,0,0],'mount_local_rotation':[0,0,0],'mount_local_scale':[1,1,1],
          'source_coordinate_mapping':'Blender=(UnityX,UnityZ,UnityY)',
          'export_compensation':'Rotate export mesh 180deg around Blender Z; equivalent to prior Unity Y180 correction',
          'parts':[],'source_hashes_before':before}
def aggregate(collection,name):
    dg=bpy.context.evaluated_depsgraph_get();pts=[];faces=[];uvs=[];mis=[];mats=[];smooth=[]
    for o in sorted(collection.objects,key=lambda q:q.name):
        if o.type not in {'MESH','CURVE'}:continue
        ev=o.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
        base=len(pts);pts.extend([ev.matrix_world@q.co for q in me.vertices])
        uv=me.uv_layers.active
        for f in me.polygons:
            faces.append(tuple(base+i for i in f.vertices));smooth.append(f.use_smooth)
            mat=me.materials[f.material_index] if len(me.materials) else iron
            if mat not in mats:mats.append(mat)
            mis.append(mats.index(mat))
            for li in f.loop_indices:
                if uv:uvs.append(tuple(uv.data[li].uv))
                else:
                    q=P@(ev.matrix_world@me.vertices[me.loops[li].vertex_index].co);uvs.append((q.z/2,q.y/2))
        ev.to_mesh_clear()
    me=bpy.data.meshes.new(name);me.from_pydata(pts,[],faces);me.update()
    for m in mats:me.materials.append(m)
    for f,mi,sm in zip(me.polygons,mis,smooth):f.material_index=mi;f.use_smooth=sm
    uv=me.uv_layers.new(name='UVMap')
    for data,xy in zip(uv.data,uvs):data.uv=xy
    o=bpy.data.objects.new(name,me);export_col.objects.link(o)
    source_points=[P@q.co for q in me.vertices]
    me.calc_loop_triangles()
    # Check complete triangle AABBs against a conservative swept elevator box.
    safe_lo=Vector((-2.55,-.55,-3.27));safe_hi=Vector((2.55,33.55,.55))
    bad=[]
    for tri in me.loop_triangles:
        vv=[source_points[i] for i in tri.vertices]
        if all(max(p[k] for p in vv)>safe_lo[k] and min(p[k] for p in vv)<safe_hi[k] for k in range(3)):
            bad.append(tri.index)
    if bad:raise RuntimeError(name+' intrudes swept cabin/track clearance: '+str(bad[:10]))
    intrusions=[q for q in source_points if 0<q.y<6 and q.z>.25]
    # Bottom/root/roof nodes do not enter the room. Shaft itself must stay behind wall.
    if intrusions:raise RuntimeError(name+' enters laboratory: '+str(intrusions[:2]))
    entry=[q for q in source_points if abs(q.x)<1.2 and -.2<q.z<1.4 and (0<q.y<3 or 30<q.y<33)]
    if entry:raise RuntimeError(name+' obstructs an exit opening')
    rec={'name':name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),
         'design_min':[min(q[k] for q in source_points) for k in range(3)],
         'design_max':[max(q[k] for q in source_points) for k in range(3)],
         'materials':[m.name for m in mats],'material_face_counts':{m.name:mis.count(i) for i,m in enumerate(mats)},
         'checks':{'swept_box_clear':True,'laboratory_interior_clear':True,'entry_exit_clear':True,'uv_loops_complete':len(uvs)==len(me.loops)}}
    # Bake correction into exported geometry; source art stays in the familiar review coordinates.
    turn=Matrix.Rotation(math.pi,4,'Z');me.transform(turn);me.update()
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/(name+'.fbx')),use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,
        bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    me.transform(turn.inverted());me.update();o.hide_render=True;o.hide_set(True)
    return rec
for c,name in ((rock_col,'SHAFT_RockShell'),(steel_col,'SHAFT_Steelwork'),(detail_col,'SHAFT_Details')):
    manifest['parts'].append(aggregate(c,name))
export_col.hide_render=True;export_col.hide_viewport=True
manifest['total_triangles']=sum(p['triangles'] for p in manifest['parts'])
manifest['source_hashes_after']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
assert before==manifest['source_hashes_after'],'Source files changed during art generation.'
manifest['unity_project_unchanged']=True
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
scene.cursor.location=(0,0,0)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_distance=13
            a.spaces.active.region_3d.view_location=v((0,16,-1.5))
            a.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MineShaft.blend'))
print('SHAFT_BUILD_OK',manifest['total_triangles'])
