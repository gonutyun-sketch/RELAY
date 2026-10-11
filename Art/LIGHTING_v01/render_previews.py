"""Actual Blender renders of the lighting source. Does not touch Unity."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Matrix
assert bpy.app.background
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_Lighting.blend'))
bpy.context.preferences.filepaths.save_version=0
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(a): return P @ Vector(a)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=40
scene.cycles.use_denoising=True
scene.cycles.max_bounces=10
scene.cycles.transmission_bounces=8
scene.cycles.transparent_max_bounces=8
scene.render.image_settings.file_format='PNG'
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.19,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
studio=bpy.data.collections.new('03_PREVIEW_STUDIO_NOT_EXPORTED')
scene.collection.children.link(studio)
def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    studio.objects.link(o)
def material(name,color,rough):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    return m
back=material('Preview_only_ceiling',(.073,.086,.086),.88)
bpy.ops.mesh.primitive_cube_add(size=1,location=v((.32,.033,0)))
panel=bpy.context.object; panel.name='Preview_ceiling'; panel.scale=v((200,.060,200)); link(panel)
panel.data.materials.append(back)
def area(name,pos,target,power,color,size,size_y=None):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK' if size_y is None else 'RECTANGLE'; d.size=size
    if size_y is not None: d.size_y=size_y
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=v(pos); o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
area('Large_softbox',(-1.8,-2.8,1.6),(.3,-.05,0),340,(1,.94,.83),2.8,1.8)
area('Cool_edge',(2,-1.6,-1.1),(.4,-.1,0),180,(.79,.9,1),2,2)
area('Rim_strip',(-.8,-.8,-2),(.3,-.05,0),120,(1,1,1),1.8,.6)
d=bpy.data.cameras.new('Preview_Camera'); camera=bpy.data.objects.new('Preview_Camera',d); studio.objects.link(camera); scene.camera=camera
d.type='ORTHO'; d.lens=50
def shot(name,pos,target,ortho,res=(1600,1160)):
    camera.location=v(pos); camera.rotation_euler=(v(target)-camera.location).to_track_quat('-Z','Y').to_euler(); d.ortho_scale=ortho
    scene.render.resolution_x,scene.render.resolution_y=res
    scene.render.filepath=str(OUT/'previews'/name)
    bpy.ops.render.render(write_still=True)
def visible(root_name,value):
    root=bpy.data.objects[root_name]
    for o in [root]+list(root.children_recursive): o.hide_render=not value
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
if mode=='draft':
    scene.cycles.samples=16
    shot('LIGHTING_draft.png',(1.85,-3.6,2.9),(.35,-.06,0),2.7,(1100,800))
else:
    shot('LIGHTING_overview.png',(1.85,-3.6,2.9),(.35,-.06,0),2.7)
    # Save studio only to its own review file; neutral model file remains uncluttered.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_Lighting_Review.blend'))
    visible('LIGHT_Bulkhead_MountPlane_Y0',False)
    shot('LIGHT_Linear_detail.png',(-1.45,-2.8,2.1),(0,-.09,.04),2.06,(1500,1280))
    visible('LIGHT_Bulkhead_MountPlane_Y0',True)
    visible('LIGHT_Linear_MountPlane_Y0',False)
    shot('LIGHT_Bulkhead_detail.png',(1.6,-1.5,1.45),(.95,-.09,0),1.10,(1320,1320))
    visible('LIGHT_Linear_MountPlane_Y0',True)
    # Powered study is a Blender preview, not an authored always-on Unity material.
    lp=bpy.data.materials['RLYL_Lens'].node_tree.nodes.get('Principled BSDF')
    lp.inputs['Emission Color'].default_value=(1,.90,.71,1); lp.inputs['Emission Strength'].default_value=2
    for o in studio.objects:
        if o.type=='LIGHT': o.data.energy*=.3
    area('Linear_powered_bounce',(0,-.20,0),(0,-2,0),9,(1,.94,.83),1.3,.25)
    area('Bulkhead_powered_bounce',(.95,-.20,0),(.95,-2,0),4,(1,.94,.83),.48,.22)
    shot('LIGHTING_powered_study.png',(1.85,-3.6,2.9),(.35,-.06,0),2.7)
print('LIGHTING_PREVIEWS_OK')
