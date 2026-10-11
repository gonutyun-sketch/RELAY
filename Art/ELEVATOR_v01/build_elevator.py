"""RELAY mine cage. Creates art files only, outside Unity. Blender 5.2 background."""
import bpy, math, json, bmesh, random, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np
assert bpy.app.background
OUT=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\gonut\School_p2').resolve()
assert not OUT.is_relative_to(PROJECT)
for folder in ('exports','textures','previews','checks'): (OUT/folder).mkdir(parents=True,exist_ok=True)
scene_file=PROJECT/'Assets/Scenes/Startup_Graybox.unity'
scene_hash=hashlib.sha256(scene_file.read_bytes()).hexdigest()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
src=bpy.data.collections.get('Collection'); src.name='01_EDITABLE_CAGE'
ex=bpy.data.collections.new('02_EXPORTS'); bpy.context.scene.collection.children.link(ex)
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(a): return P @ Vector(a)
def rgb(h):
    a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in a)
def material(name,col,metal,rough):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb(col),1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m
iron=material('RLYE_Iron','323936',.55,.62)
paint=material('RLYE_FadedPaint','666857',.15,.72)
steel=material('RLYE_WornSteel','858679',.80,.43)
rust=material('RLYE_Oxide','604638',.12,.92)
yellow=material('RLYE_Ochre','A8904E',.10,.74)
dark=material('RLYE_Dark','222521',0,.92)
wood=material('RLYE_Timber','7B6650',0,.88)
# Two compact, real image textures survive FBX handoff; all source images are packed.
rng=np.random.default_rng(31); n=512; yy,xx=np.mgrid[0:n,0:n]
fine=rng.random((n,n)).astype(np.float32)
grain=(np.sin(yy*.44 + 1.2*np.sin(xx*.014)+.65*np.sin(xx*.041))* .035
       +np.sin(yy*1.71+np.sin(xx*.021))*.014)
board=np.clip(.75+grain+(fine-.5)*.075,0,1)
for k in range(26):
    row=int(rng.integers(3,n-4)); start=int(rng.integers(0,430)); end=min(512,start+int(rng.integers(35,190)))
    board[row:row+int(rng.integers(1,3)),start:end]*=.68
def image_texture(name,pixels,mat):
    im=bpy.data.images.new(name,width=n,height=n,alpha=True)
    im.pixels.foreach_set(pixels.astype(np.float32).ravel()); im.filepath_raw=str(OUT/'textures'/(name+'.png')); im.file_format='PNG'; im.save(); im.pack()
    nodes=mat.node_tree.nodes; tex=nodes.new('ShaderNodeTexImage'); tex.image=im
    mat.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    return im
rgba=np.ones((n,n,4),dtype=np.float32); rgba[:,:,:3]=board[:,:,None]*np.array([.54,.44,.32])[None,None,:]
image_texture('RLYE_Timber_BaseColor',rgba,wood)
noise=.78+(fine-.5)*.08+.04*np.sin(xx*.073)*np.sin(yy*.093)
rgba=np.ones((n,n,4),dtype=np.float32); rgba[:,:,:3]=noise[:,:,None]*np.array([.30,.34,.315])[None,None,:]
image_texture('RLYE_Iron_BaseColor',rgba,iron)

def empty(name,pos=(0,0,0)):
    o=bpy.data.objects.new(name,None); src.objects.link(o); o.location=v(pos); o.empty_display_size=.16
    return o
def move_collection(o,col=src):
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o)
def finish(o,name,mat,parent,bevel=0):
    o.name=name; move_collection(o); o.parent=parent; o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Edge radius','BEVEL'); b.width=bevel; b.segments=2
        w=o.modifiers.new('Corner normals','WEIGHTED_NORMAL'); w.keep_sharp=True
    return o
def box(name,pos,size,mat,parent,bevel=.004):
    bpy.ops.mesh.primitive_cube_add(size=1,location=v(pos)); o=bpy.context.object; o.scale=v(size)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    # Independent per-board atlas region and correctly oriented timber grain.
    if mat==wood:
        uv=o.data.uv_layers.active; shift=(sum(ord(c) for c in name)*.017)%1
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                q=P@o.data.vertices[o.data.loops[li].vertex_index].co
                if abs(poly.normal.z)>.5:
                    u=q.x/max(.01,size[0]); vv=q.z/max(.01,size[2])
                elif abs(poly.normal.y)>.5:
                    u=q.x/max(.01,size[0]); vv=q.y/max(.01,size[1])
                else:
                    u=q.z/max(.01,size[2]); vv=q.y/max(.01,size[1])
                uv.data[li].uv=(u*.8+.5,vv*.31+shift)
    return finish(o,name,mat,parent,bevel)
