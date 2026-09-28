import bpy, os, json
from mathutils import Matrix, Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v01.blend'))
with open(os.path.join(OUT,'manifest.json'),encoding='utf-8') as f: manifest=json.load(f)
checks=[]
def extent(coords):
    return [max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
for record in manifest['parts']:
    name=record['name']; mesh=bpy.data.objects[name+'_Mesh']
    assert mesh.type=='MESH' and mesh.data.uv_layers
    assert len(mesh.data.vertices)>0 and len(mesh.data.polygons)>0
    assert all(s.material is not None for s in mesh.material_slots)
    expected=extent([x.co for x in mesh.data.vertices])
    bpy.ops.object.select_all(action='DESELECT')
    clone=mesh.copy(); clone.data=mesh.data.copy(); bpy.context.collection.objects.link(clone)
    clone.parent=None; clone.matrix_world=Matrix.Identity(4); clone.name=name+'__Visual'
    clone.select_set(True); bpy.context.view_layer.objects.active=clone
    path=os.path.join(OUT,record['file'])
    bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
        add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    bpy.data.objects.remove(clone,do_unlink=True)
    previous=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    imported=set(bpy.data.objects)-previous
    imported_meshes=[o for o in imported if o.type=='MESH']
    actual=extent([ob.matrix_world @ vert.co for ob in imported_meshes for vert in ob.data.vertices])
    error=max(abs(a-b) for a,b in zip(expected,actual))
    assert error<.0001, (name,expected,actual,error)
    assert all(ob.data.uv_layers for ob in imported_meshes)
    checks.append({'part':name,'fbx_roundtrip_max_extent_error_m':error,'uv_present':True,'triangles':record['triangles']})
    for ob in imported: bpy.data.objects.remove(ob,do_unlink=True)

# Make the source self-contained and pleasant to open without touching Unity.
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['RELAY_POWER_Assembly'].select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['RELAY_POWER_Assembly']
camera=bpy.context.scene.camera
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='MATERIAL'
            space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            space.region_3d.view_location=Vector((0,-.1,0))
            space.region_3d.view_distance=4.7
            space.clip_end=200
for ob in bpy.data.collections['PREVIEW_ONLY'].objects:
    if ob.type in {'LIGHT','CAMERA'}: ob.hide_set(True)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v01.blend'))
with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:
    json.dump({'parts_checked':len(checks),'total_triangles':sum(r['triangles'] for r in checks),
               'unity_runtime_tested':False,'checks':checks},f,indent=2)
print('VALIDATED_ALL_PARTS',len(checks))
scene=bpy.context.scene
camera.hide_set(False)
camera.location=(0,-7,.25)
camera.rotation_euler=(Vector((0,-.5,0))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=2.85
scene.render.resolution_x=1000; scene.render.resolution_y=1200
scene.cycles.samples=16; scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.filepath=os.path.join(OUT,'previews','POWER_front.png')
bpy.ops.render.render(write_still=True)
