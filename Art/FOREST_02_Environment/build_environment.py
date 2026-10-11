"""RELAY: complete mountain forest art. Never writes to the Unity project."""
import bpy, bmesh, math, random, json, hashlib, shutil, time
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.noise import noise_vector

OUT=Path(__file__).resolve().parent
TREE=OUT.parent/'FOREST_01_HeroTree'
PROJECT=Path('C:/Users/gonut/School_p2').resolve()
assert not OUT.is_relative_to(PROJECT)
assert bpy.app.background
for d in ('exports','previews','checks','textures'): (OUT/d).mkdir(exist_ok=True,parents=True)
watched=[PROJECT/'Assets/Scenes/Startup_Graybox.unity',*sorted((PROJECT/'Assets/RELAY/Scripts').glob('*.cs'))]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
R=random.Random(20261010)
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(p):return P@Vector(p)
def design(p):return P@Vector(p)
def linear(h):
    return tuple(q/12.92 if q<=.04045 else ((q+.055)/1.055)**2.4 for q in (int(h[i:i+2],16)/255 for i in (0,2,4)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
def col(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
terrain=col('01_Terrain_and_Path');rocks=col('02_Rockwork');undergrowth=col('03_Ferns_and_Forest_Litter')
near=col('04_Trees_Near');mid=col('05_Trees_Mid');far=col('06_Trees_Far');ridges=col('07_Distant_Ridges')
preview=col('90_Preview_Lighting_Fog_Cameras');library=col('98_Tree_Library');exports=col('99_Unity_Exports')
library.hide_render=True;library.hide_viewport=True
exports.hide_render=True

def mat(name,h,rough=.85):
    m=bpy.data.materials.new(name);m.diffuse_color=(*linear(h),1);m.use_nodes=True
    ns=m.node_tree.nodes;ns.clear();b=ns.new('ShaderNodeBsdfPrincipled');o=ns.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(b.outputs['BSDF'],o.inputs['Surface']);b.inputs['Base Color'].default_value=m.diffuse_color
    b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=.26
    return m,b
def image_material(name,base,normal,rough=.85):
    m,b=mat(name,'777777',rough)
    for fn,space,out in ((base,'sRGB','Color'),(normal,'Non-Color','Normal')):
        if not fn:continue
        im=bpy.data.images.load(str(OUT/'textures'/fn),check_existing=True);im.colorspace_settings.name=space;im.pack()
        tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
        if out=='Color':m.node_tree.links.new(tx.outputs['Color'],b.inputs['Base Color'])
        else:
            nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65
            m.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    return m
floor=image_material('RLYF_ForestFloor','RLYF_MossFloor_BaseColor.png','RLYF_Floor_Normal.png',.84)
rock=image_material('RLYF_DampGranite','RLYF_Rock_BaseColor.png','RLYF_Rock_Normal.png',.86)
pathmat=image_material('RLYF_TroddenPath','RLYF_Path_Cutout.png',None,.85)
pbs=next(n for n in pathmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
ptx=next(n for n in pathmat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.colorspace_settings.name=='sRGB')
ptx.extension='EXTEND'
threshold=pathmat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.45
pathmat.node_tree.links.new(ptx.outputs['Alpha'],threshold.inputs[0]);pathmat.node_tree.links.new(threshold.outputs[0],pbs.inputs['Alpha'])
# A slightly lighter, warmer path remains the same earthy material in exported FBX.
moss,_=mat('RLYF_OldMoss','48533C',.96)
fern_mats=[mat('RLYF_Fern_'+str(i),h,.84)[0] for i,h in enumerate(('42503B','536344','626D43','343F31'))]
grass_mats=[mat('RLYF_Sedge_'+str(i),h,.92)[0] for i,h in enumerate(('5C6046','666651','444A37'))]
ridge_mat,_=mat('RLYF_DistantStone','646E70',.96)
stem_mat,_=mat('RLYF_DryTwigs','514738',.96)
cutwood=image_material('RLYF_CutWood','RLYF_LogEnd_BaseColor.png','RLYF_LogEnd_Normal.png',.89)
for n in cutwood.node_tree.nodes:
    if n.type=='TEX_IMAGE':n.extension='EXTEND'
shrub_mats=[mat('RLYF_Bilberry_'+str(i),h,.72)[0] for i,h in enumerate(('34482F','455739','5B6240'))]
litter_mats=[mat('RLYF_LeafLitter_'+str(i),h,.94)[0] for i,h in enumerate(('584E36','66573D','403D2C'))]
moss_detail_mats=[mat('RLYF_RockMoss_'+str(i),h,.98)[0] for i,h in enumerate(('455033','59613E','37452E'))]

with bpy.data.libraries.load(str(TREE/'RELAY_FOREST_Spruce_A.blend'),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('SPRUCE_A_')]
templates={}
for o in dst.objects:
    library.objects.link(o);templates[o.name]=o
for fn in ('RLYF_Bark_BaseColor.png','RLYF_Bark_Normal.png','RLYF_Bark_Roughness.png','RLYF_Needles_Atlas.png'):
    shutil.copy2(TREE/'textures'/fn,OUT/'textures'/fn)
for im in bpy.data.images:
    if im.source=='FILE' and Path(im.filepath).name in {p.name for p in (OUT/'textures').glob('*.png')}:
        im.filepath=str(OUT/'textures'/Path(im.filepath).name)
bark=bpy.data.materials['RLYF_SpruceBark'];wood=bpy.data.materials['RLYF_ExposedWood']

def mesh(name,pts,faces,materials,collection,uvs=None,indices=None,smooth=True,recalc=True):
    me=bpy.data.meshes.new(name);me.from_pydata([v(p) for p in pts],[],faces);me.update()
    for m in materials:me.materials.append(m)
    if recalc:
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    for f in me.polygons:
        f.use_smooth=smooth
        if indices:f.material_index=indices[f.index]
    uv=me.uv_layers.new(name='UVMap')
    for f in me.polygons:
        for li in f.loop_indices:
            q=design(me.vertices[me.loops[li].vertex_index].co)
            # Axis projection selected per face keeps cliff textures undistorted.
            n=design(f.normal);axis=max(range(3),key=lambda k:abs(n[k]))
            xy=(q.x/2,q.z/2) if axis==1 else (q.z/2,q.y/2) if axis==0 else (q.x/2,q.y/2)
            uv.data[li].uv=xy
    obj=bpy.data.objects.new(name,me);collection.objects.link(obj);return obj

def path_x(z):return (1.5*math.sin(z*.16)+.55*math.sin(z*.39))*min(1,max(0,z/4))
def ground_y(x,z):
    px=path_x(min(19,max(0,z)));d=abs(x-px)
    micro=.035*math.sin(x*1.2+z*.41)*math.sin(z*.8-x*.6)
    walk=.015*math.sin(z*.38)+micro*min(1,d/2)
    side=max(0,d-2.0)
    banks=.08*side+.24*math.sin(x*.33+z*.15)*min(1,side/3)
    if z>20:
        walk-=min(3.4,(z-20)*.19)
        banks+=.45*math.sin(x*.12+z*.18)
    if z>48:
        walk+=min(1,(z-48)/20)*(1.4*math.sin(z*.065+x*.03)+1.3*math.sin(x*.11+z*.039)+(z-48)*.013)
    if z<.7 and abs(x)<1.4:return 0.0
    return walk+banks

# Continuous terrain: the original 20 m walk area fits inside this wider scene.
nx=132;xs=[-42+i*84/nx for i in range(nx+1)];zs=[-7+i*.6 for i in range(93)]+[50+i*2 for i in range(80)];nz=len(zs)-1
pts=[(x,ground_y(x,z),z) for z in zs for x in xs];faces=[]
for j in range(nz):
    for i in range(nx):
        a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
terrainobj=mesh('Forest_Ground',pts,faces,[floor],terrain)
# An open height field has no enclosed volume: generic normal recalculation
# can choose the underside. Explicitly orient every ground face toward +Z.
bm=bmesh.new();bm.from_mesh(terrainobj.data);bm.normal_update()
bmesh.ops.reverse_faces(bm,faces=[f for f in bm.faces if f.normal.z < 0])
bm.to_mesh(terrainobj.data);bm.free();terrainobj.data.update()
assert all(f.normal.z > 0 for f in terrainobj.data.polygons)

# Irregular path with a feathered geometric edge, never a ruler-straight strip.
pv=[];pf=[]
for j in range(91):
    z=j*.21;w=1.13+.10*math.sin(z*1.7)+.10*math.sin(z*.42)
    for t in (-1,-.65,0,.65,1):
        x=path_x(z)+w*t;pv.append((x,ground_y(x,z)+.006,z))
for j in range(90):
    for k in range(4):a=j*5+k;pf.append((a,a+1,a+6,a+5))
pathobj=mesh('Worn_Forest_Path',pv,pf,[pathmat],terrain)
for poly in pathobj.data.polygons:
    for li in poly.loop_indices:
        p=design(pathobj.data.vertices[pathobj.data.loops[li].vertex_index].co)
        w=1.13+.10*math.sin(p.z*1.7)+.10*math.sin(p.z*.42)
        pathobj.data.uv_layers.active.data[li].uv=((p.x-path_x(p.z))/(2*w)+.5,p.z/18.9)

# Granite prototypes are linked, varied in shape, embedded into soil.
rockprotos=[]
for i in range(7):
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
    for vert in bm.verts:
        p=vert.co;nv=noise_vector(p*2.2+Vector((i*4.2,3,5)))
        p*=1+.16*nv.x;p.x+=.12*nv.y;p.z+=.1*nv.z
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    q=[tuple(design(p.co)) for p in bm.verts];f=[tuple(a.index for a in face.verts) for face in bm.faces];bm.free()
    proto=mesh('Granite_Form_%02d'%i,q,f,[rock],library)
    rockprotos.append(proto)

rock_placements=[]
def place_rock(x,z,scale,angle=None,name='Granite'):
    proto=rockprotos[len(rock_placements)%len(rockprotos)]
    o=bpy.data.objects.new(name+'_%03d'%len(rock_placements),proto.data);rocks.objects.link(o)
    y=ground_y(x,z)-scale[1]*.35
    o.location=v((x,y,z));o.scale=(scale[0],scale[2],scale[1]);o.rotation_euler[2]=R.uniform(-math.pi,math.pi) if angle is None else angle
    rock_placements.append({'x':x,'z':z,'radius':max(scale[0],scale[2]),'height':scale[1]})
    return o
# Strong asymmetrical foreground anchors, no obstacle in the entrance.
for x,z,s in [(-3.0,2.8,(1.4,.9,1.0)),(4.3,4.8,(1.6,1.1,1.25)),(-3.8,7.8,(1.8,1.15,1.25)),
              (5.2,12.3,(1.5,.9,1.2)),(-4.5,16,(2.4,1.6,1.5)),(5.6,18.8,(2.1,1.3,1.7)),
              (-8.1,11,(2.3,1.8,2.0)),(8.7,7,(2.4,1.7,1.6)),(-8,23,(3.6,2.7,3.1)),(12,25,(3,2.3,2.5))]:place_rock(x,z,s)
for i in range(115):
    x=R.uniform(-25,25);z=R.uniform(-3,47);d=abs(x-path_x(min(z,19)))
    if z<20 and d<2.0:continue
    size=R.uniform(.12,.65) if i<75 else R.uniform(.8,2.6)
    if z<20 and d<2.4+size:continue
    place_rock(x,z,(size*R.uniform(.8,1.4),size*R.uniform(.4,.85),size*R.uniform(.7,1.2)))

# The grove is placed in irregular groups, with a gap facing the final ridge.
tree_placements=[]
def place_tree(x,z,scale,lod,collection):
    rot=R.uniform(-math.pi,math.pi);wide=R.uniform(.82,1.10);sy=scale*R.uniform(.94,1.04)
    for part in ('Wood','Needles'):
        src=templates['SPRUCE_A_%s_LOD%d'%(part,lod)]
        o=bpy.data.objects.new('Spruce_%03d_%s'%(len(tree_placements),part),src.data);collection.objects.link(o)
        o.location=v((x,ground_y(x,z),z));o.scale=(scale*wide,scale*R.uniform(.94,1.04),sy)
        # Identical transform for wood and needles preserves every branch attachment.
        if part=='Wood':shared_scale=o.scale.copy()
        else:o.scale=shared_scale
        o.rotation_euler=(R.uniform(-.02,.02),R.uniform(-.02,.02),rot) if part=='Wood' else rotation
        if part=='Wood':rotation=o.rotation_euler.copy()
    tree_placements.append({'x':x,'z':z,'scale':scale,'lod':lod,'trunk_radius':.42*scale})
for x,z,s in [(-3.7,4.1,1.09),(4.5,7.8,1.0)]:place_tree(x,z,s,0,near)
for x,z,s in [(-5.8,1.2,.95),(6.7,1.8,1.05),(-5.2,10.2,.91),(6.8,14.0,1.06),
              (-6.9,17.8,1.11),(4.4,18.2,.91),(-10.3,6.8,1.12),(10.2,6.7,1.05),
              (-10.2,13.5,.97),(9.8,19.2,.91),(-11.7,22.3,1.04),(13.0,23.0,.9)]:place_tree(x,z,s,1,mid)
trials=0
while len(tree_placements)<116 and trials<15000:
    trials+=1;x=R.uniform(-35,35);z=R.uniform(-4,64)
    if z<21 and abs(x-path_x(max(0,z)))<4.0:continue
    if z>20 and abs(x)<3.5+(z-20)*.10:continue # layered valley vista
    if any((x-t['x'])**2+(z-t['z'])**2<2.7**2 for t in tree_placements):continue
    if z<20 and abs(x)<11:continue # hero placements already cover the playable strip
    # Extra spacing in the clearing, denser in distance.
    if z<24 and abs(x)<16 and R.random()<.60:continue
    s=R.uniform(.62,1.15);place_tree(x,z,s,2,far)
# Smaller valley groups break up the far ground silhouette while keeping the vista open.
for group,cx in enumerate((-7.0,8.0,-15.5,15.0)):
    for j in range(6):
        x=cx+R.uniform(-2,2);z=32+j*7+R.uniform(0,7)+group*3
        place_tree(x,z,R.uniform(.38,.65),2,far)

def tube(name,points,radii,collection,materials=(None,),sides=8):
    materials=list(materials) if materials[0] else [bark,cutwood]
    vv=[];ff=[];mi=[];pts=[Vector(p) for p in points];previous_axis=None
    for j,(p,rad) in enumerate(zip(pts,radii)):
        t=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
        # Parallel-transport the ring frame. Switching world-up references at a
        # nearly vertical segment twists a stump and can fold the side faces.
        a=previous_axis-t*previous_axis.dot(t) if previous_axis is not None else Vector()
        if a.length<1e-5:
            ref=min((Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))),key=lambda q:abs(t.dot(q)))
            a=t.cross(ref)
        a.normalize();previous_axis=a.copy();b=t.cross(a).normalized()
        for k in range(sides):vv.append(tuple(p+rad*(math.cos(k*math.tau/sides)*a+math.sin(k*math.tau/sides)*b)))
    for j in range(len(pts)-1):
        for k in range(sides):ff.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k));mi.append(0)
    ff.extend([tuple(range(sides-1,-1,-1)),tuple((len(pts)-1)*sides+k for k in range(sides))]);mi.extend([min(1,len(materials)-1)]*2)
    obj=mesh(name,vv,ff,materials,collection,indices=mi)
    # Cylindrical bark UVs follow the grain along a fallen log or exposed root.
    dist=[0.0]
    for j in range(1,len(pts)):dist.append(dist[-1]+(pts[j]-pts[j-1]).length)
    circum=math.tau*sum(radii)/len(radii)
    for poly in obj.data.polygons:
        if poly.index<(len(pts)-1)*sides:
            k=poly.index%sides
            for li in poly.loop_indices:
                vi=obj.data.loops[li].vertex_index;ring=vi//sides;edge=vi%sides
                if k==sides-1 and edge==0:edge=sides
                obj.data.uv_layers.active.data[li].uv=(edge/sides*circum,dist[ring]/2)
        else:
            cc=sum((design(obj.data.vertices[i].co) for i in poly.vertices),Vector())/len(poly.vertices)
            norm=design(poly.normal);aa=norm.cross(Vector((0,1,0)))
            if aa.length<.1:aa=norm.cross(Vector((1,0,0)))
            aa.normalize();bb=norm.cross(aa).normalized();rad=max((design(obj.data.vertices[i].co)-cc).length for i in poly.vertices)
            for li in poly.loop_indices:
                q=design(obj.data.vertices[obj.data.loops[li].vertex_index].co)-cc
                obj.data.uv_layers.active.data[li].uv=(.5+.48*q.dot(aa)/rad,.5+.48*q.dot(bb)/rad)
    return obj
