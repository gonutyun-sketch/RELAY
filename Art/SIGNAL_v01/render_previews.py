"""Render the standalone SIGNAL asset; no Unity access or changes."""
import bpy, os, sys
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_SIGNAL_v01.blend'))
scene=bpy.context.scene; camera=scene.camera
draft='--draft' in sys.argv
scene.cycles.samples=12 if draft else 32
scene.render.resolution_percentage=65 if draft else 100
suffix='_draft' if draft else ''
def render(name,loc,target,scale,width,height):
    camera.location=loc; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    scene.render.resolution_x=width; scene.render.resolution_y=height
    scene.render.filepath=os.path.join(OUT,'previews',name+suffix+'.png')
    bpy.ops.render.render(write_still=True)
render('SIGNAL_hero',(3.8,-7.8,2.1),(0,-.06,0),3.36,1200,1500)
if '--hero-only' not in sys.argv:
    render('SIGNAL_front',(0,-7,.1),(0,-.06,0),2.92,1200,1500)
    render('SIGNAL_controls',(1.7,-5.5,1.4),(0,-.58,.08),1.85,1500,1150)
print('SIGNAL_PREVIEWS_COMPLETE',flush=True)
