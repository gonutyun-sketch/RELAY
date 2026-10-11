"""RELAY exit retrofit. Writes ART ONLY, never a Unity scene or project asset."""
import bpy, bmesh, math, random, json, shutil, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.noise import noise_vector

OUT=Path(__file__).resolve().parents[1]
ART=OUT.parent
assert bpy.app.background
assert not OUT.is_relative_to(Path('C:/Users/gonut/School_p2'))
for d in ('exports','previews','checks','textures'): (OUT/d).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'FOREST_02_Environment/RELAY_MountainForest.blend'))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
R=random.Random(11102026)
def v(p): return P@Vector(p)
def col(n):
    c=bpy.data.collections.new(n);scene.collection.children.link(c);return c
hill=col('10_EXIT_Hillside');portal=col('11_EXIT_Headwall');landing=col('12_EXIT_Landing')
seals=col('13_EXIT_SealTrim_VISUAL_ONLY');apron=col('14_MOVING_ELEVATOR_LandingApron')
trees=col('15_EXIT_BackTrees');context=col('91_PREVIEW_Elevator_NOT_EXPORTED')
lightcol=bpy.data.collections['90_Preview_Lighting_Fog_Cameras']
terrain=bpy.data.collections['01_Terrain_and_Path']
undergrowth=bpy.data.collections['03_Ferns_and_Forest_Litter']

def color(h):
    return tuple(t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4 for t in [int(h[i:i+2],16)/255 for i in (0,2,4)])
def material(n,h,rough,metal=0,tex=False):
    m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*color(h),1)
    m.node_tree.nodes.clear();b=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');output=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(b.outputs['BSDF'],output.inputs['Surface']);b.inputs['Base Color'].default_value=m.diffuse_color
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if tex:
        for suffix,space in [('BaseColor','sRGB'),('Normal','Non-Color')]:
            im=bpy.data.images.load(str(OUT/'textures'/f'{n}_{suffix}.png'));im.colorspace_settings.name=space;im.pack()
            tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
            if suffix=='BaseColor':m.node_tree.links.new(tx.outputs['Color'],b.inputs['Base Color'])
            else:
                nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7
                m.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    return m
concrete=material('RLYX_AgedConcrete','6B6961',.87,tex=True)
steel=material('RLYX_DarkSteel','302F2B',.69,.78,True)
rubber=material('RLYX_SealRubber','171916',.95)
oxide=material('RLYX_SparseOxide','594334',.9,.25)
ochre=material('RLYX_FadedOchre','887640',.84,.15)
rock=bpy.data.materials['RLYF_DampGranite'];soil=bpy.data.materials['RLYF_ForestFloor']
moss=bpy.data.materials.get('RLYF_OldMoss') or material('RLYX_RockMoss','424A32',.97)

def mesh(n,points,faces,mats,c,smooth=False,recalc=True):
    me=bpy.data.meshes.new(n);me.from_pydata([v(p) for p in points],[],faces);me.update()
    for m in mats:me.materials.append(m)
    if recalc:
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(n,me);c.objects.link(o)
    for f in me.polygons:f.use_smooth=smooth
    project_uv(o)
    return o
def project_uv(o,scale=1.5):
    me=o.data;uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
    for f in me.polygons:
        n=v(f.normal);a=max(range(3),key=lambda i:abs(n[i]))
        for li in f.loop_indices:
            q=v(me.vertices[me.loops[li].vertex_index].co)
            uv.data[li].uv=((q.x,q.z) if a==1 else (q.z,q.y) if a==0 else (q.x,q.y))
            uv.data[li].uv/=scale
def box(n,center,size,m,c,bevel=.012):
    x,y,z=center;dx,dy,dz=[a/2 for a in size]
    points=[(x+a*dx,y+b*dy,z+d*dz) for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]]
    o=mesh(n,points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],[m],c)
    if bevel:
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        mod=o.modifiers.new('Small worn arris','BEVEL');mod.width=min(bevel,min(size)/4);mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False);project_uv(o)
    return o
def cylinder(n,center,r,depth,m,c,axis=(0,0,1),vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=v(center))
    o=bpy.context.object;o.name=n;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(axis))
    for cc in list(o.users_collection):cc.objects.unlink(o)
    c.objects.link(o);o.data.materials.append(m)
    return o