for i,(x,z,dx,dz,length) in enumerate([(-3.5,12.7,-.6,1,3.7),(5.3,3.0,.8,.4,2.5),(-6.4,20.4,.8,.3,3.2)]):
    h=ground_y(x,z)+.20;pts=[(x+dx*t*length,h+.05*math.sin(t*4),z+dz*t*length) for t in (0,.25,.5,.75,1)]
    tube('Fallen_Trunk_%d'%i,pts,[.25,.24,.22,.20,.18],undergrowth)
    for j,t in enumerate((.25,.5,.72)):
        a=Vector((x+dx*t*length,h,z+dz*t*length));b=a+Vector((-.36,.37,.28))
        tube('Broken_Branch', [a,b], [.055,.018],undergrowth,sides=7)

# Low, uneven exposed roots tie the hero trunks into the ground.
for ti,t in enumerate(tree_placements[:6]):
    x,z=t['x'],t['z']
    for k in range(5):
        ang=math.tau*k/5+ti*.71;length=R.uniform(1.2,2.5);points=[]
        for j in range(9):
            f=j/8;xx=x+math.cos(ang)*length*f+.13*math.sin(f*5+ti)*f;zz=z+math.sin(ang)*length*f+.12*math.sin(f*6+k)*f
            points.append((xx,ground_y(xx,zz)+.07*(1-f)+.025*math.sin(f*5)**2,zz))
        if any(abs(p[0]-path_x(p[2]))<1.2 and 0<p[2]<19 for p in points):continue
        tube('Exposed_Spruce_Root',points,[.13*(1-j/9)**1.5+.008 for j in range(9)],undergrowth,sides=9)

