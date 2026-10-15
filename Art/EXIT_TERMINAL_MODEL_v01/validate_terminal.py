"""Read-only asset checks in a separate Blender process, no Unity use."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from io_scene_fbx import parse_fbx
import numpy as np

OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'RELAY_ExitTerminal.blend'))
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
checks=[]
def check(name,ok,details=None):
    checks.append({'name':name,'passed':bool(ok),'details':details})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def bounds(points): return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
def error(a,b): return max(abs(x-y) for va,vb in zip(a,b) for x,y in zip(va,vb))

total=0
for part in manifest['parts']:
    name=part['name']; original=bpy.data.objects[name]
    points=[p.co.copy() for p in original.data.vertices]; expected=bounds(points)
    check(name+' finite geometry',all(math.isfinite(x) for p in points for x in p))
    check(name+' controlled material names',set(m.name for m in original.data.materials).issubset({'RLYT_Surface','RLYT_Ink','RLYT_Legend','RLYT_CRTScreen'}))
    total+=sum(len(p.vertices)-2 for p in original.data.polygons)
    if name!='TERMINAL_Screen':
        uv=original.data.uv_layers.active
        check(name+' complete UV map',uv is not None and len(uv.data)==len(original.data.loops))
        check(name+' UV coordinates within atlas',uv is not None and all(-.0001<=x<=1.0001 for a in uv.data for x in a.uv))
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT/part['file']))
    imported=set(bpy.data.objects)-before
    meshes=[o for o in imported if o.type=='MESH']
    after=bounds([o.matrix_world@p.co for o in meshes for p in o.data.vertices])
    check(name+' FBX reimport preserves dimensions',len(meshes)==1 and error(expected,after)<.00005,{'max_error_m':error(expected,after)})
    check(name+' FBX neutral origin and no animation',len(imported)==1 and meshes[0].location.length<.00001 and meshes[0].animation_data is None)
    # Verify raw exported axes against the established RELAY Y180 attachment rule.
    root,version=parse_fbx.parse(str(OUT/part['file']))
    objects=next(e for e in root.elems if e.id==b'Objects')
    geometry=next(e for e in objects.elems if e.id==b'Geometry')
    raw=next(e for e in geometry.elems if e.id==b'Vertices').props[0]
    # Unity's handedness X reflection followed by a 180-degree Y child rotation.
    converted=[Vector((raw[i],raw[i+1],-raw[i+2])) for i in range(0,len(raw),3)]
    expected_unity=bounds([P@p for p in points])
    check(name+' FBX axes match documented attachment',error(expected_unity,bounds(converted))<.00005)
    for o in imported: bpy.data.objects.remove(o,do_unlink=True)

check('One environment prop triangle budget',total<40000,{'triangles':total,'budget':40000})
check('69 modelled keys',manifest['keyboard_key_count']==69)
body=bpy.data.objects['TERMINAL_Body']; keys=bpy.data.objects['TERMINAL_Keys']
keypoints=[P@(keys.matrix_world@p.co) for p in keys.data.vertices]
check('Keycaps clear CRT front lip',min(p.z for p in keypoints)>.237+.03,{'nearest_key_z':min(p.z for p in keypoints)})
screen=bpy.data.objects['TERMINAL_Screen']
spoints=[P@(screen.matrix_world@p.co) for p in screen.data.vertices]
check('Screen remains behind existing WorldStatus canvas',max(p.z for p in spoints)<.245-.008,{'frontmost_glass_z':max(p.z for p in spoints),'canvas_z':.245})
check('Screen normals face player',sum((P@p.normal).z for p in screen.data.polygons)>0)
bodypoints=[P@p.co for p in body.data.vertices]
bvh=BVHTree.FromPolygons(bodypoints,[tuple(p.vertices) for p in body.data.polygons],all_triangles=False)
hits=0
for ix in range(31):
    for iy in range(17):
        hit=bvh.ray_cast(Vector((-.30+.60*ix/30,1.11+.28*iy/16,1)),Vector((0,0,-1)),1-.245)
        hits+=hit[0] is not None
check('Live status text area has no front occlusion',hits==0,{'rays':31*17,'blocked':hits})
for filename in ('TERMINAL_BaseColor.png','TERMINAL_Roughness.png','TERMINAL_MetallicSmoothness.png'):
    img=bpy.data.images.load(str(OUT/'textures'/filename),check_existing=False)
    check(filename+' actual saved 2048 texture',list(img.size)==[2048,2048],{'dimensions':list(img.size)})
    if 'MetallicSmoothness' in filename:
        img.colorspace_settings.name='Non-Color'
        values=np.empty(2048*2048*4,dtype=np.float32); img.pixels.foreach_get(values); values=values.reshape(-1,4)
        check('Packed metallic red and smoothness alpha retained',values[:,0].max()>.7 and values[:,3].max()>.45 and values[:,3].min()<.4,
              {'metallic_max':float(values[:,0].max()),'smoothness_min':float(values[:,3].min()),'smoothness_max':float(values[:,3].max())})

report={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'unity_opened_or_modified':False,'actual_unity_playtest':False}
(OUT/'checks/validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'passed':report['passed'],'count':len(checks),'failed':[c['name'] for c in checks if not c['passed']]}),flush=True)
if not report['passed']: raise RuntimeError('Asset validation failed; see checks/validation.json')
