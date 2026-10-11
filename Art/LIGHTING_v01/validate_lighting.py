"""Independent read-only LIGHTING artifact and FBX round-trip verification.

Run in Blender background mode with --factory-startup --disable-autoexec.
Writes only checks/validation.json; never saves the loaded blend or touches Unity.
"""
import bpy
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Matrix, Vector


OUT = Path(__file__).resolve().parent
PROJECT = Path('C:/Users/gonut/School_p2')
P = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
EXPECTED_FBX_IMPORT_MATRIX = Matrix.Rotation(math.pi / 2, 4, 'X')
TOL = 0.00005
EXPECTED = {
    'LIGHT_LinearHousing', 'LIGHT_LinearLens', 'LIGHT_LinearGlass',
    'LIGHT_BulkheadHousing', 'LIGHT_BulkheadLens', 'LIGHT_BulkheadGlass',
}
APPROVED = {'RLYL_Paint', 'RLYL_Frame', 'RLYL_Steel', 'RLYL_Rubber', 'RLYL_Lens', 'RLYL_Glass'}
HOUSING_MATERIALS = {'RLYL_Paint', 'RLYL_Frame', 'RLYL_Steel', 'RLYL_Rubber'}
LIMITS = {
    'Linear': [[-.30, .30], [-.19, 0], [-.90, .90]],
    'Bulkhead': [[-.25, .25], [-.17, 0], [-.42, .42]],
}
reference = json.loads((OUT / 'checks/scene_reference.json').read_text(encoding='utf-8'))
manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
report = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'method': 'Load saved Blender mesh, actual independent FBX imports, compare round-trip geometry/UVs/materials/transforms and audited scene mounts.',
    'unity_opened_or_modified': False,
    'tolerance_m': TOL,
    'checks': [],
    'manual_runtime_checks': [
        'Unity importer material remapping and actual rendering.',
        'User assigns new Lens renderer references for all four fixtures.',
        'OFF, AUX-only, MAIN-on, power-loss and elevator-motion playtest.',
    ],
    'known_scene_issue': 'Existing Fixture_Exit overlaps Beam_Front. Manual root Z=-6.5 clearance correction is recommended, not applied.',
}


def check(name, passed, details):
    report['checks'].append({'name': name, 'passed': bool(passed), 'details': details})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)


def bounds(coords):
    return [[min(p[a] for p in coords), max(p[a] for p in coords)] for a in range(3)]


def max_error(a, b):
    return max(abs(x - y) for aa, bb in zip(a, b) for x, y in zip(aa, bb))


def finite(coords):
    return all(math.isfinite(c) for p in coords for c in p)


def unit_scale(ob):
    return max(abs(c - 1) for c in ob.matrix_world.to_scale()) < TOL


def uv_good(ob):
    uv = ob.data.uv_layers.active
    return (uv is not None and len(uv.data) == len(ob.data.loops)
            and all(math.isfinite(c) for datum in uv.data for c in datum.uv))


def triangles(ob):
    return sum(max(0, len(p.vertices) - 2) for p in ob.data.polygons)