# A broken, weathered deadfall near the walking route rewards a close look.
x,z=-2.65,6.25;y=ground_y(x,z)
tube('Weathered_Stump',[(x,y,z),(x+.03,y+.20,z-.02),(x-.03,y+.43,z+.03)],[.29,.25,.235],undergrowth,sides=15)
tube('Close_Deadfall',[(x-.15,y+.21,z+.55),(x-.52,y+.24,z+1.25),(x-.85,y+.16,z+1.90)],[.19,.17,.15],undergrowth,sides=15)
for k in range(6):
    a=k*math.tau/6;xx=x+math.cos(a)*.19;zz=z+math.sin(a)*.19
    tube('Stump_Splinter',[(xx,y+.33,zz),(xx+.014,y+R.uniform(.44,.53),zz+.01)],[.02,.004],undergrowth,[cutwood],sides=5)

# Physical moss islands conform to upward rock faces, with rough broken borders.
bpy.context.view_layer.update();mv=[];mf=[];mfi=[]
for ro in [o for o in rocks.objects if o.name.startswith('Granite')][:6]:
    ro.data.calc_loop_triangles()
    for tri in ro.data.loop_triangles:
        p=[design(ro.matrix_world@ro.data.vertices[i].co) for i in tri.vertices]
        n=design(ro.matrix_world.to_3x3().inverted().transposed()@tri.normal).normalized()
        if n.y<.36:continue
        area=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
        for j in range(min(240,int(area*500))):
            a=R.random();b=R.random()
            if a+b>1:a=1-a;b=1-b
            center=p[0]+a*(p[1]-p[0])+b*(p[2]-p[0]);nv=noise_vector(center*3.7)
            if nv.x<-.08:continue
            side=n.cross(Vector((0,0,1))).normalized();forward=n.cross(side).normalized();rad=R.uniform(.004,.012)
            base=len(mv);mv.append(tuple(center+n*R.uniform(.003,.006)))
            for k in range(7):
                ang=k*math.tau/7;size=rad*R.uniform(.75,1.22)
                mv.append(tuple(center+n*.0015+side*math.cos(ang)*size+forward*math.sin(ang)*size))
            for k in range(7):mf.append((base,base+1+k,base+1+(k+1)%7));mfi.append(j%3)
