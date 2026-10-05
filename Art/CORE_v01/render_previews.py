"""Render actual saved CORE model. Preview-only lighting does not enter exports."""
import bpy, os, math
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_CORE_v01.blend'))
s=bpy.context.scene; camera=s.camera
def aim(at): camera.rotation_euler=(Vector(at)-camera.location).to_track_quat('-Z','Y').to_euler()
def render(name):
    s.render.filepath=os.path.join(OUT,'previews',name+'.png'); bpy.ops.render.render(write_still=True)
s.cycles.samples=36; s.render.resolution_percentage=100
render('CORE_hero')
# Front console review shows the exact existing controls and live display openings.
camera.location=(3.95,-6.5,.6); aim((2.55,-.15,-.52)); camera.data.ortho_scale=2.98
s.render.resolution_x=1150; s.render.resolution_y=1400
render('CORE_controls')
# Modest emission study only. No particle effects or power-driven behavior here.
console=bpy.data.objects['CONTROL_CONSOLE']
def hide_children(ob):
    ob.hide_render=True
    for child in ob.children: hide_children(child)
hide_children(console)
camera.location=(3.6,-7,2.2); aim((0,0,-.02)); camera.data.ortho_scale=4.38
s.render.resolution_x=1250; s.render.resolution_y=1450
m=bpy.data.materials['RLYK_Emitter'].node_tree.nodes.get('Principled BSDF')
m.inputs['Emission Color'].default_value=(.10,.55,1,1); m.inputs['Emission Strength'].default_value=4
s.world.node_tree.nodes['Background'].inputs[1].default_value=.12
for name in ('Workshop softbox','High cool bounce','Front reflected light'):
    bpy.data.objects[name].data.energy*=.35
for zz in (-.40,.40):
    light=bpy.data.lights.new('ENERGIZED STUDY ONLY','POINT'); light.energy=28; light.color=(.15,.63,1); light.shadow_soft_size=.22
    o=bpy.data.objects.new(light.name,light); s.collection.objects.link(o); o.location=(0,0,zz)
render('CORE_emission_study')
print('CORE_PREVIEWS_COMPLETE',flush=True)