def material_name(mat):
    return re.sub(r'\.\d{3}$', '', mat.name) if mat else None


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def audit_sources(stage):
    for key in ('scene', 'controller'):
        source = reference[key]
        actual = file_hash(source['path'])
        check(stage + ' audited Unity ' + key + ' SHA256 unchanged', actual == source['sha256'],
              {'path': source['path'], 'actual': actual, 'expected': source['sha256']})
    result = subprocess.run(['git', '-C', str(PROJECT), 'status', '--porcelain=v1', '--untracked-files=normal'],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    check(stage + ' Unity repository worktree clean', result.returncode == 0 and not result.stdout.strip(),
          {'returncode': result.returncode, 'status': result.stdout, 'stderr': result.stderr,
           'scope': 'Git-tracked project content and nonignored untracked files; not Unity Library or other ignored generated caches.'})


audit_sources('Before validation')
blend = OUT / 'RELAY_Lighting.blend'
artifact_hashes = {str(blend): file_hash(blend), str(OUT / 'manifest.json'): file_hash(OUT / 'manifest.json')}
for path in sorted((OUT / 'exports').glob('*.fbx')):
    artifact_hashes[str(path)] = file_hash(path)

bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
scene = bpy.context.scene
check('Blender scene uses metric metres', scene.unit_settings.system == 'METRIC'
      and abs(scene.unit_settings.scale_length - 1) < TOL,
      {'system': scene.unit_settings.system, 'scale_length': scene.unit_settings.scale_length})
check('Saved authoring file has no cameras lights or animation',
      all(o.type not in {'CAMERA', 'LIGHT', 'ARMATURE'} and o.animation_data is None for o in bpy.data.objects)
      and len(bpy.data.actions) == 0,
      {'excluded_object_types': [o.name for o in bpy.data.objects if o.type in {'CAMERA', 'LIGHT', 'ARMATURE'}],
       'action_count': len(bpy.data.actions)})

entries = {p['name']: p for p in manifest['parts']}
disk_names = {p.stem for p in (OUT / 'exports').glob('*.fbx')}
check('Exactly six expected manifest entries and FBX files', set(entries) == EXPECTED and disk_names == EXPECTED,
      {'manifest_names': sorted(entries), 'disk_names': sorted(disk_names)})
check('Manifest import offset agrees with audited top mount convention',
      manifest.get('manual_import_local_position') == [0, .05, 0],
      manifest.get('manual_import_local_position'))

parts = {}
total_triangles = 0
for name in sorted(EXPECTED):
    entry = entries.get(name)
    ob = bpy.data.objects.get(name + '_Export')
    check(name + ': saved export mesh exists', ob is not None and ob.type == 'MESH', name + '_Export')
    if entry is None or ob is None or ob.type != 'MESH':
        continue
    source_coords = [v.co.copy() for v in ob.data.vertices]
    local_coords = [P @ p for p in source_coords]
    count = triangles(ob)
    total_triangles += count
    check(name + ': finite nonempty geometry and applied source scale',
          bool(source_coords) and count > 0 and finite(source_coords) and unit_scale(ob),
          {'vertices': len(source_coords), 'triangles': count, 'scale': list(ob.matrix_world.to_scale())})
    if not source_coords:
        continue
    b = bounds(local_coords)
    variant = 'Linear' if 'Linear' in name else 'Bulkhead'
    envelope = LIMITS[variant]
    excessive = max(max(lo - actual[0], actual[1] - hi) for actual, (lo, hi) in zip(b, envelope))
    check(name + ': baked local mesh inside exact design envelope', excessive < TOL,
          {'actual_unity_bounds': b, 'allowed_bounds': envelope, 'maximum_excess_m': excessive})
    stated = [[a, z] for a, z in zip(entry['unity_min'], entry['unity_max'])]
    check(name + ': manifest matches source mesh bounds and counts',
          max_error(b, stated) < TOL and entry['vertices'] == len(source_coords) and entry['triangles'] == count,
          {'bound_error_m': max_error(b, stated), 'triangles': count})
    check(name + ': complete finite source UVs', uv_good(ob),
          {'layers': len(ob.data.uv_layers), 'loops': len(ob.data.loops)})
    materials = [material_name(m) for m in ob.data.materials]
    expected_materials = (['RLYL_Lens'] if name.endswith('Lens') else
                          ['RLYL_Glass'] if name.endswith('Glass') else None)
    good_materials = (materials == expected_materials if expected_materials else
                      set(materials) == HOUSING_MATERIALS and len(materials) == 4)
    check(name + ': expected runtime material slots', good_materials and set(materials).issubset(APPROVED), materials)
    # Baked export roots intentionally stay at the common zero mount origin.
    # Editable Bulkhead source group is offset 0.95m only for authoring display.
    pivot_error = ob.matrix_world.translation.length
    check(name + ': source origin agrees with shared fixture mount',
          pivot_error < TOL and ob.animation_data is None and not ob.modifiers,
          {'pivot_error_m': pivot_error, 'source_origin_blender': list(ob.matrix_world.translation),
           'note': 'All baked export roots and FBX origins are zero; editable source group offset is not an export offset.'})
    parts[name] = {'source_coords': source_coords, 'unity_coords': local_coords, 'bounds': b, 'triangles': count}

    file_path = (OUT / entry['fbx']).resolve()
    check(name + ': export path remains in package', file_path.is_relative_to(OUT) and file_path.suffix.lower() == '.fbx', str(file_path))
    if not file_path.is_file():
        check(name + ': FBX exists', False, str(file_path))
        continue
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=str(file_path), use_anim=True)
        imported = set(bpy.data.objects) - before
        mesh_objects = [obj for obj in imported if obj.type == 'MESH']
        check(name + ': FBX contains exactly one mesh and no helper content',
              len(imported) == 1 and len(mesh_objects) == 1,
              [{'name': obj.name, 'type': obj.type} for obj in imported])
        if len(mesh_objects) != 1:
            continue
        mesh = mesh_objects[0]
        roundtrip = [mesh.matrix_world @ vert.co for vert in mesh.data.vertices]
        err = max_error(bounds(source_coords), bounds(roundtrip)) if roundtrip else math.inf
        unity_roundtrip = [P @ v for v in roundtrip]
        axis_error = max(abs(mesh.matrix_world[row][col] - EXPECTED_FBX_IMPORT_MATRIX[row][col])
                         for row in range(4) for col in range(4))
        check(name + ': actual FBX orientation metre scale and mount origin preserved',
              bool(roundtrip) and finite(roundtrip) and err < TOL
              and mesh.matrix_world.translation.length < TOL and unit_scale(mesh) and axis_error < TOL,
              {'max_bound_error_m': err, 'expected_fbx_axis_matrix_error': axis_error,
               'note': 'Blender FBX reimport uses +90-degree X axis conversion; world-space mesh must match original Blender geometry.',
               'unity_bounds': bounds(unity_roundtrip), 'origin': list(mesh.matrix_world.translation),
               'scale': list(mesh.matrix_world.to_scale()), 'matrix': [list(row) for row in mesh.matrix_world]})
        check(name + ': FBX UVs finite and triangle count preserved', uv_good(mesh) and triangles(mesh) == count,
              {'uv_layers': len(mesh.data.uv_layers), 'triangles': triangles(mesh), 'source_triangles': count})
        roundtrip_materials = [material_name(m) for m in mesh.data.materials]
        check(name + ': FBX material slots preserved and no animation',
              roundtrip_materials == materials and mesh.animation_data is None
              and all(o.type == 'MESH' and o.animation_data is None for o in imported),
              {'materials': roundtrip_materials, 'animation_data': str(mesh.animation_data)})
    except Exception as exc:
        check(name + ': actual FBX import completes', False, repr(exc))
    finally:
        for imported_object in set(bpy.data.objects) - before:
            bpy.data.objects.remove(imported_object, do_unlink=True)

