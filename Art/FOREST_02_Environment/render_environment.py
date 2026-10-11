"""Render real Blender scene cameras, without touching Unity."""
import bpy, sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
scene=bpy.context.scene
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'draft'
pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='CUDA';pref.get_devices()
if any(d.type=='CUDA' for d in pref.devices):
    for d in pref.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU'
scene.render.engine='CYCLES';scene.cycles.use_denoising=True
scene.cycles.transparent_max_bounces=64;scene.cycles.max_bounces=8
if mode=='delivery':
    cameras=[('01_Player_Exit_View','FOREST_Player_Exit'),('04_Ground_Detail','FOREST_Ground_Detail'),('02_Forest_Path_View','FOREST_Path_and_Valley'),('03_Layout_Overview','FOREST_Layout_Overview')]
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.cycles.samples=32
elif mode=='draft':
    cameras=[('01_Player_Exit_View','FOREST_Draft')]
    scene.render.resolution_x=1120;scene.render.resolution_y=700;scene.cycles.samples=24
elif mode=='overview':
    cameras=[('03_Layout_Overview','FOREST_Layout_Overview')]
    scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.cycles.samples=24
    bpy.data.objects['PREVIEW_ONLY_Valley_Mist'].hide_render=True
elif mode=='detail':
    cameras=[('04_Ground_Detail','FOREST_Ground_Detail')]
    scene.render.resolution_x=1360;scene.render.resolution_y=1020;scene.cycles.samples=40
elif mode=='detailcheck':
    cameras=[('04_Ground_Detail','FOREST_Detail_Check')]
    scene.render.resolution_x=960;scene.render.resolution_y=720;scene.cycles.samples=16
else:
    cameras=[('01_Player_Exit_View','FOREST_Player_Exit'),('02_Forest_Path_View','FOREST_Path_and_Valley')]
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.cycles.samples=48
for camera,filename in cameras:
    if camera=='02_Forest_Path_View':
        scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.cycles.samples=24
    if mode=='delivery' and camera=='04_Ground_Detail':
        scene.render.resolution_x=1360;scene.render.resolution_y=1020;scene.cycles.samples=32
    if mode=='delivery' and camera=='03_Layout_Overview':
        scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.cycles.samples=16
        bpy.data.objects['PREVIEW_ONLY_Valley_Mist'].hide_render=True
    scene.camera=bpy.data.objects[camera]
    scene.render.filepath=str(OUT/'previews'/(filename+'.png'))
    bpy.ops.render.render(write_still=True)
    print('FOREST_RENDER_OK',filename,flush=True)
