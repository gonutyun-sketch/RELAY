"""Read-only FBX validation; writes only checks/validation.json."""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
SCENE = Path('C:/Users/gonut/School_p2/Assets/Scenes/Startup_Graybox.unity')
TOL = 0.0001


def close_vec(a, b):
    return all(abs(x - y) <= TOL for x, y in zip(a, b))


def to_unity(world):
    # Source maps Unity (X,Y,Z) to Blender (X,Z,Y). Imported FBX world
    # geometry includes the importer's +90-degree X object rotation.
    return [world.x, world.z, world.y]


def image_path(image):
    return Path(bpy.path.abspath(image.filepath)).resolve()


report = {
    'method': 'Independent fresh Blender FBX imports; no Unity or model edits, no render.',
    'blender_version': bpy.app.version_string,
    'tolerance_metres': TOL,
    'parts': [],
}

for advertised in MANIFEST['parts']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    filepath = ROOT / 'exports' / (advertised['name'] + '.fbx')
    result = {'name': advertised['name'], 'file': str(filepath), 'checks': {}}
    checks = result['checks']
    checks['fbx_exists'] = filepath.is_file()
    try:
        bpy.ops.import_scene.fbx(filepath=str(filepath))
        objects = list(bpy.context.scene.objects)
        meshes = [o for o in objects if o.type == 'MESH']
        result['object_types'] = [o.type for o in objects]
        checks['one_mesh'] = len(meshes) == 1
        checks['no_lights_or_cameras'] = not any(o.type in {'LIGHT', 'CAMERA'} for o in objects)
        checks['no_animation'] = len(bpy.data.actions) == 0 and all(o.animation_data is None for o in objects)
        if len(meshes) != 1:
            raise ValueError(f'Expected one mesh, found {len(meshes)}')
        obj = meshes[0]
        mesh = obj.data
        points = [to_unity(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
        checks['finite_positions'] = bool(points) and all(math.isfinite(v) for p in points for v in p)
        lo = [min(p[i] for p in points) for i in range(3)]
        hi = [max(p[i] for p in points) for i in range(3)]
        result['unity_min'] = lo
        result['unity_max'] = hi
        result['unity_size'] = [b - a for a, b in zip(lo, hi)]
        result['pivot_world'] = list(obj.matrix_world.translation)
        checks['pivot_at_zero'] = close_vec(result['pivot_world'], [0, 0, 0])
        checks['bounds_match_manifest'] = close_vec(lo, advertised['unity_min']) and close_vec(hi, advertised['unity_max'])
        mesh.calc_loop_triangles()
        result['triangles'] = len(mesh.loop_triangles)
        checks['triangles_match_manifest'] = result['triangles'] == advertised['triangles']
        result['uv_layers'] = len(mesh.uv_layers)
        checks['uv_present_and_finite'] = len(mesh.uv_layers) >= 1 and all(
            len(layer.data) == len(mesh.loops) and all(math.isfinite(c) for datum in layer.data for c in datum.uv)
            for layer in mesh.uv_layers)
        slots = [slot.material.name if slot.material else None for slot in obj.material_slots]
        assigned = sorted({face.material_index for face in mesh.polygons})
        result['materials'] = slots
        result['assigned_material_indices'] = assigned
        checks['material_names_match_manifest'] = slots == advertised['materials']
        checks['assigned_indices_cover_all_slots'] = assigned == list(range(len(slots)))
        checks['assigned_indices_match_manifest'] = assigned == advertised['used_material_indices']
        result['base_color_images'] = []
        image_names_with_links = set()
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type != 'BSDF_PRINCIPLED':
                    continue
                for link in node.inputs['Base Color'].links:
                    source = link.from_node
                    if source.type == 'TEX_IMAGE' and source.image:
                        path = image_path(source.image)
                        result['base_color_images'].append({
                            'material': mat.name,
                            'image': source.image.name,
                            'path': str(path),
                            'exists': path.is_file(),
                        })
                        image_names_with_links.add(mat.name)
        expected_textured = set(slots).intersection({'RLYE_Iron', 'RLYE_Timber'})
        checks['expected_base_color_textures_connected'] = expected_textured.issubset(image_names_with_links)
        checks['base_color_texture_paths_exist'] = bool(result['base_color_images']) and all(x['exists'] for x in result['base_color_images'])
        if advertised['name'] in {'ELEVATOR_DoorLeft', 'ELEVATOR_DoorRight'}:
            half_box = [0.6, 1.5, 0.08]
            checks['door_within_existing_panel_box'] = all(lo[i] >= -half_box[i] - TOL and hi[i] <= half_box[i] + TOL for i in range(3))
    except Exception as error:
        result['error'] = repr(error)
        checks['import_and_validation_completed'] = False
    else:
        checks['import_and_validation_completed'] = True
    result['passed'] = all(checks.values())
    report['parts'].append(result)

parts = {part['name']: part for part in report['parts']}
layout = {}
try:
    left = parts['ELEVATOR_DoorLeft']
    right = parts['ELEVATOR_DoorRight']
    track = parts['ELEVATOR_DoorTrack']
    closed_left_edge = -0.6 + left['unity_max'][0]
    closed_right_edge = 0.6 + right['unity_min'][0]
    open_left_edge = -1.85 + left['unity_min'][0]
    open_right_edge = 1.85 + right['unity_max'][0]
    layout['closed_seam_x'] = [closed_left_edge, closed_right_edge]
    layout['open_outer_x'] = [open_left_edge, open_right_edge]
    layout['track_outer_x'] = [track['unity_min'][0], track['unity_max'][0]]
    layout['checks'] = {
        'closed_doors_meet_at_x_zero': abs(closed_left_edge) <= TOL and abs(closed_right_edge) <= TOL,
        'open_door_extent_matches_2_45': abs(open_left_edge + 2.45) <= TOL and abs(open_right_edge - 2.45) <= TOL,
        'track_extent_matches_2_53': abs(track['unity_min'][0] + 2.53) <= TOL and abs(track['unity_max'][0] - 2.53) <= TOL,
        'open_doors_fit_track_span': open_left_edge >= track['unity_min'][0] - TOL and open_right_edge <= track['unity_max'][0] + TOL,
    }
except Exception as error:
    layout['error'] = repr(error)
    layout['checks'] = {'layout_validation_completed': False}
layout['passed'] = all(layout['checks'].values())
report['door_layout'] = layout

scene_hash = hashlib.sha256(SCENE.read_bytes()).hexdigest()
report['unity_scene'] = {
    'file': str(SCENE),
    'sha256_current': scene_hash,
    'sha256_build_before': MANIFEST['unity_scene_sha256_before'],
    'sha256_build_after': MANIFEST['unity_scene_sha256_after'],
    'unchanged': scene_hash == MANIFEST['unity_scene_sha256_before'] == MANIFEST['unity_scene_sha256_after'],
}
report['total_triangles'] = sum(p.get('triangles', 0) for p in report['parts'])
report['all_passed'] = all(p['passed'] for p in report['parts']) and layout['passed'] and report['unity_scene']['unchanged']
target = ROOT / 'checks' / 'validation.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'validation': str(target), 'all_passed': report['all_passed'], 'parts': [{ 'name': p['name'], 'passed': p['passed'], 'failed_checks': [k for k, v in p['checks'].items() if not v]} for p in report['parts']], 'door_layout_passed': layout['passed'], 'unity_scene_unchanged': report['unity_scene']['unchanged']}, ensure_ascii=False))