perimeter = bpy.data.objects.get('Cage_perimeter')
ribs = [o for o in bpy.data.objects if o.name.startswith('Cage_transverse_rib') and o.type == 'CURVE']
if perimeter is not None and perimeter.type == 'CURVE' and len(ribs) == 5:
    perimeter_points = [perimeter.matrix_world @ Vector(p.co[:3])
                        for p in perimeter.data.splines[0].points]
    def point_segment_distance(point, start, end):
        delta = end - start
        t = min(1, max(0, (point - start).dot(delta) / delta.length_squared))
        return (point - (start + t * delta)).length
    endpoint_distances = []
    for rib in ribs:
        points = rib.data.splines[0].points
        for index in (0, len(points) - 1):
            point = rib.matrix_world @ Vector(points[index].co[:3])
            distance = min(point_segment_distance(point, p, perimeter_points[(i + 1) % len(perimeter_points)])
                           for i, p in enumerate(perimeter_points))
            endpoint_distances.append({'rib': rib.name, 'end': index, 'distance_m': distance})
    check('All five transverse cage ribs meet the rounded perimeter',
          max(d['distance_m'] for d in endpoint_distances) < .003,
          {'endpoint_count': len(endpoint_distances), 'tolerance_m': .003,
           'details': endpoint_distances})
