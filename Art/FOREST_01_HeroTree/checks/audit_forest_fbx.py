"""Independent art-only FBX audit. Never imports into or writes to Unity."""
import sys, json, math, hashlib
from pathlib import Path
from io_scene_fbx import parse_fbx
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

OUT = Path(__file__).resolve().parent
ROOT = Path(r'C:\Users\gonut\RELAY_Art\FOREST_01_HeroTree')
NAMES = ['FOREST_Spruce_A_LOD%d.fbx' % n for n in range(3)]

def child(e, key):
    return next((x for x in e.elems if x.id == key), None) if e else None

def arr(e, key):
    a = child(e, key)
    return list(a.props[0]) if a else []

def scalar(e, key):
    a = child(e, key)
    return a.props[0] if a and a.props else None

def props(e):
    p = child(e, b'Properties70')
    return {x.props[0].decode(): list(x.props[4:]) for x in p.elems} if p else {}

def name(e):
    return e.props[1].decode().split('\x00')[0]

def finite(a):
    return all(math.isfinite(x) for x in a)

def audit(path, expected):
    tree, version = parse_fbx.parse(str(path))
    objects = child(tree, b'Objects').elems
    links = [(e.props[0], e.props[1], e.props[2]) for e in child(tree, b'Connections').elems]
    byid = {e.props[0]: e for e in objects}
    settings = props(child(tree, b'GlobalSettings'))
    checks = {
        'y_up': settings.get('UpAxis') == [1] and settings.get('UpAxisSign') == [1],
        'axis_matches_shaft_convention': settings.get('FrontAxis') == [2] and settings.get('FrontAxisSign') == [1] and settings.get('CoordAxis') == [0] and settings.get('CoordAxisSign') == [1],
        'metres_unit': settings.get('UnitScaleFactor') == [100.0],
        'no_animation_camera_light': not any(e.id.startswith(b'Animation') or (e.id == b'NodeAttribute' and e.props[-1] in [b'Camera', b'Light']) for e in objects),
    }
    model_info, geom_info = [], []
    expected_parts = {p['name']: p for p in expected['parts']} if expected else {}
    for e in objects:
        if e.id == b'Model':
            p = props(e)
            mc = {}
            for k, default in [('Lcl Translation', [0., 0., 0.]), ('Lcl Rotation', [0., 0., 0.]), ('Lcl Scaling', [1., 1., 1.]), ('PreRotation', [0., 0., 0.]), ('PostRotation', [0., 0., 0.]), ('GeometricTranslation', [0., 0., 0.]), ('GeometricRotation', [0., 0., 0.]), ('GeometricScaling', [1., 1., 1.])]:
                value = p.get(k, default)
                mc[k] = len(value) == 3 and finite(value) and all(abs(a-b) < 1e-5 for a, b in zip(value, default))
            mc['root_at_scene'] = any(t == b'OO' and a == e.props[0] and b == 0 for t, a, b in links)
            model_info.append({'name': name(e), 'checks': mc, 'passed': all(mc.values())})
        if e.id != b'Geometry' or e.props[-1] != b'Mesh':
            continue
        raw = arr(e, b'Vertices')
        pts = [Vector(raw[i:i+3]) for i in range(0, len(raw), 3)]
        idx = arr(e, b'PolygonVertexIndex')
        polygons, partial = [], []
        for i in idx:
            partial.append(-i-1 if i < 0 else i)
            if i < 0:
                polygons.append(partial)
                partial = []
        valid_idx = not partial and all(len(p) >= 3 and len(set(p)) == len(p) and all(0 <= i < len(pts) for i in p) for p in polygons)
        models = [b for t, a, b in links if t == b'OO' and a == e.props[0] and byid.get(b) and byid[b].id == b'Model']
        mats = [name(byid[a]) for t, a, b in links if t == b'OO' and b in models and byid.get(a) and byid[a].id == b'Material']
        uv = child(e, b'LayerElementUV')
        normals = child(e, b'LayerElementNormal')
        material = child(e, b'LayerElementMaterial')
        uv_data, uv_idx = arr(uv, b'UV'), arr(uv, b'UVIndex')
        n_data, n_idx = arr(normals, b'Normals'), arr(normals, b'NormalsIndex')
        m_idx = arr(material, b'Materials')
        uv_mapping, uv_ref = scalar(uv, b'MappingInformationType'), scalar(uv, b'ReferenceInformationType')
        n_mapping, n_ref = scalar(normals, b'MappingInformationType'), scalar(normals, b'ReferenceInformationType')
        m_mapping = scalar(material, b'MappingInformationType')
        n_expected = len(idx) if n_mapping == b'ByPolygonVertex' else len(pts) if n_mapping == b'ByVertice' else len(polygons) if n_mapping == b'ByPolygon' else 1 if n_mapping == b'AllSame' else -1
        n_count_ok = len(n_data)//3 == n_expected if n_ref == b'Direct' else len(n_idx) == n_expected and all(0 <= i < len(n_data)//3 for i in n_idx)
        minimum_area = math.inf
        tess_triangles = 0
        if valid_idx:
            for polygon in polygons:
                coords = [pts[i] for i in polygon]
                for tri in tessellate_polygon([coords]):
                    if isinstance(tri[0], int):
                        tri = [coords[i] for i in tri]
                    area = (tri[1]-tri[0]).cross(tri[2]-tri[0]).length * .5
                    minimum_area = min(minimum_area, area)
                    tess_triangles += 1
        expected_unity = [Vector((-p.x, p.y, p.z)) for p in pts]
        lo = [min(p[k] for p in expected_unity) for k in range(3)]
        hi = [max(p[k] for p in expected_unity) for k in range(3)]
        triangles = sum(len(p)-2 for p in polygons)
        gc = {
            'finite_vertices': bool(raw) and len(raw)%3 == 0 and finite(raw),
            'valid_polygon_indices': valid_idx,
            'tessellation_triangle_count': tess_triangles == triangles,
            'no_degenerate_triangles': minimum_area > 1e-12,
            'finite_uv': bool(uv_data) and len(uv_data)%2 == 0 and finite(uv_data),
            'uv_corner_mapping': uv_mapping == b'ByPolygonVertex' and ((uv_ref == b'IndexToDirect' and len(uv_idx) == len(idx) and all(0 <= i < len(uv_data)//2 for i in uv_idx)) or (uv_ref == b'Direct' and len(uv_data)//2 == len(idx))),
            'finite_unit_normals': bool(n_data) and len(n_data)%3 == 0 and finite(n_data) and all(.98 < sum(v*v for v in n_data[i:i+3]) < 1.02 for i in range(0, len(n_data), 3)),
            'normal_mapping_complete': n_count_ok,
            'material_indices_valid': bool(mats) and bool(m_idx) and all(0 <= i < len(mats) for i in m_idx) and ((m_mapping == b'ByPolygon' and len(m_idx) == len(polygons)) or (m_mapping == b'AllSame' and len(m_idx) == 1)),
        }
        exp = expected_parts.get(name(e))
        if expected:
            gc['manifest_part_present'] = exp is not None
            if exp:
                gc['manifest_vertices_triangles_match'] = exp['vertices'] == len(pts) and exp['triangles'] == triangles
                gc['manifest_bounds_match_expected_unity'] = all(abs(a-b) < 1e-4 for a,b in zip(lo+hi, exp['min']+exp['max']))
                gc['manifest_materials_match'] = mats == exp['materials']
        if 'Needles' in name(e):
            gc['needle_uv_within_atlas'] = all(-1e-6 <= value <= 1+1e-6 for value in uv_data)
        geom_info.append({'name':name(e), 'vertices':len(pts), 'polygons':len(polygons), 'triangles':triangles, 'minimum_triangle_area_m2':minimum_area, 'expected_unity_min':lo, 'expected_unity_max':hi, 'materials':mats, 'used_material_indices':sorted(set(m_idx)), 'checks':gc, 'passed':all(gc.values())})
    checks['two_mesh_parts'] = len(geom_info) == 2 and len(model_info) == 2
    checks['lod_names_consistent'] = all('_LOD' + path.stem[-1] in item['name'] for item in geom_info + model_info)
    checks['distinct_wood_needles_parts'] = sum('Wood' in item['name'] for item in geom_info) == 1 and sum('Needles' in item['name'] for item in geom_info) == 1
    return {'file':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'version':version, 'axis_settings':settings, 'checks':checks, 'models':model_info, 'geometry':geom_info, 'total_triangles':sum(g['triangles'] for g in geom_info), 'passed':all(checks.values()) and all(x['passed'] for x in model_info + geom_info)}

manifest_path = ROOT/'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else None
result = {'method':'Independent raw FBX parse with Blender parser and polygon tessellation. No Unity import/UI. Unity bounds are inferred using prior shaft X handedness convention, not verified in Unity.', 'manifest_available':bool(manifest), 'files':[]}
for lod, filename in enumerate(NAMES):
    path = ROOT/'exports'/filename
    if not path.exists():
        result['files'].append({'file':str(path),'passed':False,'error':'missing'})
        continue
    try:
        result['files'].append(audit(path, manifest['layers'][lod] if manifest else None))
    except Exception as error:
        result['files'].append({'file':str(path),'passed':False,'error':repr(error)})
totals = [f.get('total_triangles',-1) for f in result['files']]
result['lod_triangle_counts_decrease'] = totals[0] > totals[1] > totals[2] > 0
result['passed'] = bool(manifest) and result['lod_triangle_counts_decrease'] and all(f['passed'] for f in result['files'])
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'forest_fbx_audit.json').write_text(json.dumps(result, indent=2, default=lambda value: value.decode() if isinstance(value, bytes) else str(value)), encoding='utf-8')
print(json.dumps({'passed':result['passed'],'triangles':totals,'files':[{'file':f['file'],'passed':f['passed'],'error':f.get('error')} for f in result['files']]}, indent=2), flush=True)
