"""Independent saved-scene/mesh validation. Never opens or writes Unity."""
import bpy, os, json, math
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__))
P = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'RELAY_SIGNAL_v01.blend'))
with open(os.path.join(OUT, 'manifest.json'), encoding='utf-8') as f:
    manifest = json.load(f)
with open(os.path.join(OUT, 'checks', 'scene_reference.json'), encoding='utf-8') as f:
    reference = json.load(f)
report = {'unity_opened_or_modified': False, 'checks': [],
          'manual_runtime_check': 'Unity import, lighting and interaction remain for the user.'}

def check(name, passed, detail):
    report['checks'].append({'name': name, 'passed': bool(passed), 'details': detail})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)

def bounds(points):
    return [[min(p[a] for p in points), max(p[a] for p in points)] for a in range(3)]

def bounds_error(a, b):
    return max(abs(x-y) for ax, bx in zip(a, b) for x, y in zip(ax, bx))

def unity_vertices(ob):
    return [P @ v.co for v in ob.data.vertices]

def mesh_bvh(ob, translation=(0,0,0)):
    t = Vector(translation)
    vertices = [P @ v.co + t for v in ob.data.vertices]
    faces = [tuple(p.vertices) for p in ob.data.polygons]
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False), vertices

expected_names = {'SIGNAL_Cabinet', 'SCOPE_Housing', 'FREQUENCY_Housing',
                  'FREQUENCY_Knob', 'PHASE_Housing', 'PHASE_Handle',
                  'GAIN_Housing', 'GAIN_Handle', 'LOCK_Housing'}
entries = {p['name']: p for p in manifest['parts']}
check('Exactly nine separate expected exported units', set(entries) == expected_names,
      sorted(entries))
expected_materials = {m['name'] for m in manifest['materials']}
total_triangles = 0
for name, entry in entries.items():
    ob = bpy.data.objects[name + '_EXPORT']
    neutral_bounds = bounds([v.co for v in ob.data.vertices])
    check(name + ' neutral mesh origin and finite vertices',
          ob.type == 'MESH' and all(math.isfinite(c) for v in ob.data.vertices for c in v.co),
          {'vertices': len(ob.data.vertices)})
    uv = ob.data.uv_layers.active
    check(name + ' complete finite UV coordinates',
          uv is not None and len(uv.data) == len(ob.data.loops)
          and all(math.isfinite(c) for d in uv.data for c in d.uv),
          {'uv_layers': len(ob.data.uv_layers), 'mesh_loops': len(ob.data.loops)})
    used = {m.name for m in ob.data.materials if m is not None}
    check(name + ' export has only approved runtime materials',
          used.issubset(expected_materials) and all('PREVIEW' not in m for m in used),
          sorted(used))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, entry['file']))
    imported = set(bpy.data.objects) - before
    meshes = [o for o in imported if o.type == 'MESH']
    coords = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    err = bounds_error(neutral_bounds, bounds(coords))
    check(name + ' actual FBX round-trip dimensions and neutral object',
          len(meshes) == 1 and len(imported) == 1 and err < 0.00005
          and meshes[0].matrix_world.translation.length < 0.00001,
          {'mesh_count': len(meshes), 'objects': len(imported),
           'maximum_axis_bound_error_m': err,
           'imported_origin': list(meshes[0].matrix_world.translation)})
    check(name + ' FBX mesh has no animation or preview assets',
          all(o.animation_data is None for o in imported)
          and all('PREVIEW' not in o.name for o in imported)
          and all('PREVIEW' not in m.name for o in meshes for m in o.data.materials if m),
          [o.name for o in imported])
    total_triangles += sum(len(p.vertices)-2 for p in ob.data.polygons)
    for o in imported:
        bpy.data.objects.remove(o, do_unlink=True)
check('Total triangle count is appropriate for one environment prop',
      total_triangles < 90000, {'triangles': total_triangles, 'budget': 90000})

# Check actual stored export origins against independently measured saved Unity mounts.
def add(a,b): return [x+y for x,y in zip(a,b)]
root_pos = {
    'SIGNAL_Cabinet': [0,0,0], 'SCOPE_Housing': reference['scope']['position'],
    'FREQUENCY_Housing': reference['frequency']['position'],
    'FREQUENCY_Knob': add(reference['frequency']['position'], reference['frequency']['moving_part']['position']),
    'PHASE_Housing': reference['phase']['position'],
    'PHASE_Handle': add(reference['phase']['position'], reference['phase']['moving_part']['position']),
    'GAIN_Housing': reference['gain']['position'],
    'GAIN_Handle': add(reference['gain']['position'], reference['gain']['moving_part']['position']),
    'LOCK_Housing': reference['lock_indicator']['position']}