mesh('Rock_Surface_Moss',mv,mf,moss_detail_mats,undergrowth,indices=mfi,recalc=False)

# Small bilberry shrubs: woody stems and modeled folded oval leaves.
sv=[];sf=[];sfi=[]
def oval_leaf(center,axis,side,length,width,target_v,target_f,target_m,mi):
    center=Vector(center);axis=Vector(axis).normalized();side=Vector(side).normalized();normal=axis.cross(side).normalized();base=len(target_v)
    points=[center,center+axis*length*.30-side*width*.7,center+axis*length*.68-side*width,
            center+axis*length,center+axis*length*.68+side*width,center+axis*length*.30+side*width*.7,
            center+axis*length*.52+normal*width*.22]
    target_v.extend(map(tuple,points))
    for k in range(6):target_f.append((base+k,base+(k+1)%6,base+6));target_m.append(mi)
for si,(x,z) in enumerate([(-2.6,2.0),(3.7,3.8),(-2.8,5.3),(4.0,7.0),(-3.8,10.1),(3.8,13.6),(-4.0,15.2),(5.0,18.5),(-6,8.0),(7.3,9.8),(-5.5,3.1)]):
    y=ground_y(x,z)
    for branch in range(9):
        angle=R.uniform(0,math.tau);h=R.uniform(.24,.52);dx=math.cos(angle);dz=math.sin(angle)
        p=[Vector((x,y,z)),Vector((x+dx*.14,y+h*.58,z+dz*.14)),Vector((x+dx*.28,y+h,z+dz*.28))]
        tube('Bilberry_Stem',p,[.006,.004,.0018],undergrowth,[stem_mat],sides=5)
        for j in range(7):
            t=.25+j*.10;c=p[0].lerp(p[2],t);a=angle+R.choice((-1,1))*1.15
            axis=Vector((math.cos(a),R.uniform(.10,.4),math.sin(a)));side=Vector((-math.sin(a),0,math.cos(a)))
            oval_leaf(c,axis,side,R.uniform(.055,.095),R.uniform(.019,.034),sv,sf,sfi,(si+j)%3)
