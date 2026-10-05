"""Sample the real articulated starter handle against its fixed housing."""
import bpy, os, json, math
from mathutils import Matrix, Vector, Euler
from mathutils.bvhtree import BVHTree
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_CORE_v01.blend'))
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
fixed=bpy.data.objects['START_Housing_EXPORT']
fixedv=[P@v.co for v in fixed.data.vertices]
fixedf=[tuple(p.vertices) for p in fixed.data.polygons]
fixedbvh=BVHTree.FromPolygons(fixedv,fixedf)
moving=bpy.data.objects['START_Handle_EXPORT']
mv=[P@v.co for v in moving.data.vertices]
mf=[tuple(p.vertices) for p in moving.data.polygons]
bad=[]
for n in range(131):
    angle=-25-n
    R=Euler((math.radians(angle),0,0),'XYZ').to_matrix()
    verts=[R@v+Vector((0,0,-.1)) for v in mv]
    overlaps=fixedbvh.overlap(BVHTree.FromPolygons(verts,mf))
    if overlaps: bad.append({'angle_x':angle,'face_pair_count':len(overlaps)})
# The neutral stem/grip stay inside the existing clickable stem/grip box union.
# Pivot axle is fixed through the bearing and deliberately tested separately.
stem=bpy.data.objects['Forged lever stem']; grip=bpy.data.objects['Bakelite grip']
deps=bpy.context.evaluated_depsgraph_get()
neutralchecks=[]
for ob,center,dims in [(stem,(0,.18,0),(.06,.36,.06)),(grip,(0,.36,0),(.28,.09,.1))]:
    evaluated=ob.evaluated_get(deps); me=evaluated.to_mesh()
    points=[P@(ob.matrix_local@v.co) for v in me.vertices]
    ok=all(all(abs(p[i]-center[i])<=dims[i]/2+1e-5 for i in range(3)) for p in points)
    neutralchecks.append({'part':ob.name,'fits_existing_neutral_collider':ok})
    evaluated.to_mesh_clear()
report={'samples':131,'off_x':-25,'on_x':-155,'intersections':bad,'clickable_fit':neutralchecks,
 'passed':not bad and all(c['fits_existing_neutral_collider'] for c in neutralchecks),
 'note':'Geometric swept-pose check only; Unity animation/input is not run.'}
with open(os.path.join(OUT,'checks','lever_sweep.json'),'w',encoding='utf-8') as f: json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
if not report['passed']: raise SystemExit(1)
