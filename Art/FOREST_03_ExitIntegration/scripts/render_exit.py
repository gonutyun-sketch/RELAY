import bpy,sys
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'draft'
scene=bpy.context.scene
cam=bpy.data.objects['EXIT_01_From_Forest'];cam.location=(.4,8.2,1.9)
cam.rotation_euler=(Vector((0,-1.3,3.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28
scene.render.engine='CYCLES';scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='CUDA';prefs.get_devices()
    if any(d.type=='CUDA' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='CUDA'
        scene.cycles.device='GPU'
except Exception:pass
scene.cycles.transparent_max_bounces=64;scene.cycles.max_bounces=8
scene.render.resolution_percentage=100
scene.render.resolution_x=1280 if mode=='draft' else 1440
scene.render.resolution_y=850 if mode=='draft' else 960
scene.cycles.samples=20 if mode=='draft' else 32
cams=['EXIT_01_From_Forest'] if mode=='draft' else ['EXIT_01_From_Forest','EXIT_02_Threshold_Detail','EXIT_03_From_Cage','EXIT_04_Overview']
if mode=='overview':
    cams=['EXIT_04_Overview'];scene.cycles.samples=24
    scene.render.resolution_x=1360;scene.render.resolution_y=900
if mode=='aperture':
    cams=['EXIT_05_Aperture'];scene.cycles.samples=20
    for n in ['11_EXIT_Headwall','10_EXIT_Hillside','15_EXIT_BackTrees','91_PREVIEW_Elevator_NOT_EXPORTED','14_MOVING_ELEVATOR_LandingApron']:
        if n in bpy.data.collections:bpy.data.collections[n].hide_render=True
    for ob in bpy.data.collections['90_Preview_Lighting_Fog_Cameras'].objects:
        if ob.type=='MESH':ob.hide_render=True
for n in cams:
    scene.camera=bpy.data.objects[n];scene.render.filepath=str(OUT/'previews'/(n+'.png'))
    bpy.ops.render.render(write_still=True)
    print('EXIT_RENDER_OK',n,flush=True)