mesh('Bilberry_Leaves',sv,sf,shrub_mats,undergrowth,indices=sfi,recalc=False)

# Individual curled leaf fragments complement the small needles in the floor maps.
lv=[];lf=[];lfi=[]
for i in range(330):
    z=R.uniform(.7,20);x=path_x(z)+R.choice((-1,1))*R.uniform(.85,4.3);y=ground_y(x,z)+.012;a=R.uniform(0,math.tau)
    oval_leaf((x,y,z),(math.cos(a),R.uniform(-.03,.10),math.sin(a)),(-math.sin(a),0,math.cos(a)),R.uniform(.04,.095),R.uniform(.012,.026),lv,lf,lfi,i%3)
mesh('Scattered_Leaf_Litter',lv,lf,litter_mats,undergrowth,indices=lfi,recalc=False)

# Ferns have modeled pinnae; no large transparent square cards close to camera.
fv=[];ff=[];fi=[]
def fern(x,z,size,seed):
    rr=random.Random(seed);y=ground_y(x,z)+.01
    for fr in range(rr.randint(6,9)):
        ang=math.tau*fr/8+rr.uniform(-.2,.2);d=Vector((math.cos(ang),0,math.sin(ang)));side=Vector((-d.z,0,d.x))
        length=size*rr.uniform(.75,1.15)
        def center(t):return Vector((x,y,z))+d*(length*t*.86)+Vector((0,length*(.17*t+.57*math.sin(t*math.pi*.72)),0))
        # Thin rachis plus tapered paired leaflets with a folded center ridge.
        for j in range(1,10):
            t=.12+j*.078;c=center(t);leaflen=length*.22*math.sin(t*math.pi)**.65*(1-.45*t)
            for sign in (-1,1):
                tip=c+side*leaflen*sign+d*(leaflen*.35)+Vector((0,.01,0));w=length*.030*(1-t*.7)
                base=len(fv);fv.extend([tuple(c-d*w*.30),tuple((c+tip)*.5-d*w),tuple((c+tip)*.5+Vector((0,w*.42,0))),tuple(tip),tuple((c+tip)*.5+d*w)])
                ff.extend([(base,base+1,base+2),(base+1,base+3,base+2),(base+2,base+3,base+4),(base,base+2,base+4)]);fi.extend([seed%4]*4)
        for j in range(7):
            a=center(j/7);b=center((j+1)/7);w=.004*size;base=len(fv)
            fv.extend([tuple(a-side*w),tuple(a+side*w),tuple(b+side*w*.3),tuple(b-side*w*.3)]);ff.append((base,base+1,base+2,base+3));fi.append(seed%4)