# Exact polygon subtraction retains material, winding and per-loop UVs.
RECTS=[(-1.75,1.75,-3.55,.55),(-2.65,2.65,-.82,-.16)]
TERRAIN_CUTS=[(-3.70,3.70,-3.80,1.75),(-1.70,1.70,1.74,2.75)]
def split(poly,axis,limit,positive):
    inside=[];outside=[]
    if not poly:return inside,outside
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=(a[0][axis]-limit)*positive;db=(b[0][axis]-limit)*positive
        ia=da>=-1e-9;ib=db>=-1e-9
        (inside if ia else outside).append(a)
        if ia!=ib:
            t=da/(da-db);q=(a[0].lerp(b[0],t),a[1].lerp(b[1],t))
            inside.append(q);outside.append(q)
    return inside,outside
def subtract(poly,rect):
    x0,x1,z0,z1=rect;res=[];cur=poly
    for axis,limit,sign in [(0,x0,1),(0,x1,-1),(2,z0,1),(2,z1,-1)]:
        cur,ext=split(cur,axis,limit,sign)
        if len(ext)>=3:res.append(ext)
        if len(cur)<3:break
    return res
cut_report=[]
for obj in [bpy.data.objects['Forest_Ground'],bpy.data.objects['Worn_Forest_Path']]:
    old=obj.data;verts=[];faces=[];uvfaces=[];mi=[];smooth=[];lookup={}
    for f in old.polygons:
        poly=[(v(old.vertices[old.loops[li].vertex_index].co),old.uv_layers.active.data[li].uv.copy()) for li in f.loop_indices]
        polys=[poly]
        for rect in TERRAIN_CUTS:
            new=[]
            for p in polys:
                xs=[a[0].x for a in p];zs=[a[0].z for a in p]
                if max(xs)<=rect[0] or min(xs)>=rect[1] or max(zs)<=rect[2] or min(zs)>=rect[3]:new.append(p)
                else:new.extend(subtract(p,rect))
            polys=new
        for p in polys:
            face=[];uv=[]
            for co,tc in p:
                key=tuple(round(x,7) for x in co)
                if key not in lookup:lookup[key]=len(verts);verts.append(co)
                idx=lookup[key]
                if not face or idx!=face[-1]:face.append(idx);uv.append(tc)
            if len(face)>1 and face[0]==face[-1]:face.pop();uv.pop()
            if len(set(face))<3:continue
            faces.append(face);uvfaces.append(uv);mi.append(f.material_index);smooth.append(f.use_smooth)
    me=bpy.data.meshes.new(old.name+'_ExitCut');me.from_pydata([v(p) for p in verts],[],faces);me.update()
    for m in old.materials:me.materials.append(m)
    uv=me.uv_layers.new(name='UVMap')
    for f,tcs in zip(me.polygons,uvfaces):
        f.material_index=mi[f.index];f.use_smooth=smooth[f.index]
        for li,tc in zip(f.loop_indices,tcs):uv.data[li].uv=tc
    obj.data=me
    cut_report.append({'object':obj.name,'old_faces':len(old.polygons),'new_faces':len(me.polygons),'all_upward':all(f.normal.z>0 for f in me.polygons)})

# Remove grass/twig/fern mesh islands that would sprout through the cage or new
# concrete. All undergrowth beyond the small construction footprint is retained.
vegetation_cut=[]
for obj in list(undergrowth.objects):
    if obj.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(obj.data);seen=set();remove=[]
    for start in bm.verts:
        if start in seen:continue
        island=[];stack=[start];seen.add(start);intrudes=False
        while stack:
            vv=stack.pop();island.append(vv);q=v(obj.matrix_world@vv.co)
            if (-3.78<q.x<3.78 and -3.85<q.z<1.83) or (-1.77<q.x<1.77 and 1.72<q.z<2.80):intrudes=True
            for e in vv.link_edges:
                other=e.other_vert(vv)
                if other not in seen:seen.add(other);stack.append(other)
        if intrudes:remove.extend(island)
    if remove:
        bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(obj.data);obj.data.update()
        vegetation_cut.append({'object':obj.name,'removed_vertices':len(remove)})
    bm.free()
    if not obj.data.polygons:bpy.data.objects.remove(obj,do_unlink=True)

