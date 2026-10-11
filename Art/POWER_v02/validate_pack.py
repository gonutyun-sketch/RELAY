"""Check exported geometry without launching or modifying Unity."""
import bpy, os, json, math
from mathutils import Vector, Matrix, Euler
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v02.blend'))
with open(os.path.join(OUT,'manifest.json'),encoding='utf-8') as f: manifest=json.load(f)
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def rotation(u): return (P @ Euler(tuple(math.radians(a) for a in u),'XYZ').to_matrix() @ P).to_quaternion()
def bounds(coords):
    return [[min(c[i] for c in coords),max(c[i] for c in coords)] for i in range(3)]
checks=[]
for record in manifest['parts']:
    name=record['name']; ob=bpy.data.objects[name+'_EXPORT']
    assert ob.type=='MESH' and len(ob.data.vertices)>0 and ob.data.uv_layers
    assert all(slot.material for slot in ob.material_slots)
    assert all(math.isfinite(c) for vert in ob.data.vertices for c in vert.co)
    expected=bounds([vert.co for vert in ob.data.vertices])
    previous=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT,record['file']))
    imported=set(bpy.data.objects)-previous
    meshes=[o for o in imported if o.type=='MESH']
    actual=bounds([o.matrix_world @ vert.co for o in meshes for vert in o.data.vertices])
    error=max(abs(a-b) for pair1,pair2 in zip(expected,actual) for a,b in zip(pair1,pair2))
    assert error<.0001,(name,error,expected,actual)
    assert all(o.data.uv_layers for o in meshes)
    checks.append({'part':name,'fbx_roundtrip_max_bounds_error_m':error,
        'uv_present':True,'triangles':record['triangles'],'bounds_blender_xyz':expected})
    for o in imported: bpy.data.objects.remove(o,do_unlink=True)

# Check full MAIN motion, not just the endpoint screenshots.
main=bpy.data.objects['MAIN_Handle_EXPORT']
control_position=Vector((.28,-.75,-.65))
minimum_floor=999; minimum_panel=999
for angle in range(-155,-24):
    q=rotation((angle,0,0))
    for vert in main.data.vertices:
        u=P @ (q @ vert.co)+control_position
        minimum_floor=min(minimum_floor,u.y+1.2)
        minimum_panel=min(minimum_panel,-.514-u.z)
assert minimum_floor>.04,minimum_floor
assert minimum_panel>.015,minimum_panel

# Source is editable; exported meshes remain hidden and won't double-render.
camera=bpy.context.scene.camera
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active; sp.shading.type='MATERIAL'
            sp.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            sp.region_3d.view_location=Vector((0,-.1,0)); sp.region_3d.view_distance=4.7
            sp.clip_end=200
bpy.ops.object.select_all(action='DESELECT')
assembly=bpy.data.objects['RELAY_POWER_V02']; assembly.select_set(True)
bpy.context.view_layer.objects.active=assembly
for ob in bpy.data.collections['03_PREVIEW_ONLY'].objects:
    if ob.type in {'LIGHT','CAMERA'}: ob.hide_set(True)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
for image in bpy.data.images:
    if image.filepath and image.source=='FILE': image.pack()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v02.blend'))
report={'parts_checked':len(checks),'total_triangles':sum(p['triangles'] for p in checks),
    'unity_runtime_tested':False,'unity_files_modified':False,
    'main_full_travel_degrees':[-155,-25],
    'main_minimum_floor_clearance_m':minimum_floor,
    'main_minimum_fixed_fascia_clearance_m':minimum_panel,'checks':checks}
with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f: json.dump(report,f,indent=2)
print('VALIDATED_V02',json.dumps({k:v for k,v in report.items() if k!='checks'}))

# Actuated overview demonstrates moving origins without baking a Unity animation.
for name,angles in {'AUX_Handle':(0,0,-25),'MAIN_Handle':(-155,0,0),
                    'VOLTAGE_Knob':(0,0,-54),'BALANCE_Knob':(0,0,0),'Gauge_Needle':(0,0,-67.5)}.items():
    ob=bpy.data.objects[name]; ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rotation(angles)
scene=bpy.context.scene; scene.cycles.samples=20; camera.hide_set(False)
scene.render.filepath=os.path.join(OUT,'previews','POWER_v02_operated.png')
bpy.ops.render.render(write_still=True)
