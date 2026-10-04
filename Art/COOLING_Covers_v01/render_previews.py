"""Render actual cover geometry in a separate Blender process; no Unity access."""
import bpy, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_COOLING_Covers_v01.blend'))
scene=bpy.context.scene;camera=scene.camera
draft='--draft' in sys.argv
scene.cycles.samples=12 if draft else 40
scene.render.resolution_percentage=60 if draft else 100
suffix='_draft' if draft else ''
def render(name,loc,target,scale,w,h):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale;scene.render.resolution_x=w;scene.render.resolution_y=h
    scene.render.filepath=str(OUT/'previews'/(name+suffix+'.png'))
    bpy.ops.render.render(write_still=True)
render('COOLING_with_covers',(3.8,-7.8,2.1),(0,-.06,0),3.30,1200,1500)
if '--hero-only' not in sys.argv:
    render('COOLING_covers_front',(0,-7,.12),(0,-.06,0),2.9,1200,1500)
    render('COOLING_cover_detail',(3.6,-4.4,1.3),(.36,-.32,-.20),1.90,1400,1100)
print('COVER_PREVIEWS_COMPLETE',flush=True)
