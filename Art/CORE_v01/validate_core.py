"""Independent CORE export verification; reads Unity files and never launches Unity.

Run using Blender --background --factory-startup --python validate_core.py.
Loads the saved Blender artifact and actually re-imports every exported FBX.
Writes only CORE_v01/checks/validation.json. Does not save the loaded .blend.
"""
import bpy
import hashlib
import json
import math
import os
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__))
P = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
TOL = 0.00005
with open(os.path.join(OUT, 'checks', 'scene_reference.json'), encoding='utf-8') as f:
    reference = json.load(f)
with open(os.path.join(OUT, 'manifest.json'), encoding='utf-8') as f:
    manifest = json.load(f)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'RELAY_CORE_v01.blend'))

report = {
    'method': 'Saved Blender baked meshes, actual FBX round trip, measured Unity mounts, mesh BVH rays.',
    'unity_opened_or_modified': False,
    'checks': [],
    'manual_runtime_check': 'Unity import, render order, material remapping, lighting, first-person interaction and startup gameplay remain for the user.',
}


def check(name, passed, details):
    report['checks'].append({'name': name, 'passed': bool(passed), 'details': details})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)


def bounds(points):
    return [[min(p[a] for p in points), max(p[a] for p in points)] for a in range(3)]


def bound_error(a, b):
    return max(abs(x - y) for aa, bb in zip(a, b) for x, y in zip(aa, bb))


def finite_points(points):
    return all(math.isfinite(c) for p in points for c in p)


def unit_scale(ob):
    return max(abs(c - 1) for c in ob.matrix_world.to_scale()) < TOL


EXPECTED = {
    'CORE_Cabinet', 'START_Housing', 'START_Handle', 'STARTUP_GaugeHousing',
    'HEAT_Housing', 'COLD_Housing', 'STARTUP_Housing',
    'CORE_Containment', 'CORE_Glass', 'CORE_Emitter', 'CORE_Guardrail',
}
REACTOR = {'CORE_Containment', 'CORE_Glass', 'CORE_Emitter', 'CORE_Guardrail'}
entries = {part['name']: part for part in manifest['parts']}
check('Exactly eleven expected model exports', set(entries) == EXPECTED, sorted(entries))
approved_materials = {m['name'] for m in manifest['materials']}
meshes = {}
total_triangles = 0

for name, entry in entries.items():
    ob = bpy.data.objects.get(name + '_EXPORT')
    check(name + ' baked mesh exists', ob is not None and ob.type == 'MESH', {'object': name + '_EXPORT'})
    if ob is None or ob.type != 'MESH':
        continue
    meshes[name] = ob
    local_vertices = [v.co.copy() for v in ob.data.vertices]
    triangles = sum(max(0, len(p.vertices) - 2) for p in ob.data.polygons)
    total_triangles += triangles
    check(name + ' nonempty finite geometry and unit source scale',
          len(local_vertices) > 0 and triangles > 0 and finite_points(local_vertices) and unit_scale(ob),
          {'vertices': len(local_vertices), 'triangles': triangles, 'scale': list(ob.matrix_world.to_scale())})
    if not local_vertices:
        continue
    uv = ob.data.uv_layers.active
    check(name + ' complete finite UV mapping',
          uv is not None and len(uv.data) == len(ob.data.loops)
          and all(math.isfinite(c) for d in uv.data for c in d.uv),
          {'loops': len(ob.data.loops), 'uv_layers': len(ob.data.uv_layers)})
    used = {m.name for m in ob.data.materials if m}
    check(name + ' runtime materials and no preview content',
          used.issubset(approved_materials) and all('PREVIEW' not in m.upper() for m in used)
          and ob.animation_data is None,
          sorted(used))
    unity_bounds = bounds([P @ p for p in local_vertices])
    check(name + ' manifest dimensions match stored mesh',
          bound_error(unity_bounds, entry['bounds_unity_local']) < TOL,
          {'actual': unity_bounds, 'manifest': entry['bounds_unity_local']})
    file_path = os.path.abspath(os.path.join(OUT, entry['file']))
    check(name + ' FBX path remains within art output folder',
          os.path.commonpath([OUT, file_path]) == OUT and file_path.lower().endswith('.fbx'), file_path)
    if not os.path.isfile(file_path):
        check(name + ' FBX exists', False, file_path)
        continue
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=file_path)
        imported = set(bpy.data.objects) - before
        imported_meshes = [o for o in imported if o.type == 'MESH']
        coords = [o.matrix_world @ v.co for o in imported_meshes for v in o.data.vertices]
        valid = len(imported_meshes) == 1 and len(imported) == 1 and bool(coords) and finite_points(coords)
        error = bound_error(bounds(local_vertices), bounds(coords)) if valid else None
        check(name + ' actual FBX round-trip bounds and identity transform',
              valid and error < TOL
              and imported_meshes[0].matrix_world.translation.length < TOL
              and unit_scale(imported_meshes[0]),
              {'mesh_count': len(imported_meshes), 'object_count': len(imported),
               'max_bound_error_m': error,
               'scales': [list(o.matrix_world.to_scale()) for o in imported_meshes]})
        check(name + ' reimport contains no animation camera light or preview material',
              all(o.animation_data is None and o.type == 'MESH' for o in imported)
              and all('PREVIEW' not in m.name.upper() for o in imported_meshes for m in o.data.materials if m),
              [o.name for o in imported])
    except Exception as ex:
        check(name + ' actual FBX round trip', False, repr(ex))
    finally:
        for imported_ob in set(bpy.data.objects) - before:
            bpy.data.objects.remove(imported_ob, do_unlink=True)