else:
    check('Cage source geometry available for continuity check', False,
          {'perimeter_exists': perimeter is not None, 'rib_count': len(ribs)})

for variant in ('Linear', 'Bulkhead'):
    names = ['LIGHT_' + variant + suffix for suffix in ('Housing', 'Lens', 'Glass')]
    if not all(n in parts for n in names):
        check(variant + ': assembled parts available', False, names)
        continue
    coords = [coord for n in names for coord in parts[n]['unity_coords']]
    b = bounds(coords)
    check(variant + ': combined model reaches ceiling mount plane without exceeding it', abs(b[1][1]) < TOL,
          {'combined_bounds': b, 'top_y': b[1][1]})
    local_bottom = b[1][0] + .05
    check(variant + ': preserved Light origin lies below entire imported assembly', local_bottom > -.16 + TOL,
          {'assembly_bottom_relative_to_fixture_y': local_bottom, 'light_y': -.16,
           'light_below_entire_assembly_m': local_bottom + .16})
    lens_b = parts['LIGHT_' + variant + 'Lens']['bounds']
    glass_b = parts['LIGHT_' + variant + 'Glass']['bounds']
    check(variant + ': clear cover lies ahead of downward lens face', glass_b[1][0] < lens_b[1][0]
          and glass_b[0][0] <= lens_b[0][0] and glass_b[0][1] >= lens_b[0][1]
          and glass_b[2][0] <= lens_b[2][0] and glass_b[2][1] >= lens_b[2][1],
          {'lens_bounds': lens_b, 'glass_bounds': glass_b})

linear = bounds([coord for n in parts if 'Linear' in n for coord in parts[n]['unity_coords']])
bulkhead = bounds([coord for n in parts if 'Bulkhead' in n for coord in parts[n]['unity_coords']])
exit_furthest_z = -6.5 + linear[2][1]
check('Recommended Exit root position clears front structural beam', exit_furthest_z < -5.325,
      {'recommended_root_z': -6.5, 'actual_model_end_z': exit_furthest_z,
       'beam_near_z': -5.325, 'gap_m': -5.325 - exit_furthest_z, 'applied_to_unity': False})
check('Compact cabin fixture fits cabin roof and rear wall clearance',
      bulkhead[0][0] > -1.2 and bulkhead[0][1] < 1.2 and -1.7 + bulkhead[2][0] > -2.75
      and -1.7 + bulkhead[2][1] < -.45,
      {'width_bounds': bulkhead[0], 'cabin_z_bounds': [-1.7 + z for z in bulkhead[2]],
       'rear_wall_gap_m': -1.7 + bulkhead[2][0] + 2.75})
check('Aggregate geometry count agrees with manifest and bounded fixture budget',
      total_triangles == manifest['total_triangles'] and total_triangles <= 60000,
      {'total_triangles': total_triangles, 'manifest_total': manifest['total_triangles'],
       'audit_budget': 60000, 'note': 'Geometry check only; not a Unity runtime performance measurement.'})

for path, before_hash in artifact_hashes.items():
    after_hash = file_hash(path)
    check('Input artifact unchanged during validation: ' + Path(path).name, before_hash == after_hash,
          {'sha256': after_hash})
audit_sources('After validation')
report['total_triangles'] = total_triangles
report['check_count'] = len(report['checks'])
report['failures'] = [c['name'] for c in report['checks'] if not c['passed']]
report['all_checks_passed'] = not report['failures']
(OUT / 'checks/validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({key: report[key] for key in ('all_checks_passed', 'check_count', 'total_triangles', 'failures')}, indent=2), flush=True)
