"""Actual Blender renders. Old RELAY equipment is preview context only."""
import bpy, math, sys
from pathlib import Path
from mathutils import Matrix, Vector
OUT=Path(__file__).resolve().parents[1]
ART=OUT.parent
assert bpy.app.background
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_Laboratory.blend'))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(a): return P@Vector(a)
context=bpy.data.collections.new('90_EXISTING_EQUIPMENT_PREVIEW_ONLY')
scene.collection.children.link(context)
studio=bpy.data.collections.new('91_RENDER_CAMERAS_LIGHTS_NOT_EXPORTED')
scene.collection.children.link(studio)

def append_collection(file,prefix):
    with bpy.data.libraries.load(str(file),link=False) as (a,b):
        b.collections=[n for n in a.collections if n.startswith(prefix)]
    assert len(b.collections)==1,(file,b.collections)
    c=b.collections[0]
    context.children.link(c)
    return c

core=append_collection(ART/'CORE_v01/RELAY_CORE_v01.blend','01_EDITABLE_CORE')
bpy.data.objects['REACTOR'].location=v((0,1.75,-1.5))
bpy.data.objects['CONTROL_CONSOLE'].location=v((3,1.2,4))
cool=append_collection(ART/'COOLING_v01/RELAY_COOLING_v01.blend','01_EDITABLE_COOLING')
bpy.data.objects['RELAY_COOLING_V01'].location=v((-3,1.2,4))
signal=append_collection(ART/'SIGNAL_v01/RELAY_SIGNAL_v01.blend','01_EDITABLE_SIGNAL')
bpy.data.objects['RELAY_SIGNAL_V01'].location=v((-1,1.2,4))
power=append_collection(ART/'POWER_v02_nameplate/RELAY_POWER_v02_nameplate.blend','01_EDITABLE_PARTS')
bpy.data.objects['RELAY_POWER_V02'].location=v((1,1.2,4))
cage=append_collection(ART/'ELEVATOR_v01/RELAY_MineElevator.blend','01_EDITABLE_CAGE')
for o in cage.objects:
    if o.parent is None: o.location+=v((0,0,-10))

light=append_collection(ART/'LIGHTING_v01/RELAY_Lighting.blend','01_SOURCE')
bulkheads=[o for o in light.objects if o.name.startswith('LIGHT_Bulkhead_MountPlane')]
for o in bulkheads:
    for child in list(o.children_recursive): bpy.data.objects.remove(child,do_unlink=True)
    bpy.data.objects.remove(o,do_unlink=True)
context.children.unlink(light)
for x in (-4,4):
    for z in (-6.5,-2,2.5):
        o=bpy.data.objects.new('Existing six ceiling fittings',None)
        o.instance_type='COLLECTION'; o.instance_collection=light; o.location=v((x,6,z)); context.objects.link(o)

def area(name,pos,target,power,color,size,second=None):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color
    d.shape='RECTANGLE'; d.size=size; d.size_y=second or size
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=v(pos)
    o.rotation_euler=(v(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

for x in (-4,4):
    for z in (-6.5,-2,2.5):
        area('Existing ceiling light - preview illumination',(x,5.76,z),(x,0,z),375,(1,.86,.69),.38,1.42)
area('Preview broad ambient bounce',(0,4.7,-2),(0,1,-2),180,(.70,.81,1),10,10)
for name in ('RLYL_Lens',):
    if name in bpy.data.materials:
        p=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF')
        p.inputs['Emission Color'].default_value=(1,.84,.61,1)
        p.inputs['Emission Strength'].default_value=4
em=bpy.data.materials.get('RLYK_Emitter')
if em:
    p=em.node_tree.nodes.get('Principled BSDF')
    p.inputs['Emission Color'].default_value=(.08,.48,1,1);p.inputs['Emission Strength'].default_value=3
# Core glow is shown only in the presentation file; runtime FX is untouched.
for dx,dz in ((-1,0),(1,0),(0,-1),(0,1)):
    area('Existing core bounce - preview',(.54*dx,1.85,-1.5+.54*dz),(3*dx,1.5,-1.5+3*dz),24,(.16,.47,1),.45,.9)

scene.render.engine='CYCLES'; scene.cycles.samples=40; scene.cycles.use_denoising=True
scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=4;scene.cycles.transmission_bounces=6
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='CUDA'
    if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
except Exception as e: print('GPU fallback',e)
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.render.resolution_x=1500;scene.render.resolution_y=980
scene.world=bpy.data.worlds.new('Lab preview world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.19,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.07
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
d=bpy.data.cameras.new('Laboratory presentation camera'); cam=bpy.data.objects.new('Laboratory presentation camera',d)
studio.objects.link(cam);scene.camera=cam
cam.data.clip_start=.05; cam.data.clip_end=180
def shot(filename,pos,target,lens=23):
    cam.data.type='PERSP';cam.data.lens=lens
    cam.location=v(pos);cam.rotation_euler=(v(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/'previews'/filename)
    bpy.ops.render.render(write_still=True)

draft='--draft' in sys.argv
if draft:
    scene.cycles.samples=20;scene.render.resolution_x=1100;scene.render.resolution_y=720
    shot('LAB_Draft.png',(6.4,2.4,-8.4),(-1.7,2.45,2.8),23)
else:
    shot('LAB_01_Interior.png',(6.4,2.4,-8.4),(-1.7,2.45,2.8),23)
    for screen in bpy.data.screens:
        for area_ui in screen.areas:
            if area_ui.type=='VIEW_3D':
                area_ui.spaces.active.region_3d.view_perspective='CAMERA'
                area_ui.spaces.active.shading.type='MATERIAL'
    # Save full context for inspection; presentation equipment never enters FBX.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_Laboratory_Review.blend'),compress=True)
    shot('LAB_02_Wall_Floor.png',(-4.9,1.05,-1.0),(-7.20,1.65,1.05),26)
    shot('LAB_03_Ceiling_Exit.png',(4.9,2.0,3.7),(-1.2,3.65,-7.4),22)
    shot('LAB_04_Pipe_Corner.png',(-4.1,3.65,-4.8),(-6.4,4.9,-8.7),25)
    shot('LAB_05_Back_Corner.png',(3.7,3.6,.7),(6.1,4.9,4.5),25)
print('LAB_RENDER_OK',flush=True)