for name, expected in root_pos.items():
    actual = P @ bpy.data.objects[name+'_EXPORT'].matrix_world.translation
    delta = (actual - Vector(expected)).length
    check(name+' authoring pivot matches saved Unity mount', delta < 0.00002,
          {'expected': expected, 'actual': list(actual), 'error_m': delta})

# Validate handle shape and actual export child scales against original scaled pick boxes.
for key, name in [('phase','PHASE_Handle'), ('gain','GAIN_Handle')]:
    ob = bpy.data.objects[name+'_EXPORT']
    vertices = unity_vertices(ob)
    parent_scale = reference[key]['moving_part']['scale']
    child_scale = entries[name]['model_child_local_scale']
    cancel_error = max(abs(a*b-1) for a,b in zip(parent_scale,child_scale))
    dims = parent_scale
    overshoot = [max(abs(p[i]) - dims[i]/2 for p in vertices) for i in range(3)]
    # Grip markings project two millimetres beyond the former cube's front face;
    # their XY footprint must remain inside the raycast footprint exactly.
    check(name+' parent scale cancellation and original collider footprint',
          cancel_error < 1e-6 and overshoot[0] < 0.0002 and overshoot[1] < 0.0002
          and overshoot[2] <= 0.0021,
          {'scale_cancellation_error': cancel_error, 'axis_overshoot_m': overshoot,
           'note': 'Up to 2mm front surface relief is permitted, keeping the original XY hit area.'})
    fixed = bpy.data.objects[key.upper()+'_Housing_EXPORT']
    fixed_bvh, _ = mesh_bvh(fixed)
    start = Vector(reference[key]['minimum_position'])
    end = Vector(reference[key]['maximum_position'])
    hits = []
    for i in range(101):
        t = i/100
        moving_bvh, _ = mesh_bvh(ob, start.lerp(end,t))
        overlaps = fixed_bvh.overlap(moving_bvh)
        if overlaps:
            hits.append({'travel_fraction': t, 'intersecting_face_pairs': len(overlaps)})
    check(name+' complete travel has no fixed housing surface intersection',
          not hits, {'samples':101, 'collision_samples':len(hits), 'first_samples':hits[:8],
                     'last_samples': hits[-3:],
                     'note':'Actual evaluated export mesh BVH surface intersections, including touching surfaces.'})

# Ray tests use actual baked geometry, not nominal dimensions from the builder.
def occlusion_grid(name, xr, yr, target_z, nx, ny, label):
    bvh, _ = mesh_bvh(bpy.data.objects[name+'_EXPORT'])
    hits = []
    for ix in range(nx):
        x=xr[0]+(xr[1]-xr[0])*ix/(nx-1)
        for iy in range(ny):
            y=yr[0]+(yr[1]-yr[0])*iy/(ny-1)
            hit, normal, face, distance = bvh.ray_cast(Vector((x,y,-1)),Vector((0,0,1)), 1+target_z-0.0001)
            if hit is not None:
                hits.append({'point':[x,y], 'occluder_z':hit.z})
    check(label, not hits, {'rays':nx*ny, 'occluded':len(hits), 'examples':hits[:8]})

occlusion_grid('SCOPE_Housing', (-.598,.598),(-.254,.254),-.11,61,31,
               'Live waveform footprint is clear of new opaque scope geometry')
occlusion_grid('LOCK_Housing', (-.0695,.0695),(-.007,.057),-.078,31,15,
               'Existing unlit lens remains visible through new lock housing')
occlusion_grid('LOCK_Housing', (-.0595,.0595),(0.0005,.0495),-.083,31,15,
               'Existing controlled lit lens remains visible through new lock housing')

report['all_checks_passed'] = all(c['passed'] for c in report['checks'])
report['check_count'] = len(report['checks'])
report['failures'] = [c['name'] for c in report['checks'] if not c['passed']]
os.makedirs(os.path.join(OUT,'checks'),exist_ok=True)
with open(os.path.join(OUT,'checks','validation.json'),'w',encoding='utf-8') as f:
    json.dump(report,f,indent=2)
print(json.dumps({'all_checks_passed':report['all_checks_passed'],
                  'count':report['check_count'],'failures':report['failures']},indent=2),flush=True)