def ground_y(x,z):
    zz=min(19,max(0,z));px=(1.5*math.sin(zz*.16)+.55*math.sin(zz*.39))*min(1,max(0,zz/4));d=abs(x-px)
    micro=.035*math.sin(x*1.2+z*.41)*math.sin(z*.8-x*.6)
    walk=.015*math.sin(z*.38)+micro*min(1,d/2);side=max(0,d-2)
    banks=.08*side+.24*math.sin(x*.33+z*.15)*min(1,side/3)
    if z<.7 and abs(x)<1.4:return 0
    return walk+banks
def hill_y(x,z):
    # Wide asymmetric escarpment, taper to the already placed forest at the front.
    dome=9.5*math.exp(-((x+2)/17)**4-((z+10)/15)**4)
    wobble=.75*math.sin(x*.39+z*.13)+.47*math.cos(x*.18-z*.55)+.25*math.sin(x*1.1+z*.76)
    front=max(0,min(1,(.85-z)/3.6));front=front*front*(3-2*front)
    outer=min(1,max(0,(24-abs(x))/3))*min(1,max(0,(z+27)/3))
    return ground_y(x,z)+max(0,dome+wobble)*front*outer
xs=[-24+i*.5 for i in range(97)];zs=[-27+j*.5 for j in range(57)]+[1.05]
pts=[(x,hill_y(x,z),z) for z in zs for x in xs];faces=[];nx=len(xs);nz=len(zs)
for j in range(nz-1):
    for i in range(nx-1):
        a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
