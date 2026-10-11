"""Fix only the external forest source/export. Never write into Unity."""
import ast, hashlib, json, math, shutil
from pathlib import Path
import bpy, bmesh
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[1]
PROJECT=Path(r'C:\Users\gonut\School_p2').resolve()
assert not ROOT.is_relative_to(PROJECT)
FIX=ROOT/'fixes'/'TerrainFacing_20261010'
FIX.mkdir(parents=True,exist_ok=True)
BACK=FIX/'before'; BACK.mkdir(exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
watched=[PROJECT/'Assets/Scenes/Startup_Graybox.unity',
         *sorted((PROJECT/'Assets/RELAY/Scripts').glob('*.cs')),
         *sorted(p for p in (PROJECT/'Assets/RELAY/Art/Forest').rglob('*') if p.is_file())]
before={str(p):digest(p) for p in watched}
original=ROOT/'RELAY_MountainForest.blend'
fbx=ROOT/'exports/FOREST_Terrain.fbx'
for p in (original,fbx):
    target=BACK/p.name
    if not target.exists():shutil.copy2(p,target)

bpy.ops.wm.open_mainfile(filepath=str(original))
bpy.context.preferences.filepaths.save_version=0
source=[]
for name in ('Forest_Ground','Worn_Forest_Path'):
    o=bpy.data.objects[name]
    verts=[tuple(v.co) for v in o.data.vertices]
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update()
    wrong=[f for f in bm.faces if f.normal.z<0]
    count=len(wrong)
    if wrong:bmesh.ops.reverse_faces(bm,faces=wrong)
    bm.to_mesh(o.data);bm.free();o.data.update()
    assert verts==[tuple(v.co) for v in o.data.vertices], 'Vertex positions changed'
    assert all(p.normal.z>0 for p in o.data.polygons), name
    source.append({'object':name,'faces_reversed':count,'faces':len(o.data.polygons),'all_upward':True})

# Reuse the original exporter so object names, material slots, UVs and axes stay identical.
tree=ast.parse((ROOT/'build_environment.py').read_text(encoding='utf-8-sig'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='aggregate')
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
env={'bpy':bpy,'Matrix':Matrix,'math':math,'OUT':ROOT,
     'exports':bpy.data.collections['99_Unity_Exports'],'design':lambda p:P@p}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(ROOT/'build_environment.py'),'exec'),env)
record=env['aggregate'](bpy.data.collections['01_Terrain_and_Path'],'FOREST_Terrain')
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
old=next(p for p in manifest['parts'] if p['file']=='FOREST_Terrain.fbx')
assert record['vertices']==old['vertices'] and record['triangles']==old['triangles']
assert record['materials']==old['materials']
for field in ('min','max'):
    assert all(abs(a-b)<1e-5 for a,b in zip(record[field],old[field])),field
bpy.ops.wm.save_as_mainfile(filepath=str(original))
shutil.copy2(fbx,FIX/'FOREST_Terrain.fbx')

# Re-import the actual exported file and check its geometric faces, not just shading normals.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx))
actual=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    nt=o.matrix_world.to_3x3().inverted().transposed()
    for mi,m in enumerate(o.data.materials):
        normals=[(nt@p.normal).normalized().z for p in o.data.polygons if p.material_index==mi]
        assert normals and min(normals)>0, m.name
        actual.append({'material':m.name,'faces':len(normals),'minimum_up_normal':min(normals),'all_upward':True})
changed=[str(p) for p in watched if digest(p)!=before[str(p)]]
report={'source':source,'exported_faces':actual,'vertex_positions_unchanged':True,
        'bounds_material_names_and_counts_preserved':True,'triangles':record['triangles'],
        'replacement':str(FIX/'FOREST_Terrain.fbx'),'sha256':digest(fbx),
        'unity_watched_files_changed':changed,'unity_import_or_playtest_performed':False}
(FIX/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TERRAIN_FACING_REPAIR '+json.dumps(report),flush=True)