budget = manifest.get('triangle_budget', 180000)
check('Combined model geometry budget', total_triangles <= budget,
      {'triangles': total_triangles, 'budget': budget, 'note': 'Mesh complexity check, not a runtime performance measurement.'})

# Positions come from the independently inspected saved Unity scene, not the builder.
def add(a, b):
    return [x + y for x, y in zip(a, b)]


mount_positions = {
    'CORE_Cabinet': [0, 0, 0],
    'START_Housing': reference['start_lever']['position'],
    'START_Handle': add(reference['start_lever']['position'], reference['start_lever']['handle_pivot']['position']),
    'STARTUP_GaugeHousing': reference['startup_gauge']['position'],
    'HEAT_Housing': reference['indicators']['heat']['position'],
    'COLD_Housing': reference['indicators']['cold']['position'],
    'STARTUP_Housing': reference['indicators']['startup']['position'],
}
mount_parent_suffix = {
    'CORE_Cabinet': 'Environment/CORE_Module',
    'START_Housing': 'Environment/CORE_Module/START_Lever',
    'START_Handle': 'Environment/CORE_Module/START_Lever/HandlePivot',
    'STARTUP_GaugeHousing': 'Environment/CORE_Module/Startup_Gauge',
    'HEAT_Housing': 'Environment/CORE_Module/HEAT_Indicator',
    'COLD_Housing': 'Environment/CORE_Module/COLD_Indicator',
    'STARTUP_Housing': 'Environment/CORE_Module/STARTUP_Indicator',
}
for name, entry in entries.items():
    if name not in EXPECTED:
        continue
    position = entry.get('model_child_local_position')
    rotation = entry.get('model_child_local_rotation')
    scale = entry.get('model_child_local_scale')
    expected_scale = [1 / 3, 1 / 3.5, 1 / 3] if name in REACTOR else [1, 1, 1]
    parent = 'Environment/Core_Block' if name in REACTOR else mount_parent_suffix[name]
    check(name + ' attachment preserves old transform and collider scale',
          position == [0, 0, 0] and rotation == [0, 180, 0]
          and scale is not None and max(abs(a - b) for a, b in zip(scale, expected_scale)) < 0.000001
          and entry.get('unity_parent') == parent,
          {'parent': entry.get('unity_parent'), 'position': position, 'rotation': rotation, 'scale': scale})

# Shared centre pivot restores physical metres beneath Core_Block's nonuniform scale.
reactor_vertices = [P @ v.co for name in REACTOR if name in meshes for v in meshes[name].data.vertices]
if reactor_vertices:
    reactor_bounds = bounds(reactor_vertices)
    limit = [[-1.5, 1.5], [-1.75, 1.75], [-1.5, 1.5]]
    excess = max(max(lo - b[0], b[1] - hi) for b, (lo, hi) in zip(reactor_bounds, limit))
    world = [[b[0] + c, b[1] + c] for b, c in zip(reactor_bounds, reference['reactor_placeholder']['position'])]
    check('Assembled reactor fits original Core_Block collision envelope',
          len(REACTOR.intersection(meshes)) == len(REACTOR) and excess < TOL,
          {'local_bounds': reactor_bounds, 'world_bounds': world, 'maximum_excess_m': excess,
           'note': 'Includes glass, emitter, guardrail and containment, not only main shell.'})