rim=list(range(nx))+[j*nx+nx-1 for j in range(1,nz)]+list(range((nz-1)*nx+nx-2,(nz-1)*nx-1,-1))+[j*nx for j in range(nz-2,0,-1)]
bot=[]
for idx in rim:bot.append(len(pts));x,_,z=pts[idx];pts.append((x,-2.2,z))
for k in range(len(rim)):kk=(k+1)%len(rim);faces.append((rim[k],bot[k],bot[kk],rim[kk]))
faces.append(tuple(reversed(bot)))
h=mesh('Mountain_abutment_closed',pts,faces,[rock,soil],hill,True)
# Full depth cavity: never leave a bottom cap over the ascending cabin.
cutter=box('TEMP_PORTAL_VOID',(0,.85,-1.75),(5.48,6.2,5.5),rubber,context,0)
bpy.context.view_layer.objects.active=h
mod=h.modifiers.new('Open mine throat','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
bm=bmesh.new();bm.from_mesh(h.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
tiny=[f for f in bm.faces if f.calc_area()<1e-11]
if tiny:bmesh.ops.delete(bm,geom=tiny,context='FACES')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(h.data);bm.free();h.data.update()
project_uv(h,2.8)
for f in h.data.polygons:
    f.material_index=1 if f.normal.z>.68 else 0

# Embedded outcrops break the manufactured symmetry; existing trees are untouched.
def outcrop(x,z,sx,sy,sz):
    y=hill_y(x,z)-sy*.36
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
    for vv in bm.verts:
        q=vv.co;nv=noise_vector(q*2.4+Vector((x,z,7)));q*=1+.2*nv.x
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    pp=[(x+vv.co.x*sx,y+vv.co.z*sy,z+vv.co.y*sz) for vv in bm.verts]
    ff=[tuple(ve.index for ve in f.verts) for f in bm.faces];bm.free()
    o=mesh('Embedded_granite_%02d'%len(hill.objects),pp,ff,[rock,moss],hill,True)
    for f in o.data.polygons:
        if f.normal.z>.7 and R.random()<.48:f.material_index=1
for p in [(-4.7,-.9,1.55,1.3,1.15),(4.9,-1.2,1.9,1.6,1.4),(-6,-3.3,2.2,1.65,1.8),(7.3,-4,2.9,2.0,2.2),(-10,-5.6,2.2,1.3,2.0),(2,-7,2.6,1.5,1.7),(-4,-10,2.4,1.2,2.7),(11,-8,2.2,1.5,2.3),(-14,-7,1.6,1.4,1.7),(4,-16,2.8,1.6,1.6),(-7,-16,3,1.5,2),(-17,-11,1.8,1.6,2),(16,-9,1.7,1.2,2.1)]:outcrop(*p)

# Concrete retaining portal. The wide gate pockets stay open underneath.
for sign in (-1,1):
    for i,(yb,yt) in enumerate([(0,1.36),(1.37,2.72),(2.73,4.2)]):
        box('Pier_%s_%d'%(sign,i),(sign*2.75,(yb+yt)/2,.62),(2.0,yt-yb,1.12),concrete,portal,.035)
    box('Wing_return_'+str(sign),(sign*3.42,1.95,-1.34),(.32,3.9,3.45),concrete,portal,.025)
    box('Pocket_face_'+str(sign),(sign*2.23,1.72,-.015),(.96,3.36,.13),steel,portal,.009)
    box('Pocket_outer_'+str(sign),(sign*2.71,1.7,-.45),(.12,3.4,.94),steel,portal,.008)
    box('Pocket_rear_'+str(sign),(sign*2.23,1.7,-.9),(.96,3.4,.10),steel,portal,.009)
    box('Pocket_lintel_'+str(sign),(sign*2.19,3.46,-.45),(1.18,.14,1.03),steel,portal,.01)
    # Recessed guide channels and restrained fasteners, no decorative text.
    box('Opening_jamb_'+str(sign),(sign*1.76,1.93,1.208),(.095,3.85,.08),steel,portal,.006)
    for y in (.23,1.02,2.10,3.51):
        cylinder('Jamb_bolt',(sign*1.76,y,1.255),.023,.012,steel,portal)
    for y in (.35,2.85):
        box('Anchor_plate',(sign*2.58,y,1.195),(.22,.20,.025),steel,portal,.007)
        for dx in (-.065,.065):cylinder('Anchor_bolt',(sign*2.58+dx,y,1.218),.018,.02,steel,portal)
    box('Pocket_foot_guard_'+str(sign),(sign*2.2,.09,.10),(.90,.18,.16),steel,portal,.007)
    # Hairline casting joints and drip edges read at walking distance.
    box('Pier_base_'+str(sign),(sign*2.75,.08,.69),(2.0,.16,1.20),concrete,portal,.025)
box('Portal_header',(0,4.12,.60),(7.55,.65,1.34),concrete,portal,.045)
box('Roof_slab',(0,4.56,-1.57),(7.3,.28,5.52),concrete,portal,.035)
box('Header_steel_lip',(0,3.785,1.24),(3.62,.09,.17),steel,portal,.008)
box('Rain_drip',(0,4.44,1.32),(7.7,.08,.18),steel,portal,.008)
# Short shaft rim below grade; retains the existing long shaft and its colliders.
box('Throat_back_skin',(0,1.91,-3.475),(5.48,3.7,.035),rock,portal,.005)
for sign in (-1,1):box('Throat_side_skin',(sign*2.73,1.91,-2.02),(.035,3.7,2.85),rock,portal,.005)

# Landing ring made from closed cells outside the union of both apertures.
xc=[-3.70,-2.65,-1.75,1.75,2.65,3.70];zc=[-3.80,-3.55,-.82,-.16,.55,1.75]
def in_hole(x,z):return any(a<x<b and c<z<d for a,b,c,d in RECTS)
for i in range(len(xc)-1):
    for j in range(len(zc)-1):
        x=(xc[i]+xc[i+1])/2;z=(zc[j]+zc[j+1])/2
        if in_hole(x,z):continue
        box('Fixed_landing_%d_%d'%(i,j),(x,-.095,z),(xc[i+1]-xc[i],.19,zc[j+1]-zc[j]),concrete,landing,.003)
# Solid ramp into the unmodified path. It starts at the slab and meets ground.
pp=[(-1.70,0,1.74),(1.70,0,1.74),(1.7,ground_y(1.7,2.75)+.012,2.75),(-1.7,ground_y(-1.7,2.75)+.012,2.75)]
pp+= [(x,-.19,z) for x,_,z in pp]
mesh('Path_transition_ramp',pp,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],[concrete],landing)
# Fixed cast iron threshold sits outside moving floor at Z .55.
box('Fixed_threshold',(0,.002,.63),(3.48,.018,.15),steel,landing,.003)
for x in [-1.52,-1.1,-.7,-.3,.3,.7,1.1,1.52]:cylinder('Threshold_screw',(x,.014,.63),.012,.006,steel,landing,(0,1,0))
# Tread lines are shallow geometry, not holes through the walking surface.
for z in (.84,1.00,1.16,1.32):box('Tread_groove',(0,.003,z),(3.1,.003,.012),rubber,landing,0)

# Moving apron: fills just the perimeter; it is parented to ELEVATOR_Module.
for sign in (-1,1):box('Moving_side_flange_'+str(sign),(sign*1.6125,-.023,-1.5),(.175,.046,4.0),steel,apron,.002)
box('Moving_front_flange',(0,-.023,.303),(3.4,.046,.394),steel,apron,.002)
box('Moving_rear_flange',(0,-.023,-3.303),(3.4,.046,.394),steel,apron,.002)
for x in (-1.30,-.78,-.26,.26,.78,1.30):cylinder('Apron_rivet',(x,.004,.34),.012,.008,steel,apron,(0,1,0))
box('Moving_threshold_wear',(0,.002,.475),(3.37,.009,.04),ochre,apron,.001)
# Visual-only brush seams meet the apron while leaving the mesh hole open.
for sign in (-1,1):
    for z0,z1 in [(-3.55,-.82),(-.16,.55)]:
        box('Side_brush_seal',(sign*1.727,.006,(z0+z1)/2),(.064,.018,z1-z0),rubber,seals,.001)
box('Front_brush_seal',(0,.006,.527),(3.51,.018,.064),rubber,seals,.001)
box('Rear_brush_seal',(0,.006,-3.527),(3.51,.018,.064),rubber,seals,.001)
# Below-grade opaque skirts stop oblique sightlines without crossing the aperture.
for sign in (-1,1):
    for z0,z1 in [(-3.55,-.82),(-.16,.55)]:box('Landing_inner_skirt',(sign*1.771,-.35,(z0+z1)/2),(.04,.7,z1-z0),steel,seals,.004)
box('Front_inner_skirt',(0,-.35,.571),(3.58,.7,.04),steel,seals,.004)
box('Back_inner_skirt',(0,-.35,-3.571),(3.58,.7,.04),steel,seals,.004)

# Sparse, varied spruce skyline planted into the new bank; no changes to old trees.
for i,(x,z) in enumerate([(-11,-4),(-7.8,-6.4),(-15,-9),(-4.6,-8.6),(3.6,-8.5),(8.7,-6),(12.5,-7.2),(16,-12),(-18,-15),(-10,-15),(0,-15),(7,-17),(12,-19),(-4,-21),(-15,-21),(19,-17)]):
    scale=R.uniform(.63,.96);angle=R.uniform(0,math.tau);wide=R.uniform(.85,1.12);height=scale*R.uniform(.99,1.01)
    for part in ('Wood','Needles'):
        src=bpy.data.objects['SPRUCE_A_%s_LOD2'%part]
        o=bpy.data.objects.new('Exit_spruce_%02d_%s'%(i,part),src.data);trees.objects.link(o)
        o.location=v((x,hill_y(x,z)-.035,z));o.scale=(scale*wide,scale,height)
        o.rotation_euler=(0,0,angle)

# Elevator is preview context only. Old import's 180 degree correction is NOT
# applied here: the original Blender design already uses the audited coordinates.
with bpy.data.libraries.load(str(ART/'ELEVATOR_v01/RELAY_MineElevator.blend'),link=False) as (src,dst):
    dst.objects=list(src.objects)
roots={o.name:o for o in dst.objects if o.name in ('ELEVATOR_Cabin','ELEVATOR_DoorTrack','ELEVATOR_DoorLeft','ELEVATOR_DoorRight')}
included=set(roots.values())
for root in roots.values():included.update(root.children_recursive)
for name,o in roots.items():
    if 'DoorLeft' in name:o.location=v((-1.85,1.5,-.45))
    elif 'DoorRight' in name:o.location=v((1.85,1.5,-.45))
    else:o.location=(0,0,0)
for o in included:
    context.objects.link(o);o.name='PREVIEW_'+o.name;o.hide_render=False
print('PREVIEW_CABIN_MESH_COUNT',sum(o.type=='MESH' for o in included),flush=True)

# Relink image files into this portable package; keep all old art immutable.
for im in bpy.data.images:
    if im.source!='FILE':continue
    fn=Path(bpy.path.abspath(im.filepath)).name
    src=Path(bpy.path.abspath(im.filepath))
    dst=OUT/'textures'/fn
    if not dst.exists():
        if src.is_file():shutil.copy2(src,dst)
        elif im.packed_file:dst.write_bytes(im.packed_file.data)
    if dst.exists():im.filepath=str(dst);im.pack()

def camera(n,p,target,lens):
    data=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,data);lightcol.objects.link(o)
    o.location=v(p);o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=400
    return o
