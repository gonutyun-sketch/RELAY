"""Additive COOLING guards. Run only in a separate background Blender process.

Reads the previous Blender source; writes only to this art package, never Unity.
Design coordinates: Unity X/right, Y/up, front/-Z, metres.
"""
import bpy, math, os, json, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix

assert bpy.app.background, 'Use background Blender, not the user editor session.'
OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'COOLING_v01'/'RELAY_COOLING_v01.blend'
PROJECT=Path('C:/Users/gonut/School_p2').resolve()
assert PROJECT not in OUT.parents and OUT != PROJECT
for sub in ('exports','previews','checks'): (OUT/sub).mkdir(parents=True,exist_ok=True)
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(u): return P@Vector(u)
def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
editable=collection('04_EDITABLE_PROTECTIVE_COVERS')
exported=collection('05_COVER_EXPORTS_HIDDEN')
def move(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)
def empty(name):
    o=bpy.data.objects.new(name,None);editable.objects.link(o);o.empty_display_size=.04;return o
assembly=empty('COOLING_PROTECTIVE_COVERS')
parts={};active=None
def part(name):
    global active
    active=empty(name);active.parent=assembly;parts[name]=active;return active
frame=bpy.data.materials['RLYC_FramePaint']
rubber=bpy.data.materials['RLYC_Rubber']
steel=bpy.data.materials['RLYC_Steel']
ink=bpy.data.materials['RLYC_PrintDark']
glass=bpy.data.materials.new('RLYC_CoverGlass');glass.use_nodes=True
def srgb(h):
    return tuple((c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for c in [int(h[i:i+2],16)/255 for i in (0,2,4)])+(1,)
glass.diffuse_color=srgb('DCEAE6')
bsdf=glass.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=glass.diffuse_color
bsdf.inputs['Roughness'].default_value=.09
bsdf.inputs['Transmission Weight'].default_value=1
bsdf.inputs['IOR'].default_value=1.45
glass['Unity surface']='Transparent / Alpha / Front / no shadow'
glass['Unity alpha']=.14
def register(o,name,loc,mat):
    move(o,editable);o.name=name;o.parent=active;o.location=v(loc)
    if mat:o.data.materials.append(mat)
    return o
def bevel(o,width=.001,segments=2):
    if width:
        b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=width;b.segments=segments
        b=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');b.keep_sharp=True
def box(name,loc,dims,mat,width=.001):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=register(bpy.context.object,name,loc,mat);o.scale=v(dims)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel(o,width);return o
def cylinder(name,loc,r,depth,mat,axis='Z',vertices=24,width=.0005):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth)
    o=register(bpy.context.object,name,loc,mat)
    o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]))
    bevel(o,width)
    for face in o.data.polygons: face.use_smooth=len(face.vertices)==4
    return o
def ring(name,cx,cy,z,w,h,strip,depth,mat):
    box(name+' left',(cx-w/2-strip/2,cy,z),(strip,h+2*strip,depth),mat,.0007)
    box(name+' right',(cx+w/2+strip/2,cy,z),(strip,h+2*strip,depth),mat,.0007)
    box(name+' upper',(cx,cy+h/2+strip/2,z),(w,strip,depth),mat,.0007)
    box(name+' lower',(cx,cy-h/2-strip/2,z),(w,strip,depth),mat,.0007)
def bolt(name,loc,axis='Z'):
    cylinder(name+' washer',loc,.010,.0025,steel,axis,24,0)
    d={'Z':(0,0,-.003),'X':(.003 if loc[0]>0 else -.003,0,0)}[axis]
    q=tuple(loc[i]+d[i] for i in range(3))
    cylinder(name+' slotted head',q,.007,.005,steel,axis,24,.0005)
    if axis=='Z':box(name+' slot',(q[0],q[1],q[2]-.0026),(.010,.0015,.0005),ink,0)
    else:box(name+' slot',(q[0]+(.0026 if q[0]>0 else -.0026),q[1],q[2]),(.0005,.0015,.010),ink,0)

# Front guard is behind the interactive faces, with four actual through-openings.
# Existing control origins are preserved; no simulated glass over the controls.
front_z=-.513
rect_holes=[
    dict(name='FLOW meter',x=-.32,y=.35,w=.634,h=.572),
    dict(name='PUMP switch',x=-.30,y=-.40,w=.308,h=.352),
    dict(name='THERMAL display',x=.28,y=-.217,w=.528,h=.358),
]
valve_hole=dict(x=.28,y=.35,r=.118)
part('COOLING_CoverFrame')
# Front perimeter fits the existing header bottom and drip tray top.
ring('Front guard perimeter',0,-.09,-.506,1.630,1.878,.022,.025,frame)
ring('Front glass bedding',0,-.09,-.510,1.611,1.859,.010,.007,rubber)
for x in (-.842,.842):
    for y in (-.96,-.30,.34,.79):
        box('Front clamp bridge',(x,y,-.481),(.040,.049,.064),frame,.002)
        bolt('Front guard fixing',(x,y,-.520))
# Narrow rubber liners provide a plausible protected edge at the penetrations.
for hole in rect_holes:
    ring(hole['name']+' edge liner',hole['x'],hole['y'],front_z,hole['w'],hole['h'],.0035,.009,rubber)