# Clumps flank the path; controlled gaps expose the dirt and small stones.
for i in range(330):
    z=R.uniform(.8,26);side=R.choice((-1,1));x=path_x(min(z,19))+side*R.uniform(1.55,8.0)
    if any((x-p['x'])**2+(z-p['z'])**2<(p['radius']*.75)**2 for p in rock_placements):continue
    fern(x,z,R.uniform(.30,.78),i+60)
for i,(x,z,s) in enumerate([(-1.7,1.5,.72),(2.4,2.8,.75),(-2.5,3.1,.6),(-1.6,5.2,.6),(3.4,6.2,.7),(-2.7,8,.8),(3.3,10,.72),(3.1,11,.58)]):fern(x,z,s,500+i)
mesh('Fern_Beds',fv,ff,fern_mats,undergrowth,indices=fi,recalc=False)
gv=[];gf=[];gi=[]
for i in range(2200):
    z=R.uniform(-1,28);x=R.uniform(-11,11)
    if abs(x-path_x(min(19,max(0,z))))<1.30 and 0<z<19:continue
    y=ground_y(x,z)
    for j in range(R.randint(4,8)):
        ang=R.uniform(0,math.tau);h=R.uniform(.10,.30);dx=math.cos(ang);dz=math.sin(ang);w=R.uniform(.009,.018)
        base=len(gv);a=Vector((x,y,z));s=Vector((-dz*w,0,dx*w));m=a+Vector((dx*h*.22,h*.64,dz*h*.22));t=a+Vector((dx*h*.64,h*.86,dz*h*.64))
        gv.extend(map(tuple,(a-s,a+s,m+s*.6,m-s*.6,t)));gf.extend([(base,base+1,base+2,base+3),(base+3,base+2,base+4)]);gi.extend([i%3]*2)