camera('EXIT_01_From_Forest',(.4,1.9,8.2),(0,3.1,-1.3),28)
camera('EXIT_02_Threshold_Detail',(.65,1.6,2.5),(0,.2,-.2),32)
camera('EXIT_03_From_Cage',(0,1.62,-1.7),(0,1.6,12),28)
camera('EXIT_04_Overview',(12,12,14),(0,1.7,-3),37)
camera('EXIT_05_Aperture',(6,9,7),(0,0,-1.3),46)
# Soft overcast bounce near entrance only, preview lighting is not exported.
ld=bpy.data.lights.new('PREVIEW_Exit_overcast_bounce','AREA');lo=bpy.data.objects.new(ld.name,ld);lightcol.objects.link(lo)
lo.location=v((0,6,6));lo.rotation_euler=(v((0,1,-2))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=1150;ld.shape='DISK';ld.size=8
scene.camera=bpy.data.objects['EXIT_01_From_Forest']
scene.render.resolution_x=1440;scene.render.resolution_y=960;scene.render.resolution_percentage=100

def export_part(c,name):
    bpy.context.view_layer.update();vv=[];ff=[];uvf=[];ids=[];sm=[];mats=[]
    for ob in c.objects:
        if ob.type!='MESH':continue
        me=ob.data;off=len(vv);vv.extend([ob.matrix_world@ve.co for ve in me.vertices]);mm={}
        for j,m in enumerate(me.materials):
            if m not in mats:mats.append(m)
            mm[j]=mats.index(m)
        for f in me.polygons:
            ff.append([off+i for i in f.vertices]);ids.append(mm.get(f.material_index,0));sm.append(f.use_smooth)
            uvf.append([me.uv_layers.active.data[li].uv.copy() for li in f.loop_indices] if me.uv_layers.active else [(0,0)]*len(f.vertices))
    me=bpy.data.meshes.new(name);me.from_pydata(vv,[],ff);me.update()
    for m in mats:me.materials.append(m)
    uv=me.uv_layers.new(name='UVMap')
    for f,coords in zip(me.polygons,uvf):
        f.material_index=ids[f.index];f.use_smooth=sm[f.index]
        for li,co in zip(f.loop_indices,coords):uv.data[li].uv=co
    design=[v(p) for p in vv];mn=[min(p[i] for p in design) for i in range(3)];mx=[max(p[i] for p in design) for i in range(3)]
    me.calc_loop_triangles();tris=len(me.loop_triangles)
    me.transform(Matrix.Rotation(math.pi,4,'Z'))
    ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    path=OUT/'exports'/f'{name}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    result={'name':name,'file':path.name,'vertices':len(vv),'triangles':tris,'unity_min':mn,'unity_max':mx,'materials':[m.name for m in mats],'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me)
    print('EXIT_EXPORT_OK',name,tris,flush=True)
    return result
parts=[]
for c,n in [(terrain,'FOREST_Terrain'),(undergrowth,'FOREST_Undergrowth'),(hill,'EXIT_Hillside'),(portal,'EXIT_Headwall'),(landing,'EXIT_Landing'),(seals,'EXIT_SealTrim'),(apron,'ELEVATOR_LandingApron'),(trees,'EXIT_BackTrees')]:parts.append(export_part(c,n))
manifest={'package':'RELAY forest exit integration 03','units':'metres','axis':'Unity +Y up, +Z forest; new exports use local identity','static_parent':'MountainEnding','moving_parent':'EXIT_Module/ELEVATOR_Module','rectangular_hole_union':RECTS,'terrain_removed_under_new_landing':TERRAIN_CUTS,'terrain_cut':cut_report,'parts':parts,'seed':11102026,'original_unity_scene_modified':False}
manifest['undergrowth_cleared_at_landing']=vegetation_cut
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
scene.camera=bpy.data.objects['EXIT_01_From_Forest']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_ForestExit_Review.blend'),compress=True)
print('EXIT_BUILD_COMPLETE',flush=True)
