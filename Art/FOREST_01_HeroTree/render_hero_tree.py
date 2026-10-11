"""Render actual asset, neutral inspection views first; preview scene is not an exported terrain."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_FOREST_Spruce_A.blend'))
bpy.context.preferences.filepaths.save_version=0
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=96;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    if any(d.type=='CUDA' for d in prefs.devices):
        for dev in prefs.devices:dev.use=dev.type=='CUDA'
        scene.cycles.device='GPU'
        print('REVIEW_RENDER_DEVICE_CUDA',flush=True)
except Exception as e:print('REVIEW_CPU_FALLBACK',str(e),flush=True)
scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=64
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Overcast forest review');scene.world.use_nodes=True
ns=scene.world.node_tree.nodes;ns.clear();bg=ns.new('ShaderNodeBackground');wo=ns.new('ShaderNodeOutputWorld')
bg.inputs['Color'].default_value=(.45,.54,.66,1);bg.inputs['Strength'].default_value=.38
scene.world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface'])
prev=bpy.data.collections.new('90_REVIEW_ONLY');scene.collection.children.link(prev)
def area(name,pos,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);prev.objects.link(o);o.location=P@Vector(pos)
    o.rotation_euler=(P@Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Overcast key',(-5,10,-6),(0,5,0),3000,(1,.91,.77),8)
area('Cool open sky',(5,11,3),(0,5,0),2700,(.66,.8,1),7)
area('Soft front lift',(1,5,-8),(0,4,0),700,(.82,.91,1),7)
# A neutral ground is used only to read the roots and silhouette.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.075));ground=bpy.context.object;ground.name='REVIEW_Ground_not_exported'
for c in list(ground.users_collection):c.objects.unlink(ground)
prev.objects.link(ground)
m=bpy.data.materials.new('REVIEW_Ground');m.use_nodes=True;ns=m.node_tree.nodes;ns.clear();p=ns.new('ShaderNodeBsdfPrincipled');mo=ns.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],mo.inputs['Surface']);p.inputs['Base Color'].default_value=(.045,.054,.044,1);p.inputs['Roughness'].default_value=.98;ground.data.materials.append(m)
d=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',d);prev.objects.link(cam);scene.camera=cam
def camera(pos,target,lens):
    cam.location=P@Vector(pos);cam.rotation_euler=(P@Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.03;d.clip_end=300
def render(name,x,y):
    scene.render.resolution_x=x;scene.render.resolution_y=y;scene.render.filepath=str(OUT/'previews'/name)
    print('RENDER_BEGIN',name,flush=True);bpy.ops.render.render(write_still=True);print('RENDER_END',name,flush=True)
camera((12,6.5,-17),(0,5.85,0),48)
scene.render.resolution_x=1000;scene.render.resolution_y=1300
if '--quick' in sys.argv:
    scene.cycles.samples=16
    render('FOREST_Silhouette_Working.png',650,850)
    print('QUICK_REVIEW_OK',flush=True)
    raise SystemExit(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_FOREST_Spruce_A_Review.blend'))
render('FOREST_Spruce_A_Full.png',1000,1300)
camera((1.9,1.2,-2.9),(0,.95,0),61)
render('FOREST_Spruce_A_BarkRoots.png',1300,1050)
mf=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
t=Vector(mf['needle_detail_target']);camera(t+Vector((.25,.55,-2.0)),t,66)
scene.cycles.samples=128
render('FOREST_Spruce_A_Needles.png',1300,1000)
print('FOREST_PREVIEWS_OK',flush=True)
