"""Render the saved art without rebuilding or altering Unity."""
import bpy, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_COOLING_v01.blend'))
scene=bpy.context.scene; camera=scene.camera
def aim(at): camera.rotation_euler=(Vector(at)-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=os.path.join(OUT,'previews','COOLING_hero.png'); bpy.ops.render.render(write_still=True)
camera.location=(0,-7,.14); aim((0,-.10,0)); camera.data.ortho_scale=2.92
scene.render.resolution_x=1200; scene.render.resolution_y=1500
scene.render.filepath=os.path.join(OUT,'previews','COOLING_front.png'); bpy.ops.render.render(write_still=True)
camera.location=(2.2,-5,1.25); aim((.02,-.59,.3)); camera.data.ortho_scale=1.53
scene.render.resolution_x=1200; scene.render.resolution_y=1000
scene.render.filepath=os.path.join(OUT,'previews','COOLING_controls.png'); bpy.ops.render.render(write_still=True)
print('FINAL_PREVIEWS_COMPLETE',flush=True)