def cylinder(name,pos,r,depth,mat,parent,axis=(0,0,1),verts=12,bevel=.001):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=v(pos)); o=bpy.context.object
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(axis).normalized())
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return finish(o,name,mat,parent,bevel)
def bar(name,a,b,width,mat,parent,depth=None):
    a,b=Vector(a),Vector(b); direction=v(b-a)
    o=box(name,(a+b)*.5,(width,(b-a).length,depth or width),mat,parent,.002 if width>.025 else 0)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(direction.normalized())
    return o
def bolt(name,pos,parent,axis=(0,0,1),r=.014):
    cylinder(name+'_washer',pos,r*1.45,.003,steel,parent,axis,12,0)
    tip=Vector(pos)+Vector(axis)*.004
    cylinder(name+'_hex',tip,r,.009,steel,parent,axis,6,.001)
def mesh(name,verts,faces,mat,parent):
    me=bpy.data.meshes.new(name); me.from_pydata([v(x) for x in verts],[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); src.objects.link(o); o.parent=parent; me.materials.append(mat)
    # Complete stable planar UVs for untextured rods too.
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li in p.loop_indices:
            q=me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv=(q.x,q.z)
    return o
def lattice(name,u0,u1,y0,y1,mapper,parent,spacing=.17,r=.005):
    verts=[]; faces=[]
    def rod(a,b):
        a,b=Vector(a),Vector(b); t=(b-a).normalized(); ref=Vector((0,0,1))
        if abs(t.dot(ref))>.9: ref=Vector((1,0,0))
        s=t.cross(ref).normalized()*r; z=t.cross(s).normalized()*r; start=len(verts)
        for c in (a,b):
            for j in range(4): verts.append(tuple(c+s*math.cos(j*math.pi/2)+z*math.sin(j*math.pi/2)))
        faces.extend([(start+i,start+(i+1)%4,start+4+(i+1)%4,start+4+i) for i in range(4)])
        faces.extend([(start+3,start+2,start+1,start),(start+4,start+5,start+6,start+7)])
    for sign in (-1,1):
        vals=[y-sign*u for y in (y0,y1) for u in (u0,u1)]
        for k in range(math.floor(min(vals)/spacing),math.ceil(max(vals)/spacing)+1):
            c=k*spacing; pts=[]
            for u in (u0,u1):
                y=sign*u+c
                if y0-1e-7<=y<=y1+1e-7: pts.append((u,y))
            for y in (y0,y1):
                u=(y-c)/sign
                if u0-1e-7<=u<=u1+1e-7: pts.append((u,y))
            if len(pts)>=2 and Vector(pts[0])!=Vector(pts[1]): rod(mapper(*pts[0]),mapper(*pts[1]))
    return mesh(name,verts,faces,iron,parent)

cabin=empty('ELEVATOR_Cabin')
left=empty('ELEVATOR_DoorLeft',(-.6,1.5,-.45))
right=empty('ELEVATOR_DoorRight',(.6,1.5,-.45))
track=empty('ELEVATOR_DoorTrack')
parts=[cabin,left,right,track]
for p in parts: p['Axis_Convention']='Unity metres; +Y up; entrance +Z; cabin extends -Z'
# Riveted platform and replaceable timber deck, top exactly at collider floor y=0.
box('Underfloor_slab',(0,-.23,-1.50),(3.05,.26,3.25),iron,cabin,.013)
for x in (-1.48,1.48): box('Deck_side_channel',(x,-.085,-1.50),(.13,.17,3.25),iron,cabin,.007)
for z in (-3.06,.06): box('Deck_end_channel',(0,-.085,z),(2.96,.17,.13),iron,cabin,.007)
for i in range(14):
    z=-2.95+i*.216
    box('Timber_deck_%02d'%i,(0,-.047,z),(2.84,.094,.210),wood,cabin,.003)
    for x in (-1.22,1.22): bolt('Deck_bolt',(x,-.009,z),cabin,(0,1,0),.007)
for x in (-1.14,1.14): box('Deck_wear_strip',(x,-.001,-1.50),(.07,.002,3.15),steel,cabin,.0005)
box('Entrance_threshold',(0,-.026,-.37),(2.9,.052,.27),steel,cabin,.004)
for i in range(5): box('Threshold_groove',(0,.001,-.475+i*.051),(2.7,.001,.007),dark,cabin,0)
# Main pillars remain outside the existing 2.4m clear walking width.
for x in (-1.30,1.30):
    for z in (-2.84,-.62):
        box('Riveted_upright',(x,1.50,z),(.20,3.0,.18),iron,cabin,.008)
        box('Pillar_shoe',(x,.15,z),(.27,.30,.25),paint,cabin,.006)
        box('Top_gusset',(x,2.87,z),(.27,.26,.25),paint,cabin,.006)
        for y in (.10,.24,2.80,2.92): bolt('Post_fastener',(x,y,z+.13),cabin,r=.012)
    for y in (.88,2.87): box('Side_rail',(x,y,-1.73),(.12,.09,2.2),iron,cabin,.004)
    # Low timber kickboards keep the upper walls visually open toward the future shaft.
    for row in range(3):
        box('Side_kickboard_%s_%s'%(x,row),(x,.22+row*.22,-1.73),(.065,.21,2.02),wood,cabin,.003)
    lattice('Side_diamond_mesh',-2.74,-.71,.94,2.81,lambda u,y,x=x:(x,y,u),cabin)
    bar('Side_diagonal_strap',(x*1.045,1.00,-2.68),(x*1.045,2.80,-.78),.041,paint,cabin,.028)
    for z in (-2.62,-.84):
        for y in (1.02,2.79): bolt('Side_strap_bolt',(x*1.061,y,z),cabin,(1 if x>0 else -1,0,0),.011)
# Back panel has a mounting patch for the existing pushbutton at x=.75,y=1.2.
for y in (.88,2.87): box('Rear_rail',(0,y,-2.84),(2.45,.09,.12),iron,cabin,.004)
for row in range(3): box('Rear_kickboard_%02d'%row,(0,.22+row*.22,-2.815),(2.42,.21,.07),wood,cabin,.003)
lattice('Rear_diamond_mesh',-1.19,1.19,.94,2.81,lambda u,y:(u,y,-2.84),cabin)
box('Existing_button_mount',(.75,1.2,-2.793),(.36,.50,.046),paint,cabin,.006)
for x in (.605,.895):
    for y in (1.00,1.40): bolt('Button_mount_bolt',(x,y,-2.762),cabin,r=.009)
box('Rear_handhold',(0,1.05,-2.75),(1.35,.05,.025),yellow,cabin,.008)
# Roof framing and folded canopy; underside clearance remains three metres.
for x in (-1.30,1.30): box('Roof_side_channel',(x,3.075,-1.73),(.22,.15,2.55),iron,cabin,.006)
for z in (-2.88,-.55): box('Roof_cross_channel',(0,3.075,z),(2.83,.15,.19),iron,cabin,.006)
for i in range(8):
    z=-2.90+i*.34
    box('Canopy_sheet_%02d'%i,(0,3.18,z),(2.78,.055,.352),paint,cabin,.003)
    box('Canopy_fold',(0,3.216,z-.16),(2.78,.027,.023),iron,cabin,.002)
box('Hoist_crossmember',(0,3.29,-1.72),(2.1,.16,.27),iron,cabin,.009)
for x in (-.62,.62):
    box('Lifting_lug_base',(x,3.39,-1.72),(.29,.12,.23),steel,cabin,.006)
    # Arc is geometry; the cable/shaft itself is intentionally outside today's model scope.
    for j in range(12):
        a=j*math.pi/12; b=(j+1)*math.pi/12
        bar('Lifting_eye',(x+.085*math.cos(a),3.43+.10*math.sin(a),-1.72),(x+.085*math.cos(b),3.43+.10*math.sin(b),-1.72),.030,steel,cabin)
# Small weathered wear marks at real handling edges, with restrained colour variation.
r=random.Random(17)
for side in (-1,1):
    for j in range(18):
        y=r.uniform(.34,2.64); z=r.choice((-.62,-2.84)); x=side*(1.30+r.uniform(-.055,.055))
        box('Edge_scuff',(x,y,z+.091),(r.uniform(.008,.035),r.uniform(.012,.065),.0012),rust if j%3 else steel,cabin,0)

def gate(part,hand):
    # All positions here are local to the EXISTING panel-centred door pivot.
    for x in (-.554,.554): box('Gate_stile',(x,0,0),(.092,2.984,.138),iron,part,.006)
    for y in (-1.45,-.75,1.45): box('Gate_crossrail',(0,y,0),(1.12,.090,.138),iron,part,.004)
    box('Gate_kickplate',(0,-1.105,.005),(1.024,.596,.043),paint,part,.003)
    lattice('Gate_diamond_mesh',-.507,.507,-.701,1.401,lambda u,y:(u,y,0),part,spacing=.14,r=.005)
    bar('Gate_diagonal',(-.49,-.68,-.025),(.49,1.38,-.025),.031,paint,part,.024)
    grip_x=.37*hand
    bar('Ochre_grip',(grip_x,-.16,.06),(grip_x,.18,.06),.032,yellow,part)
    for y in (-.16,.18): box('Grip_standoff',(grip_x,y,.03),(.041,.041,.061),steel,part,.003)
    for x in (-.43,.43):
        for y in (-1.35,-.85,1.45): bolt('Gate_rivet',(x,y,.071),part,r=.009)
    for j in range(8):
        x=r.uniform(-.46,.46); y=r.uniform(-1.33,-.88)
        box('Kickplate_wear',(x,y,.027),(r.uniform(.03,.15),.004,.001),rust,part,0)
gate(left,1); gate(right,-1)
# A separate track matches the game's unusually wide saved opening travel.
box('Upper_track_back',(0,3.115,-.475),(5.06,.19,.065),iron,track,.004)
box('Upper_track_lip',(0,3.025,-.407),(5.06,.035,.20),steel,track,.003)
box('Upper_track_weather_cover',(0,3.227,-.43),(5.06,.05,.31),paint,track,.004)
for x in (-2.50,2.50):
    box('Track_stop',(x,3.09,-.365),(.055,.16,.10),yellow,track,.004)
    box('Lower_stop',(x,.029,-.43),(.055,.05,.10),iron,track,.002)
box('Lower_guide',(0,.012,-.43),(5.06,.024,.045),steel,track,.002)
for x in (-1.30,1.30):
    box('Track_mount',(x,3.145,-.56),(.25,.24,.22),iron,track,.004)
    for dx in (-.075,.075): bolt('Track_mount_bolt',(x+dx,3.16,-.435),track,r=.012)

scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
manifest={'package':'RELAY mine elevator v01','units':'metres','parts':[],
 'unity_scene_sha256_before':scene_hash,'notes':['Visual asset only; preserve original gameplay colliders and scripts.',
 'Door panels have independent centre pivots; exported alone at origin.',
 'Track width 5.06m accommodates original 1.25m opening travel.',
 'Image textures must accompany FBX; they are packed in the Blender file.']}
for part in parts:
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.update(); pivot=part.matrix_world.translation.copy()
    copies=[]
    for o in part.children_recursive:
        if o.type!='MESH': continue
        c=o.copy(); c.data=o.data.copy(); ex.objects.link(c); c.parent=None; c.matrix_world=o.matrix_world.copy(); c.select_set(True); copies.append(c)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.convert(target='MESH')
    if len(bpy.context.selected_objects)>1: bpy.ops.object.join()
    o=bpy.context.object; o.name=part.name+'_Mesh'; scene.cursor.location=pivot; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    # Preserve polygon material assignment AFTER clearing slots; otherwise Blender resets indices.
    mats=[]; indices=[]
    for poly in o.data.polygons:
        m=o.data.materials[poly.material_index]
        if m not in mats: mats.append(m)
        indices.append(mats.index(m))
    o.data.materials.clear()
    for m in mats: o.data.materials.append(m)
    for poly,idx in zip(o.data.polygons,indices): poly.material_index=idx
    save=o.matrix_world.copy(); o.matrix_world=Matrix.Identity(4)
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/(part.name+'.fbx')),use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    coords=[P@q.co for q in o.data.vertices]; lo=[min(c[i] for c in coords) for i in range(3)]; hi=[max(c[i] for c in coords) for i in range(3)]
    manifest['parts'].append({'name':part.name,'unity_min':lo,'unity_max':hi,'source_pivot':list(P@pivot),
      'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'materials':[m.name for m in mats],
      'used_material_indices':sorted(set(f.material_index for f in o.data.polygons)),'uv_layers':len(o.data.uv_layers)})
    o.matrix_world=save; o.hide_render=True; o.hide_set(True)
ex.hide_viewport=True; ex.hide_render=True
scene.cursor.location=(0,0,0); bpy.ops.object.select_all(action='DESELECT'); cabin.select_set(True); bpy.context.view_layer.objects.active=cabin
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            reg=a.spaces.active.region_3d; reg.view_distance=7; reg.view_location=v((0,1.5,-1.2)); reg.view_rotation=(v((0,1.5,-1.2))-v((5,4,6))).to_track_quat('-Z','Y')
            a.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MineElevator.blend'))
manifest['total_triangles']=sum(p['triangles'] for p in manifest['parts'])
manifest['unity_scene_sha256_after']=hashlib.sha256(scene_file.read_bytes()).hexdigest()
assert manifest['unity_scene_sha256_after']==scene_hash,'Unity scene changed while generating; investigate external edits.'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('MINE_ELEVATOR_BUILD_OK',manifest['total_triangles'])