mesh('Sedge_and_Dry_Grass',gv,gf,grass_mats,undergrowth,indices=gi,recalc=False)
for i in range(60):
    x=R.uniform(-8,8);z=R.uniform(0,20);y=ground_y(x,z)+.015
    if abs(x)<1.2 and z<1:continue
    ln=R.uniform(.14,.6);a=R.uniform(0,math.tau)
    tube('Forest_Twig',[(x,y,z),(x+math.sin(a)*ln,y+.02,z+math.cos(a)*ln)],[.008,.003],undergrowth,[stem_mat],sides=5)
# A scattering of tiny stones near the path provides a readable scale reference.
for i in range(55):
    z=R.uniform(1,20);x=path_x(min(z,19))+R.choice((-1,1))*R.uniform(.8,2.6);s=R.uniform(.025,.10)
    place_rock(x,z,(s,s*.6,s*.8),name='Path_Pebble')

# Separate distant mountain silhouettes: the valley opens between asymmetrical peaks.
for ri,(cx,cz,width,height,depth) in enumerate([(-35,102,44,26,23),(34,119,47,35,25),(1,142,48,32,20),(-60,146,44,35,28),(63,169,54,45,32)]):
    vv=[];ff=[];nx=48;nz=20
    for j in range(nz+1):
        tz=-1+2*j/nz
        for i in range(nx+1):
            tx=-1+2*i/nx;x=cx+tx*width;z=cz+tz*depth
            crest=(max(0,1-abs(tx)**1.3)**.8)*(height+2.5*math.sin(tx*13+ri)+1.3*math.sin(tx*29+ri))
            y=-5+crest*max(0,1-tz*tz)**.75+1.1*math.sin(tx*19+tz*11)*max(0,1-abs(tx))*max(0,1-abs(tz))
            vv.append((x,y,z))
    for j in range(nz):
        for i in range(nx):a=j*(nx+1)+i;ff.append((a,a+1,a+nx+2,a+nx+1))
    mesh('Mountain_Ridge_%02d'%ri,vv,ff,[ridge_mat],ridges)

marker=bpy.data.objects.new('ELEVATOR_EXIT__Place_This_Origin_At_MountainEnding',None);preview.objects.link(marker);marker.empty_display_type='ARROWS';marker.empty_display_size=1
marker['forward']='Unity +Z, Blender +Y';marker['placement']='MountainEnding child, local position/rotation 0, scale 1'

# Lighting and volumetric atmosphere are review-only; the FBXs contain geometry.
world=bpy.data.worlds.new('Cold_Overcast_Mountain');world.use_nodes=True
ns=world.node_tree.nodes;ns.clear();bg=ns.new('ShaderNodeBackground');wo=ns.new('ShaderNodeOutputWorld')
bg.inputs['Color'].default_value=(.49,.61,.73,1);bg.inputs['Strength'].default_value=.48;world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);scene.world=world
ld=bpy.data.lights.new('Moon_through_cloud','SUN');ld.energy=1.05;ld.angle=.22;ld.color=(.70,.82,1.0)
o=bpy.data.objects.new(ld.name,ld);preview.objects.link(o);o.rotation_euler=(math.radians(27),math.radians(-24),math.radians(-34))
for name,pos,power,color,size,target in [('Soft_sky',(-6,18,10),4300,(.62,.76,1),22,(0,0,10)),('Path_bounce',(0,5,1),140,(.80,.83,.74),8,(0,0,12)),('Diffuse_near_sky',(1,7,-2),420,(.78,.82,.75),10,(-2,0,7))]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
    o=bpy.data.objects.new(name,ld);preview.objects.link(o);o.location=v(pos);o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler()

