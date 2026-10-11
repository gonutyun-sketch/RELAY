import bpy, math
from pathlib import Path
from mathutils import Matrix, Vector
assert bpy.app.background
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_MineElevator.blend'))
bpy.context.preferences.filepaths.save_version=0
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(a): return P@Vector(a)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.cycles.max_bounces=7
scene.render.resolution_x=1450; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.18,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
studio=bpy.data.collections.new('03_PREVIEW_ONLY'); scene.collection.children.link(studio)
def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    studio.objects.link(o)
# Show actual saved OPEN travel; these changes are confined to the review file.
bpy.data.objects['ELEVATOR_DoorLeft'].location=v((-1.85,1.5,-.45))
bpy.data.objects['ELEVATOR_DoorRight'].location=v((1.85,1.5,-.45))
bpy.ops.mesh.primitive_plane_add(size=200,location=v((0,-.365,0)))
o=bpy.context.object; o.name='Studio_ground'; link(o)
m=bpy.data.materials.new('Studio_ground'); m.diffuse_color=(.11,.13,.13,1); m.use_nodes=True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=m.diffuse_color
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.84
o.data.materials.append(m)
def area(name,pos,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=v(pos); o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Warm_key',(2,6,3),(0,1,-1.2),1350,(1,.85,.68),5)
area('Soft_fill',(-4,3,3),(0,1.4,-1),850,(.74,.84,1),4)
area('Roof_rim',(1,5,-5),(0,1.5,-1.5),1500,(1,.93,.80),3)
area('Interior_fill',(0,2.85,-1.4),(0,0,-1.5),45,(1,.85,.65),1.2)
d=bpy.data.cameras.new('Preview_camera'); camera=bpy.data.objects.new('Preview_camera',d); studio.objects.link(camera); scene.camera=camera
camera.location=v((5.4,4.6,7.0)); camera.rotation_euler=(v((0,1.47,-1.35))-camera.location).to_track_quat('-Z','Y').to_euler()
d.type='ORTHO'; d.ortho_scale=7.3; d.lens=55
scene.render.filepath=str(OUT/'previews'/'ELEVATOR_overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MineElevator_Review.blend'))
bpy.ops.render.render(write_still=True)
print('ELEVATOR_PREVIEW_OK')
