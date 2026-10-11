"""Read-only FBX regression against installed Unity art; writes report outside Unity."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Matrix
assert bpy.app.background
ROOT=Path(__file__).resolve().parent
UNITY=Path(r'C:\Users\gonut\School_p2')
MODELS=UNITY/'Assets/_STARTUP/Art/Lighting/Models'
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf8'))
tracked=[UNITY/'Assets/Scenes/Startup_Graybox.unity']+list(MODELS.glob('*.fbx'))+list(MODELS.glob('*.meta'))
def hashes(): return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
before=hashes()
def read(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==1
    o=meshes[0]; me=o.data
    mats=[m.name for m in me.materials]
    return {'object':o.name,'vertices':[tuple(o.matrix_world@v.co) for v in me.vertices],
        'faces':[tuple(p.vertices) for p in me.polygons],
        'uvs':[[tuple(d.uv) for d in uv.data] for uv in me.uv_layers],
        'origin':tuple(o.matrix_world.translation),
        'counts':{name:sum(p.material_index==i for p in me.polygons) for i,name in enumerate(mats)},
        'materials':mats}
def delta(a,b):
    if len(a)!=len(b): return float('inf')
    return max((abs(x-y) for aa,bb in zip(a,b) for x,y in zip(aa,bb)),default=0)
report={'scope':'Actual FBX reimports; material face allocation and geometry comparison to untouched Unity files.', 'parts':[]}
for entry in manifest['parts']:
    name=entry['name']; old=read(MODELS/(name+'.fbx')); new=read(ROOT/'exports'/(name+'.fbx'))
    vd=delta(old['vertices'],new['vertices'])
    uv_ok=len(old['uvs'])==len(new['uvs']) and all(delta(a,b)<1e-7 for a,b in zip(old['uvs'],new['uvs']))
    checks={'same_object_name':old['object']==new['object'], 'same_positions':vd<1e-7,
        'same_topology':old['faces']==new['faces'], 'same_uv':uv_ok,
        'same_zero_pivot':old['origin']==new['origin']==(0.,0.,0.),
        'same_material_names':old['materials']==new['materials'],
        'all_materials_used':all(n>0 for n in new['counts'].values()),
        'face_counts_match_source_export':new['counts']==entry['material_face_counts']}
    report['parts'].append({'name':name,'old_face_counts':old['counts'],'new_face_counts':new['counts'],
        'position_max_error':vd,'checks':checks,'passed':all(checks.values())})
report['unity_files_unchanged']=before==hashes()
report['all_passed']=report['unity_files_unchanged'] and all(p['passed'] for p in report['parts'])
(ROOT/'checks'/'material_fix_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
assert report['all_passed']
