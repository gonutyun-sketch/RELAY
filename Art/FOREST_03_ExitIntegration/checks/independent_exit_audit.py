"""Read-only model/FBX audit; writes only checks/independent_exit_audit.json."""
import bpy, json, importlib.util, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'FOREST_02_Environment/checks/audit_environment_fbx.py'
spec=importlib.util.spec_from_file_location('old_fbx_audit',OLD)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
manifest=json.loads((ROOT/'manifest.json').read_text())
result={'method':'Independent raw FBX checks and exact triangle-box sweep checks; no Unity execution or writes','files':[]}
for p in manifest['parts']:
    exp=dict(p);exp['min']=p['unity_min'];exp['max']=p['unity_max']
    r=old.audit(ROOT/'exports'/p['file'],{p['name']:exp})
    result['files'].append(r)
    print('FBX_AUDIT',p['file'],r['passed'],flush=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'RELAY_ForestExit_Review.blend'))
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))

def design_geo(objects):
    vertices=[];faces=[];owners=[]
    for ob in objects:
        if ob.type!='MESH':continue
        ob.data.calc_loop_triangles();off=len(vertices)
        vertices.extend([tuple(P@(ob.matrix_world@ve.co)) for ve in ob.data.vertices])
        for t in ob.data.loop_triangles:
            faces.append(tuple(off+i for i in t.vertices));owners.append(ob.name)
    return np.array(vertices),np.array(faces),owners

def tri_box(t,lo,hi):
    c=(lo+hi)*.5;h=(hi-lo)*.5;p=t-c
    edges=[p[1]-p[0],p[2]-p[1],p[0]-p[2]]
    axes=[np.array((1.,0,0)),np.array((0,1.,0)),np.array((0,0,1.)),np.cross(edges[0],edges[1])]
    axes.extend(np.cross(e,a) for e in edges for a in axes[:3])
    for a in axes:
        if np.dot(a,a)<1e-18:continue
        projections=p@a;r=h@np.abs(a)
        if projections.min()>=r-1e-6 or projections.max()<=-r+1e-6:return False
    return True

def overlap_checks(collections,boxes):
    objects=[o for n in collections for o in bpy.data.collections[n].objects]
    vs,fs,names=design_geo(objects);tris=vs[fs]
    mn=tris.min(axis=1);mx=tris.max(axis=1);out=[]
    for label,lower,upper in boxes:
        lo=np.array(lower);hi=np.array(upper)
        candidate=np.flatnonzero(np.all(mx>lo+1e-6,axis=1)&np.all(mn<hi-1e-6,axis=1))
        bad=[int(i) for i in candidate if tri_box(tris[i],lo,hi)]
        out.append({'sweep':label,'overlap_triangle_count':len(bad),'objects':sorted(set(names[i] for i in bad)),
                    'examples':[{'object':names[i],'bounds':[mn[i].tolist(),mx[i].tolist()]} for i in bad[:12]]})
    return out

# Full travel volume of current preserved collider and track footprints.
sweeps=[('moving floor',[-1.7,-30.5,-3.5],[1.7,0,.5]),
        ('moving roof',[-1.7,-27,-3.25],[1.7,3.3,.25]),
        ('track',[-2.53,-30,-.67],[2.53,3.265,-.275]),
        ('hoist envelope',[-.8,-26.6,-1.9],[.8,3.55,-1.5])]
result['swept_clearance']=overlap_checks(['10_EXIT_Hillside','11_EXIT_Headwall','12_EXIT_Landing'],sweeps)
for r in result['swept_clearance']:print('SWEEP',r['sweep'],r['overlap_triangle_count'],r['objects'],flush=True)

def bvh_for(objects):
    vs,fs,_=design_geo(objects)
    return BVHTree.FromPolygons(vs.tolist(),fs.tolist(),all_triangles=True)
