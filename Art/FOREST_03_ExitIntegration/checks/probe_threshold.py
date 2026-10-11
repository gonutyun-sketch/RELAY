import bpy,json
from mathutils import Vector
from pathlib import Path
out=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(out/'RELAY_ForestExit_Review.blend'))
cam=bpy.data.objects['EXIT_02_Threshold_Detail'];deps=bpy.context.evaluated_depsgraph_get()
inv=(cam.calc_matrix_camera(deps,x=1440,y=960)@cam.matrix_world.inverted()).inverted()
for x,y in [(800,873),(950,843),(1000,825),(1100,800),(1200,765),(720,800)]:
    p=inv@Vector((2*x/1440-1,1-2*y/960,-1,1));p=Vector(p[:3])/p.w
    hit=bpy.context.scene.ray_cast(deps,cam.location,(p-cam.location).normalized(),distance=25)
    print('PIXEL',x,y,'OBJECT',hit[4].name if hit[0] else None,'POINT',list(hit[1]) if hit[0] else None,flush=True)