# BVHs of saved baked meshes reconstructed at audited attachment positions.
# Separate display emitters and the old dynamic Unity parts are intentionally absent.
fixed_bvhs = {}
for name, position in mount_positions.items():
    if name == 'START_Handle' or name not in meshes:
        continue
    ob = meshes[name]
    vertices = [P @ v.co + Vector(position) for v in ob.data.vertices]
    faces = [tuple(p.vertices) for p in ob.data.polygons]
    fixed_bvhs[name] = BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def grid_clear(label, xr, yr, z, nx, ny):
    hits = []
    for ix in range(nx):
        x = xr[0] + (xr[1] - xr[0]) * ix / (nx - 1)
        for iy in range(ny):
            y = yr[0] + (yr[1] - yr[0]) * iy / (ny - 1)
            origin = Vector((x, y, -2))
            for name, bvh in fixed_bvhs.items():
                hit, normal, index, distance = bvh.ray_cast(origin, Vector((0, 0, 1)), z + 2 - 0.0001)
                if hit is not None:
                    hits.append({'sample': [x, y], 'part': name, 'occluder_z': hit.z})
    check(label, not hits,
          {'rays': nx * ny, 'opaque_parts_checked': sorted(fixed_bvhs), 'occlusion_count': len(hits), 'examples': hits[:12]})


gauge = reference['startup_gauge']
gx, gy, gz = gauge['position']
grid_clear('Full startup progress fill remains visible through all fixed new control meshes',
           (gx - .4995, gx + .4995), (gy - .037, gy + .037), gz - .086, 61, 11)
grid_clear('Unfilled startup gauge track remains visible through all fixed new control meshes',
           (gx - .4995, gx + .4995), (gy - .049, gy + .049), gz - .072, 61, 15)

for key in ('startup', 'heat', 'cold'):
    lamp = reference['indicators'][key]
    x, y, z = lamp['position']
    grid_clear(key + ' original unlit lens remains visible',
               (x - .0695, x + .0695), (y - .007, y + .057), z - .078, 21, 11)
    grid_clear(key + ' original script-controlled lit lens remains visible',
               (x - .0595, x + .0595), (y + .0005, y + .0495), z - .083, 21, 11)

status = reference['text']['status']
sx, sy = status['anchored_position']
sw, sh = status['effective_dimensions']
grid_clear('Retained dynamic startup status text rectangle is not covered by new cabinet parts',
           (sx - sw / 2 + .001, sx + sw / 2 - .001),
           (sy - sh / 2 + .001, sy + sh / 2 - .001), status['local_z'], 61, 17)

# Independent audit-start hashes; reading only, no source or import manipulation.
project = 'C:/Users/gonut/School_p2'
audit_hashes = {
    reference['source_scene']: reference['scene_sha256'],
    project + '/Assets/_STARTUP/Scripts/CoreModule.cs': '418AB68966DAAD25382E1AF3C151B69ABF7852396907F154321677860C570BC0',
    project + '/Assets/_STARTUP/Scripts/CorePanelDisplay.cs': '0E280795D3DD68134F248E5F7B79F8C6B4E4B293FB201AEA44E9335C842268AF',
    project + '/Assets/_STARTUP/Scripts/CoreStartLever.cs': '718845880F60FDDAC7D72E638800AE59A9C83AC6CD3419335B65EF5A3DAC6ECD',
    project + '/Assets/_STARTUP/Scripts/MachineSwitch.cs': '0D36625BAFBEEBD44F0CC2A0658D5914D10D873A689D63B5F691303848889607',
}
for source_path, expected_hash in audit_hashes.items():
    if not os.path.isfile(source_path):
        check('Audited Unity source still available: ' + os.path.basename(source_path), False, source_path)
        continue
    with open(source_path, 'rb') as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
    check('Unity source unchanged since audit: ' + os.path.basename(source_path), actual_hash == expected_hash,
          {'path': source_path, 'sha256': actual_hash,
           'note': 'A mismatch could be a user edit; this validator never changes source files.'})

baseline_path = os.path.join(OUT, 'checks', 'authoring_baseline.json')
if os.path.isfile(baseline_path):
    with open(baseline_path, encoding='utf-8-sig') as f:
        baseline = json.load(f)
    changed = []
    for source_path, expected_hash in baseline.items():
        if not os.path.isfile(source_path):
            changed.append({'path': source_path, 'reason': 'missing'})
            continue
        with open(source_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        if actual_hash.lower() != expected_hash.lower():
            changed.append({'path': source_path, 'reason': 'hash changed'})
    check('Full fresh authoring baseline unchanged', not changed,
          {'files_compared': len(baseline), 'changed': changed,
           'scope': 'Only the scene, scripts, script metadata and project settings listed in the fresh baseline.'})

report['all_checks_passed'] = all(c['passed'] for c in report['checks'])
report['check_count'] = len(report['checks'])
report['total_triangles'] = total_triangles
report['failures'] = [c['name'] for c in report['checks'] if not c['passed']]
os.makedirs(os.path.join(OUT, 'checks'), exist_ok=True)
with open(os.path.join(OUT, 'checks', 'validation.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)
print(json.dumps({k: report[k] for k in ('all_checks_passed', 'check_count', 'total_triangles', 'failures')}, indent=2), flush=True)