terrain=bvh_for(list(bpy.data.collections['01_Terrain_and_Path'].objects))
holes=manifest['rectangular_hole_union']
inside=lambda x,z:any(a+1e-4<x<b-1e-4 and c+1e-4<z<d-1e-4 for a,b,c,d in holes)
blocked=[];total=0
for x in np.arange(-2.6,2.61,.1):
    for z in np.arange(-3.5,.51,.1):
        if not inside(x,z):continue
        total+=1;hit=terrain.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4)
        if hit[0] is not None:blocked.append([float(x),float(z),list(hit[0])])
result['terrain_aperture_rays']={'count':total,'blocked_count':len(blocked),'blocked_examples':blocked[:30]}

hill=bvh_for(list(bpy.data.collections['10_EXIT_Hillside'].objects))
blocked=[];total=0
for x in np.arange(-2.5,2.51,.25):
    for z in np.arange(-3.25,.51,.25):
        total+=1;hit=hill.ray_cast(Vector((x,3.7,z)),Vector((0,-1,0)),5.8)
        if hit[0] is not None:blocked.append([float(x),float(z),list(hit[0])])
result['hillside_cavity_rays']={'count':total,'blocked_count':len(blocked),'blocked_examples':blocked[:30]}

# Source heights identify near-coplanar forest ground vs fixed landing top.
landing=bvh_for(list(bpy.data.collections['12_EXIT_Landing'].objects));same=[];protrusions=[]
for x in np.arange(-1.65,1.66,.15):
    for z in np.arange(.60,1.75,.1):
        th=terrain.ray_cast(Vector((x,1,z)),Vector((0,-1,0)),2)[0]
        lh=landing.ray_cast(Vector((x,1,z)),Vector((0,-1,0)),2)[0]
        if th is not None and lh is not None:
            d=th.y-lh.y
            if abs(d)<.002:same.append([float(x),float(z),float(d)])
            if d>.002:protrusions.append([float(x),float(z),float(d)])
result['ground_landing_overlap']={'coplanar_count':len(same),'terrain_above_landing_count':len(protrusions),'examples':(same+protrusions)[:20]}
# Looking down and sideways after arrival should meet cabin, lip, or fixed throat,
# rather than expose a ray deep into the old shaft. Preview cabin is included.
names=['10_EXIT_Hillside','11_EXIT_Headwall','12_EXIT_Landing','13_EXIT_SealTrim_VISUAL_ONLY','14_MOVING_ELEVATOR_LandingApron','01_Terrain_and_Path','91_PREVIEW_Elevator_NOT_EXPORTED']
assembled=bvh_for([o for n in names for o in bpy.data.collections[n].objects])
leaks=[];samples=0
for eye in [(0,1.62,-1.5),(-.85,1.62,-1.0),(.85,1.62,-1.0),(0,1.62,.8)]:
    for az in range(0,360,5):
        for pitch in (-80,-65,-50,-35):
            a=math.radians(az);p=math.radians(pitch)
            direction=Vector((math.sin(a)*math.cos(p),math.sin(p),math.cos(a)*math.cos(p)))
            samples+=1;hit=assembled.ray_cast(Vector(eye),direction,30)
            if hit[0] is None or hit[0].y < -.75:
                leaks.append({'eye':eye,'azimuth':az,'pitch':pitch,'hit':list(hit[0]) if hit[0] is not None else None})
result['arrival_oblique_down_rays']={'samples':samples,'deep_or_miss_count':len(leaks),'examples':leaks[:30]}
result['fbx_passed']=all(f['passed'] for f in result['files'])
result['swept_clear']=all(not c['overlap_triangle_count'] for c in result['swept_clearance'])
result['holes_clear']=result['terrain_aperture_rays']['blocked_count']==0 and result['hillside_cavity_rays']['blocked_count']==0
result['landing_clear']=not same and not protrusions
result['passed']=all(result[k] for k in ('fbx_passed','swept_clear','holes_clear','landing_clear'))
(ROOT/'checks/independent_exit_audit.json').write_text(json.dumps(result,indent=2,default=old.json_value),encoding='utf-8')
print('EXIT_INDEPENDENT_AUDIT',json.dumps({k:result[k] for k in ('passed','fbx_passed','swept_clear','holes_clear','landing_clear')}),flush=True)
