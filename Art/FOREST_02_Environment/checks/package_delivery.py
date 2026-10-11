"""Package art files and verify Unity source stayed untouched. No Unity writes."""
from pathlib import Path
import hashlib, json, zipfile
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
audit=json.loads((ROOT/'checks/environment_fbx_audit.json').read_text(encoding='utf-8'))
assert audit['passed']
for record in audit['files']:
    p=Path(record['file'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],p
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes_before'].items())
assert unchanged,'Unity source changed after generation; inspect before claiming unchanged.'
texnames=['RLYF_MossFloor_BaseColor.png','RLYF_Floor_Normal.png','RLYF_Path_Cutout.png',
          'RLYF_Rock_BaseColor.png','RLYF_Rock_Normal.png','RLYF_Bark_BaseColor.png',
          'RLYF_Bark_Normal.png','RLYF_Bark_Roughness.png','RLYF_Needles_Atlas.png',
          'RLYF_LogEnd_BaseColor.png','RLYF_LogEnd_Normal.png']
files=sorted((ROOT/'exports').glob('*.fbx'))+[ROOT/'textures'/n for n in texnames]+[ROOT/'README.md']
assert len(files)==19 and all(p.exists() and p.stat().st_size>0 for p in files)
delivery=ROOT/'RELAY_Forest_UnityFiles.zip'
with zipfile.ZipFile(delivery,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(delivery,'r') as z:
    assert z.testzip() is None
    assert len(z.namelist())==19
result={'all_export_audits_passed':True,'audited_export_hashes_current':True,
        'unity_source_files_unchanged':unchanged,'watched_source_count':len(manifest['source_hashes_before']),
        'delivery_zip':str(delivery),'zip_integrity_passed':True,'zip_file_count':len(files),
        'zip_bytes':delivery.stat().st_size,'unity_import_or_playtest_performed':False,
        'tree_count':manifest['tree_count'],'total_triangles':manifest['total_triangles']}
(ROOT/'checks/delivery_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('FOREST_DELIVERY_OK',json.dumps(result),flush=True)
