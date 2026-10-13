"""Reimport the delivered FBX in a separate Blender process and test geometry."""
import bpy, bmesh, json, math, hashlib
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'exports/LAB_Envelope.fbx'),use_anim=False)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
results=[]; vertices=[]; faces=[]
for o in objects:
    name=o.name.removesuffix('_GAME')
    item=next(p for p in manifest['parts'] if p['name']==name)
    coords=[P@(o.matrix_world@v.co) for v in o.data.vertices]
    lo=[min(v[i] for v in coords) for i in range(3)]
    hi=[max(v[i] for v in coords) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(lo+hi,item['min']+item['max']))
    me=o.data; me.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(me)
    loose=sum(not e.link_faces for e in bm.edges)
    boundary=sum(e.is_boundary for e in bm.edges)
    zero=sum(p.area<1e-12 for p in me.polygons)
    bm.free()
    checks=dict(bounds_match=error<2e-5,finite=all(math.isfinite(a) for v in coords for a in v),
        has_uv=len(me.uv_layers)>0,all_materials_assigned=all(m is not None for m in me.materials),
        no_loose_edges=loose==0,closed_components=boundary==0,no_zero_area_faces=zero==0,
        triangles_match=len(me.loop_triangles)==item['triangles'])
    results.append(dict(name=name,checks=checks,bounds_max_error=error,triangles=len(me.loop_triangles),
                        boundary_edges=boundary,zero_area_faces=zero))
    n=len(vertices)
    vertices.extend(tuple(o.matrix_world@v.co) for v in me.vertices)
    faces.extend(tuple(n+i for i in p.vertices) for p in me.polygons)
bvh=BVHTree.FromPolygons(vertices,faces)
def cast(origin,direction,distance):
    loc,normal,index,dist=bvh.ray_cast(P@Vector(origin),P@Vector(direction),distance)
    return None if loc is None else dict(point=list(P@loc),normal=list(P@normal),distance=dist)
tests=[]
def record(name,ok,hit=None): tests.append(dict(name=name,passed=bool(ok),hit=hit))
for x in (-5.7,-2.3,.4,3.9,5.9):
    for z in (-8.5,-3.3,.6,3.6):
        h=cast((x,1,z),(0,-1,0),2)
        record('floor_top_%s_%s'%(x,z),h and abs(h['point'][1])<.005 and h['normal'][1]>.99,h)
for x in (-5.1,0,5.1):
    for z in (-7.4,-2.5,2.5):
        h=cast((x,1,z),(0,1,0),6)
        record('ceiling_closed_%s_%s'%(x,z),h and 5.98<=h['point'][1]<=6.035 and h['normal'][1]<-.99,h)
for x in (-1.18,0,1.18):
    for y in (.1,1.5,2.94):
        h=cast((x,y,-9.4),(0,0,-1),1.1)
        record('doorway_clear_%s_%s'%(x,y),h is None,h)
h=cast((0,3.5,-9.4),(0,0,-1),1.1)
record('lintel_present',h is not None,h)
for x in (-1.55,0,1.55):
    h=cast((x,1,-9.7),(0,-1,0),2)
    record('apron_recess_%s'%x,h and h['point'][1]<=-.055,h)
for origin,direction,axis,value in [((0,2,-4.45),(-1,0,0),0,-7.744),((0,2,-4.45),(1,0,0),0,7.744),
                                     ((.4,2,2),(0,0,1),2,5.744),((4,2,-8),(0,0,-1),2,-9.744)]:
    h=cast(origin,direction,10)
    record('wall_inside_'+str(direction),h and abs(h['point'][axis]-value)<.02,h)
for origin,direction in [((0,2,-4),(-1,0,0)),((0,2,-4),(1,0,0)),((0,2,2),(0,0,1))]:
    h=cast(origin,direction,10)
    record('recessed_wall_joint_is_closed_'+str(direction),h is not None,h)
elements=json.loads((ROOT/'checks/source_elements.json').read_text(encoding='utf8'))
collisions=[]
for name,items in elements.items():
    for e in items:
        for x in (-4,4):
            for z in (-6.5,-2,2.5):
                lo=[x-.278,5.825,z-.895];hi=[x+.278,6,z+.895]
                if all(e['min'][i]<hi[i]-1e-4 and e['max'][i]>lo[i]+1e-4 for i in range(3)):
                    collisions.append(dict(part=name,element=e['name'],light=[x,6,z]))
record('six_light_mount_volumes_clear',not collisions)
scene=Path(r'C:\Users\gonut\School_p2\Assets\Scenes\Startup_Graybox.unity')
unchanged=hashlib.sha256(scene.read_bytes()).hexdigest()==manifest['scene_sha256']
report=dict(scope='Actual Blender FBX reimport plus ray tests; Unity import/playtest not performed.',
    parts=results,ray_tests=tests,light_intersections=collisions,unity_scene_unchanged=unchanged,
    all_passed=len(objects)==8 and unchanged and all(all(r['checks'].values()) for r in results) and all(t['passed'] for t in tests))
(ROOT/'checks/geometry_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('LAB_VALIDATION',json.dumps(dict(passed=report['all_passed'],parts=len(objects),tests=len(tests),
    failed_parts=[r for r in results if not all(r['checks'].values())],
    failed_tests=[t for t in tests if not t['passed']],light_intersections=collisions)),flush=True)
assert report['all_passed'], 'See checks/geometry_validation.json'