# Low-density blue-grey mist provides depth without hiding the foreground work.
bpy.ops.mesh.primitive_cube_add(size=2,location=v((0,24,85)));fog=bpy.context.object;fog.name='PREVIEW_ONLY_Valley_Mist'
for c in list(fog.users_collection):c.objects.unlink(fog)
preview.objects.link(fog);fog.scale=(130,120,39)
fm=bpy.data.materials.new('PREVIEW_ONLY_Mist');fm.use_nodes=True;ns=fm.node_tree.nodes;ns.clear()
vo=ns.new('ShaderNodeVolumePrincipled');vo.inputs['Density'].default_value=.009;vo.inputs['Color'].default_value=(.59,.69,.72,1);vo.inputs['Anisotropy'].default_value=.24
out=ns.new('ShaderNodeOutputMaterial');fm.node_tree.links.new(vo.outputs['Volume'],out.inputs['Volume']);fog.data.materials.append(fm);fog.display_type='WIRE'
def camera(name,location,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);preview.objects.link(o);o.location=v(location);o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=350;return o
cam=camera('01_Player_Exit_View',(0,1.68,.25),(1.05,2.8,18),27)
camera('02_Forest_Path_View',(path_x(8),1.7+ground_y(path_x(8),8),8),(.0,3,32),30)
camera('03_Layout_Overview',(-36,40,-30),(0,4,30),32)
camera('04_Ground_Detail',(-.9,1.55,4.8),(-2.85,.34,6.65),40)
scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=64
scene.cycles.volume_bounces=1
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.3
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
    if any(d.type=='CUDA' for d in pref.devices):
        for d in pref.devices:d.use=d.type=='CUDA'
        scene.cycles.device='GPU'
except Exception as e:print('GPU fallback',e)

manifest={'package':'RELAY FOREST complete environment 02','source_coordinate_mapping':'Blender=(UnityX,UnityZ,UnityY)',
          'mount_parent':'MountainEnding','mount_local_position':[0,0,0],'mount_local_rotation':[0,0,0],'mount_local_scale':[1,1,1],
          'units':'metres','tree_count':len(tree_placements),'tree_placements':tree_placements,'rock_placements':rock_placements,
          'parts':[],'source_hashes_before':before,'preview_only':['lights','volumetric fog','cameras'],'automatic_lod':False}
def aggregate(collection,name):
    verts=[];faces=[];uvs=[];mis=[];mats=[];smooth=[]
    for o in sorted(collection.objects,key=lambda q:q.name):
        if o.type!='MESH':continue
        me=o.data;matrix=o.matrix_world;base=len(verts);verts.extend([matrix@q.co for q in me.vertices]);uv=me.uv_layers.active
        for f in me.polygons:
            faces.append(tuple(base+i for i in f.vertices));smooth.append(f.use_smooth)
            mt=me.materials[f.material_index]
            if mt not in mats:mats.append(mt)
            mis.append(mats.index(mt))
            for li in f.loop_indices:uvs.append(tuple(uv.data[li].uv))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    for m in mats:me.materials.append(m)
    for f,i,s in zip(me.polygons,mis,smooth):f.material_index=i;f.use_smooth=s
    uv=me.uv_layers.new(name='UVMap')
    for d,xy in zip(uv.data,uvs):d.uv=xy
    obj=bpy.data.objects.new(name,me);exports.objects.link(obj)
    points=[design(q.co) for q in me.vertices];me.calc_loop_triangles()
    record={'name':name,'file':name+'.fbx','vertices':len(me.vertices),'triangles':len(me.loop_triangles),
            'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)],
            'materials':[m.name for m in mats],'uv_loops_complete':len(uvs)==len(me.loops)}
    turn=Matrix.Rotation(math.pi,4,'Z');me.transform(turn);me.update()
    bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/record['file']),use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    # Export meshes are not retained in the artist scene: instanced editable originals remain.
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(me)
    return record
bpy.context.view_layer.update()
print('ENVIRONMENT_GEOMETRY_READY',len(tree_placements),flush=True)
# Save a render-ready scene before export as a recovery checkpoint.
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL';a.spaces.active.clip_end=350
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MountainForest.blend'))
for collection,name in ((terrain,'FOREST_Terrain'),(rocks,'FOREST_Rockwork'),(undergrowth,'FOREST_Undergrowth'),(near,'FOREST_Trees_Near'),(mid,'FOREST_Trees_Mid'),(far,'FOREST_Trees_Far'),(ridges,'FOREST_Ridges')):
    manifest['parts'].append(aggregate(collection,name));print('EXPORTED',name,flush=True)
manifest['total_triangles']=sum(p['triangles'] for p in manifest['parts'])
manifest['source_hashes_after']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
assert before==manifest['source_hashes_after'],'Unexpected Unity source change'
manifest['unity_project_unchanged']=True
manifest['path_trunk_clearance_m']=min(abs(t['x']-path_x(t['z']))-t['trunk_radius'] for t in tree_placements if 0<t['z']<19)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MountainForest.blend'))
print('FOREST_ENVIRONMENT_BUILD_OK',manifest['total_triangles'],flush=True)
