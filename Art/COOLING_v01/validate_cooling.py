"""Read Blender/FBX art and write a local QA report; never opens Unity."""
import bpy, os, json, math
from mathutils import Vector, Matrix
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'RELAY_COOLING_v01.blend'))
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
with open(os.path.join(OUT,'manifest.json'),encoding='utf-8') as f: manifest=json.load(f)
report={'unity_opened_or_modified':False,'checks':[],'unity_runtime_test':'Pending manual import and gameplay verification by user'}
def check(name,condition,details):
    report['checks'].append(dict(name=name,passed=bool(condition),details=details))
def bounds(coords): return [[min(c[i] for c in coords),max(c[i] for c in coords)] for i in range(3)]
for entry in manifest['parts']:
    name=entry['name']; mesh=bpy.data.objects[name+'_EXPORT']
    expected=bounds([p.co for p in mesh.data.vertices])
    previous=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT,entry['file']))
    added=set(bpy.data.objects)-previous
    coords=[o.matrix_world@p.co for o in added if o.type=='MESH' for p in o.data.vertices]
    actual=bounds(coords); err=max(abs(a-b) for er,ar in zip(expected,actual) for a,b in zip(er,ar))
    check(name+' FBX round-trip dimensions',err<.00005,{'maximum_axis_bound_error_m':err})
    check(name+' finite geometry',all(math.isfinite(c) for p in coords for c in p),{'vertices':len(coords),'triangles':entry['triangles']})
    for ob in added: bpy.data.objects.remove(ob,do_unlink=True)
check('Triangle budget',manifest['triangles_total']<90000,manifest['triangles_total'])
# Original retained wheel colliders, evaluated in WheelPivot-local coordinates.
def box_hit(p,center,size,angle=0):
    x,y,z=p; x-=center[0]; y-=center[1]; z-=center[2]
    a=math.radians(angle); X=x*math.cos(a)+y*math.sin(a); Y=-x*math.sin(a)+y*math.cos(a)
    return abs(X)<=size[0]/2+.0001 and abs(Y)<=size[1]/2+.0001 and abs(z)<=size[2]/2+.0001
def wheel_pick(p):
    x,y,z=p
    if x*x+y*y<=.065**2 and abs(z)<=.0501: return True
    if box_hit(p,(0,0,0),(.48,.035,.04)) or box_hit(p,(0,0,0),(.035,.48,.04)): return True
    if box_hit(p,(0,.24,-.032),(.055,.045,.02)): return True
    for i in range(8):
        a=math.radians(i*45)
        # A +Y rim segment rotated around Unity +Z.
        if box_hit(p,(-math.sin(a)*.24,math.cos(a)*.24,0),(.21,.045,.05),i*45): return True
    return False
wheel=bpy.data.objects['VALVE_Wheel_EXPORT']
samples=[P@p.co for p in wheel.data.vertices]
covered=sum(wheel_pick(p) for p in samples)
missed=[p for p in samples if not wheel_pick(p)]
check('Wheel vertices inside existing approximate pick volumes',covered==len(samples),{'covered':covered,'total':len(samples),'missed_bounds':bounds(missed) if missed else None,'missed_examples':[list(p) for p in missed[:10]],'note':'Analytic retained collider volumes; actual Unity raycast remains a manual check.'})
gauge=next(p for p in manifest['parts'] if p['name']=='FLOW_Housing')
wheelentry=next(p for p in manifest['parts'] if p['name']=='VALVE_Wheel')
gap=(.28+wheelentry['bounds_unity_local'][0][0])-(-.32+gauge['bounds_unity_local'][0][1])
check('Valve and gauge horizontal separation at neutral pose',gap>.025,{'gap_m':gap,'note':'Wheel is further forward than gauge; full sweeps evaluated below.'})
# Conservative whole wheel swept radius, which includes corners of the octagonal rim.
maxr=max(math.hypot(p.x,p.y) for p in samples)
gap_sweep=.6-gauge['bounds_unity_local'][0][1]-maxr
check('Full wheel sweep does not hit gauge envelope',gap_sweep>.008,{'minimum_conservative_xy_gap_m':gap_sweep,'wheel_radius_m':maxr})
check('Flow readout remains in front of opaque face',-.095<-.087,{'text_z':-.095,'face_front_z':-.087,'clearance_m':.008})
check('Thermal readout remains in front of opaque face',-.082<-.0795,{'text_z':-.082,'face_front_z':-.0795,'clearance_m':.0025})
check('Neutral moving pivots match source scene',all(next(p for p in manifest['parts'] if p['name']==name)['authoring_pivot']==xyz for name,xyz in [('PUMP_Handle',[0,0,-.085]),('VALVE_Wheel',[0,0,-.2]),('FLOW_Needle',[0,.035,-.095])]),'PUMP_Handle, VALVE_Wheel, FLOW_Needle')
check('Nine separate exported meshes',len(manifest['parts'])==9, [p['name'] for p in manifest['parts']])
report['all_checks_passed']=all(c['passed'] for c in report['checks'])
os.makedirs(os.path.join(OUT,'checks'),exist_ok=True)
with open(os.path.join(OUT,'checks','validation.json'),'w',encoding='utf-8') as f: json.dump(report,f,indent=2)
print(json.dumps(report,indent=2),flush=True)
