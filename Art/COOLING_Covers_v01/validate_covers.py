"""Read the saved meshes and round-trip the actual additive FBX exports.
Checks physical glazing clearance, original controls, closed surfaces and source integrity.
"""
import bpy, math, json, hashlib, bmesh
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_COOLING_Covers_v01.blend'))
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,detail):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def coords(ob,world=False):return [P@(ob.matrix_world@vv.co if world else vv.co) for vv in ob.data.vertices]
def mesh_bvh(ob,pts=None):
    ob.data.calc_loop_triangles()
    return BVHTree.FromPolygons(pts if pts is not None else coords(ob,True),[tuple(f.vertices) for f in ob.data.loop_triangles],all_triangles=True)
def bounds(points):return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
expected={'COOLING_CoverFrame','COOLING_FrontGlass','COOLING_LeftGlass','COOLING_RightGlass'}
check('Four additive model units',set(p['name'] for p in manifest['parts'])==expected,sorted(expected))
for entry in manifest['parts']:
    name=entry['name'];ob=bpy.data.objects[name+'_EXPORT']
    check(name+' finite geometry and UVs',all(math.isfinite(c) for vv in ob.data.vertices for c in vv.co) and ob.data.uv_layers.active is not None and len(ob.data.uv_layers.active.data)==len(ob.data.loops),len(ob.data.vertices))
    bm=bmesh.new();bm.from_mesh(ob.data)
    bad=sum(1 for e in bm.edges if not e.is_manifold);vol=bm.calc_volume(signed=True);bm.free()
    check(name+' closed outward-facing solid',bad==0 and vol>0,dict(non_manifold_edges=bad,signed_volume=vol))
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT/entry['file']))
    imported=set(bpy.data.objects)-before;meshes=[o for o in imported if o.type=='MESH']
    bb=bounds([o.matrix_world@vv.co for o in meshes for vv in o.data.vertices]);orig=bounds([vv.co for vv in ob.data.vertices])
    err=max(abs(x-y) for a,b in zip(bb,orig) for x,y in zip(a,b))
    check(name+' FBX round-trip scale origin and materials',len(imported)==len(meshes)==1 and err<.00005 and meshes[0].matrix_world.translation.length<.00001 and len(meshes[0].data.materials)==len(entry['materials']),dict(bound_error=err,material_count=len(meshes[0].data.materials)))
    check(name+' no animation camera or light exported',all(o.type=='MESH' and o.animation_data is None for o in imported),[o.type for o in imported])
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
check('Original Blender source unchanged',hashlib.sha256(Path(manifest['source_blend']).read_bytes()).hexdigest()==manifest['source_sha256'],manifest['source_blend'])
check('No inherited meter-glass material in new guard exports',all('RLYC_MeterGlass' not in p['materials'] for p in manifest['parts']),'Existing FLOW_Glass and its material remain separate.')
check('Meter glass adjustment preserved in review scene',abs((P@bpy.data.objects['FLOW_Glass'].location).z-.01)<1e-6,list(P@bpy.data.objects['FLOW_Glass'].location))
front=mesh_bvh(bpy.data.objects['COOLING_FrontGlass_EXPORT'])
for hole in manifest['rectangular_openings']:
    hits=0
    for ix in range(9):
        for iy in range(9):
            x=hole['x']+hole['w']*.48*(ix/4-1);y=hole['y']+hole['h']*.48*(iy/4-1)
            hits+=front.ray_cast(Vector((x,y,-1)),Vector((0,0,1)),1)[0] is not None
    check(hole['name']+' opening is an actual empty aperture',hits==0,dict(rays=81,occluded=hits))
hits=0
for i in range(32):
    a=math.tau*i/32
    pos=Vector((.28+.112*math.cos(a),.35+.112*math.sin(a),-1))
    hits+=front.ray_cast(pos,Vector((0,0,1)),1)[0] is not None
check('Valve circular penetration is open',hits==0,dict(rays=32,occluded=hits))
hits=sum(front.ray_cast(Vector((x,y,-1)),Vector((0,0,1)),1)[0] is not None for x,y in [(-.76,-.9),(.72,.7),(0,-.85),(.73,-.7),(-.72,.72)])
check('Glass exists across previously open cabinet areas',hits==5,dict(probes=5,hits=hits))
guard_names=('COOLING_FrontGlass','COOLING_LeftGlass','COOLING_RightGlass')
guards={n:mesh_bvh(bpy.data.objects[n+'_EXPORT']) for n in guard_names}
for old in ('COOLING_Frame','FLOW_Housing','THERMAL_Housing','PUMP_Housing','VALVE_Housing'):
    old_ob=bpy.data.objects[old+'_EXPORT']
    old_bvh=mesh_bvh(old_ob)
    collisions={n:len(b.overlap(old_bvh)) for n,b in guards.items()}
    if any(collisions.values()):
        verts=coords(old_ob,True)
        for gn,guard in guards.items():
            pairs=guard.overlap(old_bvh)
            centers=[sum((verts[i] for i in old_ob.data.loop_triangles[pair[1]].vertices),Vector())/3 for pair in pairs[:12]]
            if centers:print('INTERSECTION',old,gn,[list(c) for c in centers],flush=True)
    check('Glazing does not intersect '+old,not any(collisions.values()),collisions)
motion_guards={**guards,'COOLING_CoverFrame':mesh_bvh(bpy.data.objects['COOLING_CoverFrame_EXPORT'])}
for name,angles in [('PUMP_Handle',range(-25,26)),('VALVE_Wheel',range(0,360,5))]:
    ob=bpy.data.objects[name+'_EXPORT'];base=coords(ob);center=P@ob.matrix_world.translation
    bad=[]
    for angle in angles:
        r=Matrix.Rotation(math.radians(angle),3,'Z')
        moving=mesh_bvh(ob,[r@c+center for c in base])
        if any(b.overlap(moving) for b in motion_guards.values()):bad.append(angle)
    check(name+' full operation clears glazing and hardware',not bad,dict(samples=len(angles),colliding_angles=bad))
check('Additive geometry budget',manifest['triangles_total']<20000,manifest['triangles_total'])
report=dict(all_checks_passed=all(c['passed'] for c in checks),check_count=len(checks),checks=checks,unity_modified=False,runtime_limit='Unity transparency, lighting and clicks require user Play-mode verification.')
(OUT/'checks'/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=report['all_checks_passed'],count=len(checks),failures=[c['name'] for c in checks if not c['passed']])),flush=True)
if not report['all_checks_passed']:raise SystemExit(1)
