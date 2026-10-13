"""Validate real closed source geometry and the mechanical termination graph."""
import bpy, json, math
from pathlib import Path
from collections import Counter
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
assert bpy.app.background
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'RELAY_Laboratory.blend'))
graph=json.loads((ROOT/'checks/service_network.json').read_text())
elements=json.loads((ROOT/'checks/source_elements.json').read_text())['LAB_Services']
mesh=bpy.data.objects['LAB_Services'].data
tests=[]
def check(name,passed,**evidence): tests.append(dict(name=name,passed=bool(passed),**evidence))

for run in graph['closed_runs']:
    element=next(e for e in elements if e['name']==run['name'])
    polygons=list(mesh.polygons)[element['first_face']:element['first_face']+element['face_count']]
    edges=Counter(); vertices=set()
    for poly in polygons:
        vv=list(poly.vertices); vertices.update(vv)
        for i,a in enumerate(vv): edges[tuple(sorted((a,vv[(i+1)%len(vv)])))]+=1
    euler=len(vertices)-len(edges)+len(polygons)
    # A continuous closed sweep has torus topology. A capped floating pipe
    # would have Euler characteristic 2 and cannot pass this test.
    check(run['name'],euler==0 and all(c==2 for c in edges.values()),
          euler_characteristic=euler,boundary_edges=sum(c!=2 for c in edges.values()))
    pts=[Vector(p) for p in run['points']]
    check(run['name']+'_nonzero_segments',all((pts[(i+1)%len(pts)]-p).length>.001 for i,p in enumerate(pts)))

for run in graph['terminated_runs']:
    for key,point in [('receiver_start',run['points'][0]),('receiver_end',run['points'][-1])]:
        receiver=run[key]
        if receiver['kind']=='enclosure':
            lo,hi=receiver['bounds']; inside=all(lo[i]<point[i]<hi[i] for i in range(3))
            check(run['name']+'_'+key,inside,point=point,receiver_bounds=[lo,hi])
        else:
            distance=(Vector(point)-Vector(receiver['position'])).length
            check(run['name']+'_'+key,distance<1e-5,distance=distance)
for item in graph['support_checks']:
    ok=abs(item['gap'])<1e-5 if item['must']=='contact' else item['gap']>=0
    check(item['name'],ok,gap=item['gap'])

# Additional measured small-detail corrections: no detached hardware and
# every removable grate tread has a common longitudinal support.
allparts=json.loads((ROOT/'checks/source_elements.json').read_text())
def overlaps(a,b): return all(min(a['max'][i],b['max'][i])-max(a['min'][i],b['min'][i])>1e-6 for i in range(3))
floors=allparts['LAB_Floor']
bearers=[e for e in floors if e['name']=='Removable grate longitudinal bearer']
treads=[e for e in floors if e['name']=='Cast grate tread']
ledge=[e for e in floors if e['name']=='Continuous grate seating ledge']
check('352_grate_treads_attached',len(treads)==352 and all(sum(overlaps(a,b) for b in bearers)==2 for a in treads))
check('grate_bearers_seated',all(any(overlaps(a,b) for b in ledge) for a in bearers))
for part,washer_name,plate_name in [('LAB_Wall_Left','Return grille bolt','Wall return outer frame'),
    ('LAB_Wall_Right','Return grille bolt','Wall return outer frame'),
    ('LAB_Wall_Exit','Jamb bolt','Door jamb folded edge'),
    ('LAB_Structure','Column splice bolt','Column joint plate')]:
    washers=[e for e in allparts[part] if e['name']==washer_name]
    plates=[e for e in allparts[part] if e['name']==plate_name]
    check(part+'_'+washer_name+'_seated',all(any(overlaps(a,b) for b in plates) for a in washers),count=len(washers))
report=dict(scope='Actual source mesh closed-loop topology, endpoint receivers and support contact geometry',
    closed_run_count=len(graph['closed_runs']),terminated_run_count=len(graph['terminated_runs']),
    tests=tests,all_passed=all(t['passed'] for t in tests))
(ROOT/'checks/services_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('SERVICES_VALIDATION',json.dumps(dict(passed=report['all_passed'],tests=len(tests),
    failed=[t for t in tests if not t['passed']])),flush=True)
assert report['all_passed']