# Valve passes through a packed circular penetration, well behind the wheel.
bpy.ops.mesh.primitive_torus_add(major_radius=.121,minor_radius=.003,major_segments=64,minor_segments=8)
o=register(bpy.context.object,'Valve penetration edge seal',(.28,.35,front_z),rubber)
o.rotation_euler=(math.pi/2,0,0)
for face in o.data.polygons:face.use_smooth=True

# Side covers are distinct exports to avoid one transparent object spanning both sides.
for side in (-1,1):
    sx=side*.898
    for z in (-.411,.411):
        box('Side guard vertical channel',(sx,.022,z),(.016,2.17,.023),frame,.002)
        box('Side vertical glass bedding',(sx,.022,z+(.008 if z<0 else -.008)),(.008,2.14,.012),rubber,.0005)
    for y in (-1.059,1.103):
        box('Side guard horizontal channel',(sx,y,0),(.016,.023,.84),frame,.002)
        box('Side horizontal bedding',(sx,y+(.008 if y<0 else -.008),0),(.008,.012,.80),rubber,.0005)
    for y in (-.97,.05,1.01):
        for z in (-.399,.399):
            box('Side retaining clip',(side*.909,y,z),(.012,.052,.034),steel,.002)
            bolt('Side cover fixing',(side*.919,y,z),'X')
        for z in (-.434,.434):
            box('Side channel mounting spacer',(side*.883,y,z),(.068,.045,.040),frame,.002)

part('COOLING_FrontGlass')
front=box('Six millimetre front guard',(0,-.09,front_z),(1.630,1.878,.006),glass,0)
cutters=[]
for hole in rect_holes:
    cutters.append(box(hole['name']+' cutter',(hole['x'],hole['y'],front_z),(hole['w'],hole['h'],.15),None,0))
cutters.append(cylinder('Valve penetration cutter',(.28,.35,front_z),valve_hole['r'],.15,None,'Z',64,0))
for cutter in cutters:
    bpy.context.view_layer.objects.active=front
    m=front.modifiers.new('Through opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
bevel(front,.0006,2)
part('COOLING_LeftGlass')
box('Left six millimetre guard',(-.898,.022,0),(.006,2.162,.822),glass,.0006)
part('COOLING_RightGlass')
box('Right six millimetre guard',(.898,.022,0),(.006,2.162,.822),glass,.0006)

# Export additive units only. Old models, interaction pivots, gauges and lamps stay intact.
bpy.context.view_layer.update()
manifest=dict(asset='RELAY COOLING protective covers v01',source_blend=str(SOURCE),source_sha256=source_hash,
    additive_only=True,unity_modified=False,units='metres',front='Unity -Z',
    preserved_flow_glass_local_z=.01,front_glass_z=front_z,rectangular_openings=rect_holes,valve_opening=valve_hole,
    import_note='All four new FBX children: parent COOLING_Module, local position zero, rotation Y180, scale1. No new colliders.',
    materials=[dict(name='RLYC_CoverGlass',hex='DCEAE6',alpha=.14,metallic=0,smoothness=.91,surface='Transparent',blend='Alpha',render_face='Front',cast_shadows=False,receive_shadows=False),
               *[dict(name=m.name,reuse_existing=True) for m in (frame,rubber,steel,ink)]],parts=[])
for name,pivot in parts.items():
    copies=[]
    for original in list(pivot.children):
        if original.type!='MESH':continue
        dup=original.copy();dup.data=original.data.copy();exported.objects.link(dup);dup.parent=None;dup.matrix_world=original.matrix_world.copy();copies.append(dup)
    bpy.ops.object.select_all(action='DESELECT')
    for dup in copies:dup.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.convert(target='MESH')
    if len(bpy.context.selected_objects)>1:bpy.ops.object.join()
    ob=bpy.context.object;ob.name=name+'_EXPORT'
    # Boolean cuts may introduce empty material slots; keep only actual used materials.
    used=[];indices=[]
    for face in ob.data.polygons:
        fm=ob.data.materials[face.material_index] if face.material_index<len(ob.data.materials) else None
        fm=fm or glass
        if fm not in used:used.append(fm)
        indices.append(used.index(fm))
    ob.data.materials.clear()
    for fm in used:ob.data.materials.append(fm)
    for face,index in zip(ob.data.polygons,indices):face.material_index=index
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.uv.smart_project(island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/f'{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')
    coords=[P@vv.co for vv in ob.data.vertices]
    manifest['parts'].append(dict(name=name,file=f'exports/{name}.fbx',triangles=sum(len(f.vertices)-2 for f in ob.data.polygons),vertices=len(ob.data.vertices),materials=[m.name for m in ob.data.materials],bounds_unity_local=[[min(p[i] for p in coords),max(p[i] for p in coords)] for i in range(3)],unity_parent='Environment/COOLING_Module',position=[0,0,0],rotation=[0,180,0],scale=[1,1,1]))
    ob.hide_render=True;ob.hide_set(True)
manifest['triangles_total']=sum(p['triangles'] for p in manifest['parts'])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
# Preview preserves the user's meter-lens adjustment without changing its original source.
meter_root=bpy.data.objects.get('FLOW_Glass')
if meter_root:meter_root.location+=v((0,0,.01))
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1200;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.camera.location=(3.8,-7.8,2.1)
scene.camera.rotation_euler=(Vector((0,-.06,0))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=3.30
bpy.ops.object.select_all(action='DESELECT');assembly.select_set(True);bpy.context.view_layer.objects.active=assembly
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_COOLING_Covers_v01.blend'))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
print('COOLING_COVERS_BUILT',manifest['triangles_total'],flush=True)
