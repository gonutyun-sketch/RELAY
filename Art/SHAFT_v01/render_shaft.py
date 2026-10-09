"""Actual Blender renders, with the existing cage used only as a review reference."""
import bpy, math
from pathlib import Path
from mathutils import Vector, Matrix
assert bpy.app.background
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_MineShaft.blend'))
bpy.context.preferences.filepaths.save_version=0
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(p):return P@Vector(p)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Review ambient')
scene.world.use_nodes=True
wn=scene.world.node_tree.nodes;wn.clear()
bg=wn.new('ShaderNodeBackground');wo=wn.new('ShaderNodeOutputWorld')
scene.world.node_tree.links.new(bg.outputs['Background'],wo.inputs['Surface'])
bg.inputs[0].default_value=(.15,.18,.22,1)
bg.inputs[1].default_value=.16
scene.view_settings.view_transform='AgX'
preview=bpy.data.collections.new('05_PREVIEW_ONLY');scene.collection.children.link(preview)
old=Path('C:/Users/gonut/RELAY_Art/ELEVATOR_v01/RELAY_MineElevator.blend')
with bpy.data.libraries.load(str(old),link=False) as (data_from,data_to):
    data_to.collections=['02_EXPORTS']
cage=data_to.collections[0];cage.name='06_REFERENCE_CAGE_NOT_EXPORTED';scene.collection.children.link(cage)
cage.hide_render=False;cage.hide_viewport=False
for o in cage.objects:
    o.hide_render=False;o.hide_set(False)
print('REFERENCE_CAGE_LOADED',len(cage.objects),flush=True)
roots=[o for o in cage.objects if o.parent is None]
base={o.name:o.location.copy() for o in roots}
def set_cage(height):
    for o in roots:o.location=base[o.name]+v((0,height,0))
def area(name,pos,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);preview.objects.link(o);o.location=v(pos)
    o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
def clear_lights():
    for o in list(preview.objects):
        if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
d=bpy.data.cameras.new('Shaft review camera');cam=bpy.data.objects.new('Shaft review camera',d)
preview.objects.link(cam);scene.camera=cam;d.clip_start=.05;d.clip_end=150
def camera(pos,target,lens=21):
    cam.location=v(pos);cam.rotation_euler=(v(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    d.type='PERSP';d.lens=lens
def cabin_view(height):
    set_cage(height);clear_lights()
    area('Cabin warm left',(-.55,height+2.93,-1.65),(-2.75,height+1.4,-2.6),170,(1,.79,.55),.55)
    area('Cabin neutral right',(.55,height+2.92,-1.55),(1.8,height+1.0,-3.6),125,(.80,.87,1),.55)
    area('Review soft bounce',(0,height+1.9,-.6),(-2.8,height+1.7,-2.4),35,(1,.86,.72),.9)
    camera((.48,height+1.63,-.92),(-2.75,height+1.6,-2.63),21)
    scene.render.resolution_x=1400;scene.render.resolution_y=950
def render(name):
    scene.render.filepath=str(OUT/'previews'/name);bpy.ops.render.render(write_still=True)
cabin_view(13.4)
print('MID_VIEW_READY',flush=True)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_MineShaft_Review.blend'))
render('SHAFT_CabinView.png')
cabin_view(27.2);render('SHAFT_UpperSoil.png')

# Cutaway overview is a separate inspection view, not an alternate exported model.
cage.hide_render=True
for name in ('Rock_R_Lower','Rock_R_Upper','Rock_Front_Mid','Roof_rock_cap'):
    bpy.data.objects[name].hide_render=True
clear_lights()
area('Cutaway key',(8,23,8),(0,17,-1.5),5500,(1,.87,.70),12)
area('Cutaway fill',(-5,11,9),(0,15,-1.5),3800,(.72,.83,1),10)
area('Cutaway top',(0,36,0),(0,26,-2),1800,(1,.90,.72),8)
camera((11,20,15),(0,16.4,-1.45));d.type='ORTHO';d.ortho_scale=37
scene.render.resolution_x=850;scene.render.resolution_y=1600;scene.cycles.samples=24
render('SHAFT_Cutaway.png')
print('SHAFT_PREVIEWS_OK')
