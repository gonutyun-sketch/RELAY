"""Independent art-only FBX audit; run with Blender --background --python.

Reads raw binary FBX and manifest data. Does not import into or change Unity.
Arrays are checked in NumPy batches to keep a multi-million-triangle audit fast.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from io_scene_fbx import parse_fbx
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'checks'
FILES = [
    'FOREST_Terrain.fbx', 'FOREST_Rockwork.fbx', 'FOREST_Undergrowth.fbx',
    'FOREST_Trees_Near.fbx', 'FOREST_Trees_Mid.fbx', 'FOREST_Trees_Far.fbx',
    'FOREST_Ridges.fbx',
]


def child(element, key):
    return next((e for e in element.elems if e.id == key), None) if element else None


def arr(element, key, dtype=None):
    value = child(element, key)
    return np.asarray(value.props[0], dtype=dtype) if value and value.props else np.asarray([], dtype=dtype)


def scalar(element, key):
    value = child(element, key)
    return value.props[0] if value and value.props else None


def props(element):
    value = child(element, b'Properties70')
    return {e.props[0].decode(): list(e.props[4:]) for e in value.elems} if value else {}


def name(element):
    return element.props[1].decode().split('\x00')[0]


def json_value(value):
    if isinstance(value, bytes):
        return value.decode()
    if isinstance(value, np.generic):
        return value.item()
    return str(value)


def expected_parts(manifest, filename):
    """Accept flat parts with a file or grouped files/exports/layers with parts."""
    found = []
    def visit(value, inherited_file=None):
        if isinstance(value, list):
            for item in value:
                visit(item, inherited_file)
        elif isinstance(value, dict):
            file_value = value.get('file', value.get('filename', inherited_file))
            if file_value is not None:
                file_value = Path(str(file_value)).name
            if all(k in value for k in ('name', 'vertices', 'triangles', 'min', 'max', 'materials')):
                if file_value == filename:
                    found.append(value)
            for key in ('parts', 'files', 'exports', 'layers', 'groups'):
                if key in value:
                    visit(value[key], file_value)
    visit(manifest)
    return {part['name']: part for part in found}


def minimum_triangle_area(points, polygon_indices, ends):
    """Fast triangles/quads; Blender tessellation only for larger polygons."""
    starts = np.r_[0, ends[:-1] + 1]
    counts = ends - starts + 1
    minimum = math.inf
    triangles = 0
    repeated = 0
    for count, splits in ((3, ((0, 1, 2),)), (4, ((0, 1, 2), (0, 2, 3)))):
        selected = starts[counts == count]
        for offset in range(0, len(selected), 100000):
            chunk = selected[offset:offset + 100000]
            ids = polygon_indices[chunk[:, None] + np.arange(count)[None, :]]
            repeated += int(np.count_nonzero(np.any(np.diff(np.sort(ids, axis=1), axis=1) == 0, axis=1)))
            for split in splits:
                a, b, c = (points[ids[:, i]] for i in split)
                areas = np.linalg.norm(np.cross(b - a, c - a), axis=1) * .5
                if areas.size:
                    minimum = min(minimum, float(areas.min()))
                triangles += len(chunk)
    for start, count in zip(starts[counts > 4], counts[counts > 4]):
        ids = polygon_indices[start:start + count]
        repeated += len(np.unique(ids)) != count
        coords = [Vector(v) for v in points[ids]]
        for tri in tessellate_polygon([coords]):
            if isinstance(tri[0], int):
                tri = [coords[i] for i in tri]
            minimum = min(minimum, (tri[1] - tri[0]).cross(tri[2] - tri[0]).length * .5)
            triangles += 1
    return minimum, triangles, repeated


def audit(path, expected):
    tree, version = parse_fbx.parse(str(path))
    objects_element, connections = child(tree, b'Objects'), child(tree, b'Connections')
    objects = objects_element.elems
    links = [(e.props[0], e.props[1], e.props[2]) for e in connections.elems]
    byid = {e.props[0]: e for e in objects}
    links_to = {}
    for kind, source, destination in links:
        if kind == b'OO':
            links_to.setdefault(destination, []).append(source)
    settings = props(child(tree, b'GlobalSettings'))
    checks = {
        'manifest_parts_present': bool(expected),
        'y_up': settings.get('UpAxis') == [1] and settings.get('UpAxisSign') == [1],
        'axis_matches_existing_art': settings.get('FrontAxis') == [2] and settings.get('FrontAxisSign') == [1] and settings.get('CoordAxis') == [0] and settings.get('CoordAxisSign') == [1],
        'metres_unit': settings.get('UnitScaleFactor') == [100.0],
        'no_animation_camera_light': not any(e.id.startswith(b'Animation') or (e.id == b'NodeAttribute' and e.props[-1] in [b'Camera', b'Light']) for e in objects),
    }
    models, geometries = [], []
    for element in objects:
        if element.id == b'Model':
            values, mc = props(element), {}
            for key, default in [
                ('Lcl Translation', [0., 0., 0.]), ('Lcl Rotation', [0., 0., 0.]),
                ('Lcl Scaling', [1., 1., 1.]), ('PreRotation', [0., 0., 0.]),
                ('PostRotation', [0., 0., 0.]), ('GeometricTranslation', [0., 0., 0.]),
                ('GeometricRotation', [0., 0., 0.]), ('GeometricScaling', [1., 1., 1.]),
            ]:
                value = np.asarray(values.get(key, default))
                mc[key] = value.shape == (3,) and bool(np.isfinite(value).all()) and bool(np.allclose(value, default, atol=1e-5, rtol=0))
            mc['root_at_scene'] = element.props[0] in links_to.get(0, [])
            models.append({'name': name(element), 'checks': mc, 'passed': all(mc.values())})
        if element.id != b'Geometry' or element.props[-1] != b'Mesh':
            continue
        raw = arr(element, b'Vertices', np.float64)
        points = raw.reshape((-1, 3))
        raw_indices = arr(element, b'PolygonVertexIndex', np.int64)
        ends = np.flatnonzero(raw_indices < 0)
        indices = np.where(raw_indices < 0, -raw_indices - 1, raw_indices)
        counts = np.diff(np.r_[-1, ends])
        valid_indices = bool(indices.size and ends.size and ends[-1] == len(indices) - 1 and counts.min() >= 3 and indices.min() >= 0 and indices.max() < len(points))
        linked_models = [destination for kind, source, destination in links if kind == b'OO' and source == element.props[0] and destination in byid and byid[destination].id == b'Model']
        materials = [name(byid[source]) for model_id in linked_models for source in links_to.get(model_id, []) if source in byid and byid[source].id == b'Material']
        uv, normal, material = (child(element, key) for key in (b'LayerElementUV', b'LayerElementNormal', b'LayerElementMaterial'))
        uv_data, uv_indices = arr(uv, b'UV', np.float64), arr(uv, b'UVIndex', np.int64)
        n_data, n_indices = arr(normal, b'Normals', np.float64), arr(normal, b'NormalsIndex', np.int64)
        m_indices = arr(material, b'Materials', np.int64)
        uv_mapping, uv_ref = scalar(uv, b'MappingInformationType'), scalar(uv, b'ReferenceInformationType')
        n_mapping, n_ref = scalar(normal, b'MappingInformationType'), scalar(normal, b'ReferenceInformationType')
        m_mapping = scalar(material, b'MappingInformationType')
        n_expected = {b'ByPolygonVertex': len(indices), b'ByVertice': len(points), b'ByVertex': len(points), b'ByPolygon': len(ends), b'AllSame': 1}.get(n_mapping, -1)
        n_mapping_ok = len(n_data) // 3 == n_expected if n_ref == b'Direct' else n_ref == b'IndexToDirect' and len(n_indices) == n_expected and bool(n_indices.size and n_indices.min() >= 0 and n_indices.max() < len(n_data) // 3)
        uv_mapping_ok = uv_mapping == b'ByPolygonVertex' and ((uv_ref == b'Direct' and len(uv_data) // 2 == len(indices)) or (uv_ref == b'IndexToDirect' and len(uv_indices) == len(indices) and bool(uv_indices.size and uv_indices.min() >= 0 and uv_indices.max() < len(uv_data) // 2)))
        n_lengths = np.einsum('ij,ij->i', n_data.reshape((-1, 3)), n_data.reshape((-1, 3))) if n_data.size and len(n_data) % 3 == 0 else np.asarray([])
        minimum, tess_count, repeated = minimum_triangle_area(points, indices, ends) if valid_indices else (0., 0, -1)
        points[:, 0] *= -1  # Prior shaft/tree export handedness convention, inferred Unity bounds.
        low, high = points.min(axis=0).tolist(), points.max(axis=0).tolist()
        triangles = int((counts - 2).sum())
        gc = {
            'finite_vertices': bool(raw.size and len(raw) % 3 == 0 and np.isfinite(raw).all()),
            'valid_polygon_indices': valid_indices and repeated == 0,
            'tessellation_triangle_count': tess_count == triangles,
            'no_degenerate_triangles': minimum > 1e-12,
            'finite_uv': bool(uv_data.size and len(uv_data) % 2 == 0 and np.isfinite(uv_data).all()),
            'uv_corner_mapping': bool(uv_mapping_ok),
            'finite_unit_normals': bool(n_lengths.size and np.isfinite(n_data).all() and np.all((n_lengths > .98) & (n_lengths < 1.02))),
            'normal_mapping_complete': bool(n_mapping_ok),
            'material_indices_valid': bool(materials and m_indices.size and m_indices.min() >= 0 and m_indices.max() < len(materials) and ((m_mapping == b'ByPolygon' and len(m_indices) == len(ends)) or (m_mapping == b'AllSame' and len(m_indices) == 1))),
        }
        part = expected.get(name(element))
        gc['manifest_part_present'] = part is not None
        if part:
            gc['manifest_vertices_triangles_match'] = part['vertices'] == len(points) and part['triangles'] == triangles
            gc['manifest_bounds_match_expected_unity'] = bool(np.allclose(low + high, part['min'] + part['max'], atol=2e-4, rtol=0))
            gc['manifest_materials_match'] = materials == part['materials']
        geometries.append({'name': name(element), 'vertices': len(points), 'polygons': len(ends), 'triangles': triangles, 'minimum_triangle_area_m2': minimum, 'expected_unity_min': low, 'expected_unity_max': high, 'materials': materials, 'checks': gc, 'passed': all(gc.values())})
    checks['mesh_model_counts_match'] = len(models) == len(geometries) > 0
    checks['all_manifest_parts_present'] = set(expected) == {g['name'] for g in geometries}
    return {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'version': version, 'axis_settings': settings, 'checks': checks, 'models': models, 'geometry': geometries, 'total_triangles': sum(g['triangles'] for g in geometries), 'passed': all(checks.values()) and all(m['passed'] for m in models + geometries)}


def main():
    manifest_path = ROOT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    result = {'method': 'Independent raw FBX parse, batched NumPy geometry checks, Blender tessellation for polygons above four corners. No Unity import/UI or runtime validation. Bounds use prior art handedness convention.', 'manifest_available': bool(manifest), 'files': []}
    for filename in FILES:
        path = ROOT / 'exports' / filename
        try:
            entry = audit(path, expected_parts(manifest, filename)) if path.exists() else {'file': str(path), 'passed': False, 'error': 'missing'}
        except Exception as error:
            entry = {'file': str(path), 'passed': False, 'error': repr(error)}
        result['files'].append(entry)
        print('AUDIT_FILE', filename, entry['passed'], flush=True)
    result['total_triangles'] = sum(f.get('total_triangles', 0) for f in result['files'])
    result['passed'] = bool(manifest) and all(f['passed'] for f in result['files'])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'environment_fbx_audit.json').write_text(json.dumps(result, indent=2, default=json_value), encoding='utf-8')
    summary = {'passed': result['passed'], 'total_triangles': result['total_triangles'], 'files': [{'file': Path(f['file']).name, 'passed': f['passed'], 'triangles': f.get('total_triangles'), 'error': f.get('error'), 'failed_checks': [key for key, passed in f.get('checks', {}).items() if not passed] + [g['name'] + ':' + key for g in f.get('geometry', []) for key, passed in g['checks'].items() if not passed]} for f in result['files']]}
    print('ENVIRONMENT_AUDIT_RESULT', json.dumps(summary, default=json_value), flush=True)


if __name__ == '__main__':
    main()
