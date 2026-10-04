"""RELAY signal art. Standalone authoring: writes only beside this script.
Design dimensions use Unity X/right, Y/up, front/-Z, metres.
The preview is a workshop asset review, not a screenshot from Unity.
"""
import bpy, math, os, json, random, sys, hashlib
from mathutils import Vector, Matrix, Euler, Quaternion

OUT=os.path.dirname(os.path.abspath(__file__))
for folder in ('exports','previews','checks'): os.makedirs(os.path.join(OUT,folder),exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(u): return P @ Vector(u)
def rot(u): return (P @ Euler(tuple(math.radians(a) for a in u),'XYZ').to_matrix() @ P).to_quaternion()
def rgba(h):
    a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in a)+(1,)
def coll(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
source=coll('01_EDITABLE_SIGNAL'); exports=coll('02_NEUTRAL_FBX_MESHES'); studio=coll('03_PREVIEW_ONLY')
def move(ob,c):
    for old in list(ob.users_collection): old.objects.unlink(ob)
    c.objects.link(ob)
mats={}; material_specs=[]
def mat(name,h,metal=0,rough=.5):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=rgba(h)
    b=m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=m.diffuse_color
    b.inputs['Metallic'].default_value=metal; b.inputs['Roughness'].default_value=rough
    mats[name]=m; material_specs.append(dict(name=name,base_color_srgb='#'+h,metallic=metal,smoothness=round(1-rough,3),surface='Opaque'))
    return m
paint=mat('RLYS_CasePaint','626A60',0,.60)
frame=mat('RLYS_FramePaint','363E3A',0,.62)
ivory=mat('RLYS_Enamel','C8C5B2',0,.64)
steel=mat('RLYS_Steel','959B96',.80,.35)
oxid=mat('RLYS_OxidizedSteel','454E49',.65,.59)
rubber=mat('RLYS_Rubber','1B221F',0,.82)
polymer=mat('RLYS_Bakelite','2B302C',0,.44)
brass=mat('RLYS_Brass','89794D',.72,.49)
ink=mat('RLYS_PrintDark','252C28',0,.79)
printlight=mat('RLYS_PrintLight','DED8C3',0,.72)
ochre=mat('RLYS_GainCap','AC925E',0,.54)
gridmat=mat('RLYS_Graticule','355346',0,.9)
parts={}; mount_spec={}; active=None
def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None); source.objects.link(o); o.parent=parent; o.location=v(loc); o.empty_display_size=.045; return o
assembly=empty('RELAY_SIGNAL_V01')
def part(name,parent,loc=(0,0,0),unity_parent=''):
    global active
    active=empty(name,loc,parent); parts[name]=active
    mount_spec[name]=dict(unity_parent=unity_parent,model_child_local_position=[0,0,0],model_child_local_rotation=[0,180,0],model_child_local_scale=[1,1,1],authoring_pivot=list(loc))
    return active
def reg(o,name,loc,m):
    move(o,source); o.name=name; o.parent=active; o.location=v(loc); o.data.materials.append(m); return o
def bevel(o,w=.002,n=2):
    if w:
        b=o.modifiers.new('Manufactured edge radius','BEVEL'); b.width=w; b.segments=n
        b.material=-1
        no=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); no.keep_sharp=True
def box(name,loc,dims,m,bev=.002,angles=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1); o=reg(bpy.context.object,name,loc,m); o.scale=v(dims)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=rot(angles); bevel(o,bev); return o
def cyl(name,loc,r,depth,m,axis='Z',verts=32,bev=.001):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth)
    o=reg(bpy.context.object,name,loc,m); o.rotation_mode='QUATERNION'
    o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(dict(X=(1,0,0),Y=(0,1,0),Z=(0,0,1))[axis]))
    bevel(o,bev)
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    return o
def sphere(name,loc,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=12,radius=1)
    o=reg(bpy.context.object,name,loc,m); o.scale=v(scale)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons: p.use_smooth=True
    return o
def torus(name,loc,major,minor,m,axis='Z'):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=10)
    o=reg(bpy.context.object,name,loc,m); o.rotation_mode='QUATERNION'
    o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(dict(X=(1,0,0),Y=(0,1,0),Z=(0,0,1))[axis]))
    for p in o.data.polygons: p.use_smooth=True
    return o
def mesh(name,coords,faces,loc,m):
    me=bpy.data.meshes.new(name); me.from_pydata([tuple(v(c)) for c in coords],[],faces); me.update()
    o=bpy.data.objects.new(name,me); source.objects.link(o); o.parent=active; o.location=v(loc); me.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    return o
def annulus(name,loc,outer,inner,depth,m):
    n=64; coords=[]; faces=[]
    for z,r in ((-depth/2,outer),(-depth/2,inner),(depth/2,outer),(depth/2,inner)):
        for i in range(n):
            a=i*math.tau/n; coords.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(n):
        j=(i+1)%n; faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    o=mesh(name,coords,faces,loc,m); bevel(o,.001)
    for p in o.data.polygons: p.use_smooth=True
    return o
font=bpy.data.fonts.load('C:/Windows/Fonts/bahnschrift.ttf')
def txt(name,body,loc,size,m=ink,align='CENTER',parent=None,collection=None):
    d=bpy.data.curves.new(name,'FONT'); d.body=body; d.font=font; d.size=size; d.align_x=align; d.align_y='CENTER'; d.resolution_u=2
    o=bpy.data.objects.new(name,d); (collection or source).objects.link(o); o.parent=parent or active; o.location=v(loc); o.rotation_euler=(math.pi/2,0,0); d.materials.append(m); return o
def fastener(name,loc,r=.008,axis='Z',m=steel):
    cyl(name+' washer',loc,r*1.3,.0025,oxid,axis,24,0)
    delta=dict(X=(-.003,0,0),Y=(0,.003,0),Z=(0,0,-.003))[axis]
    p=tuple(loc[i]+delta[i] for i in range(3)); cyl(name+' hex head',p,r,.005,m,axis,6,.0004)
def screw(loc,r=.007,angle=24):
    cyl('Slotted fastener',loc,r,.004,steel,verts=20,bev=.0005)
    box('Screw recess',(loc[0],loc[1],loc[2]-.0021),(r*1.4,.0011,.0003),ink,0,(0,0,angle))
def tube(name,points,r,m,fillet=.05):
    points=[Vector(p) for p in points]; smooth=[points[0]]
    for i in range(1,len(points)-1):
        p=points[i]; a=points[i-1]; b=points[i+1]
        d=min(fillet,(p-a).length*.35,(b-p).length*.35)
        p0=p+(a-p).normalized()*d; p2=p+(b-p).normalized()*d
        smooth.append(p0)
        for k in range(1,9):
            t=k/8; smooth.append((1-t)**2*p0+2*(1-t)*t*p+t*t*p2)
    smooth.append(points[-1]); d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.resolution_u=1
    d.bevel_depth=r; d.bevel_resolution=3; d.use_fill_caps=True
    sp=d.splines.new('POLY'); sp.points.add(len(smooth)-1)
    for pt,u in zip(sp.points,smooth): pt.co=(*v(u),1)
    o=bpy.data.objects.new(name,d); source.objects.link(o); o.parent=active; d.materials.append(m); return o

# Coordinates below are measured against the saved Unity scene; the unit is metres.
# Old functional roots, raycast colliders and live display renderers remain in Unity.
part('SIGNAL_Cabinet',assembly,unity_parent='Environment/SIGNAL_Module')
box('Welded chassis base',(0,-1.159,0),(1.78,.078,.98),frame,.012)
box('Folded cabinet top',(0,1.157,0),(1.79,.05,.98),paint,.008)
box('Rear enclosure',(0,0,.469),(1.738,2.245,.04),paint,.008)
for x in (-.868,.868):
    box('Folded side shell',(x,0,0),(.035,2.26,.96),paint,.007)
    box('Front rack upright',(x,0,-.476),(.06,2.27,.046),oxid,.006)
    box('Side panel rear seam',(x*1.008,0,.396),(.003,2.11,.006),ink,.001)
    for y in (-1.03,.91):
        for z in (-.38,.38):
            cyl('Side assembly screw',(x+(.021 if x>0 else -.021),y,z),.007,.004,steel,'X',16,.0005)
    # Recessed visible slots and their individual upper lips read as ventilation.
    for y in [i*.058 for i in range(-5,7)]:
        box('Side ventilation recess',(x+(.018 if x>0 else -.018),y,.14),(.001,.024,.40),rubber,.005)
        box('Vent folded lip',(x+(.021 if x>0 else -.021),y+.013,.14),(.006,.007,.40),paint,.002)
    for z in (-.36,.36):
        box('Rubber foot',(x*.86,-1.185,z),(.13,.026,.14),rubber,.006)

# Raised edges form a rack with an instrument above and a maintenance bay below.
box('Upper header panel',(0,.974,-.473),(1.65,.305,.032),paint,.005)
box('Instrument rack backing',(0,.02,-.466),(1.65,1.56,.025),frame,.004)
box('Control mounting plate',(0,-.355,-.506),(1.58,.77,.028),ivory,.006)
for x in (-.765,.765):
    for y in (-.707,-.001): screw((x,y,-.524),.007,35)
box('Lower service bay gasket',(0,-.936,-.477),(1.645,.312,.012),rubber,.006)
box('Removable lower service panel',(0,-.936,-.492),(1.62,.293,.025),paint,.004)
for x in (-.771,.771):
    for y in (-1.052,-.820): screw((x,y,-.508),.007,12)
for i in range(17):
    x=-.31+i*.039
    box('Lower intake slot',(x,-.93,-.506),(.020,.078,.001),rubber,.008)
box('Service recessed pull',(.60,-.922,-.51),(.13,.048,.012),oxid,.006)
box('Service pull grip',(.60,-.917,-.521),(.104,.022,.02),polymer,.004)

# Small plain enamel nameplate: no invented slogans, large badges or decorative UI.
box('SIGNAL enamel nameplate',(-.52,.975,-.496),(.35,.10,.004),polymer,.004)
txt('SIGNAL lettering','SIGNAL',(-.52,.975,-.4985),.035,printlight)
for x in (-.68,-.36): screw((x,.975,-.499),.0045,22)
txt('Rack channel number','06',(.727,.975,-.492),.040,printlight)
box('Identification underline',(.727,.940,-.491),(.042,.0013,.0003),printlight,0)

# Scope geometry surrounds the existing screen. The green screen/waves are NOT FBX.
scope=empty('Scope',(0,.42,-.55),assembly)
part('SCOPE_Housing',scope,unity_parent='Environment/SIGNAL_Module/Scope')
box('Instrument rear can',(0,0,.078),(1.425,.762,.30),frame,.035)
# Four pieces, with a real opening, never a solid front plate hiding the waves.
for x in (-.670,.670):
    box('Scope side surround',(x,0,-.087),(.090,.738,.085),ivory,.013)
    box('Inner vertical rubber seal',(math.copysign(.627,x),0,-.094),(.008,.595,.018),rubber,.003)
for y in (-.331,.331):
    box('Scope top bottom surround',(0,y,-.087),(1.27,.076,.085),ivory,.012)
    box('Inner horizontal rubber seal',(0,math.copysign(.293,y),-.094),(1.246,.008,.018),rubber,.002)
# A narrow hood and carrying loops sit outside the active aperture.
box('Upper glare hood',(0,.373,-.052),(1.438,.029,.244),paint,.006)
for x in (-.742,.742):
    box('Rack ear',(x,0,.027),(.052,.74,.036),oxid,.004)
    for y in (-.305,.305): screw((x,y,.007),.008,18)
    for y in (-.157,.157): cyl('Carry handle mounting',(x,y,-.028),.025,.035,oxid)
    tube('Instrument carrying loop',[(x,-.157,-.035),(x,-.157,-.15),(x,.157,-.15),(x,.157,-.035)],.012,steel,.034)
for x in (-.676,.676):
    for y in (-.321,.321): screw((x,y,-.131),.0065,16)
# A restrained etched graticule, behind both live lines and ahead of old Screen.
for i in range(-5,6):
    x=i*.11
    box('Screen vertical graticule',(x,0,-.0985),(.0010,.532,.0003),gridmat,0)
for i in range(-2,3):
    y=i*.106
    box('Screen horizontal graticule',(0,y,-.0985),(1.18,.0010,.0003),gridmat,0)
for i in range(-25,26):
    if i%5: box('Horizontal minor tick',(i*.022,0,-.099),( .0009,.009,.0003),gridmat,0)
for i in range(-10,11):
    if i%5: box('Vertical minor tick',(0,i*.0212,-.099),(.009,.0009,.0003),gridmat,0)
txt('Scope bezel instrument designation','DUAL TRACE',(-.525,-.329,-.131),.016,ink,'LEFT')

# Frequency dial reuses the existing Z-rotation pivot and 270 degree range.
frequency=empty('FREQUENCY_Dial',(-.48,-.16,-.55),assembly)
part('FREQUENCY_Housing',frequency,unity_parent='Environment/SIGNAL_Module/FREQUENCY_Dial')
box('Frequency square mounting flange',(0,0,.011),(.347,.347,.094),ivory,.01)
cyl('Frequency escutcheon',(0,0,-.045),.132,.021,oxid,verts=64,bev=.002)
annulus('Frequency scale ring',(0,0,-.06),.144,.103,.008,ivory)
cyl('Frequency bearing shaft',(0,0,-.068),.034,.037,brass,verts=32)
for i in range(31):
    a=math.radians(135-270*i/30); rr=.130
    length=.017 if i%5==0 else .008
    box('Frequency engraved graduation',(-math.sin(a)*rr,math.cos(a)*rr,-.065),(.0018,length,.0005),ink,0,(0,0,a*180/math.pi))
for value in (1,2,3,4,5,6):
    a=math.radians(135-270*(value-1)/5)
    txt('Frequency numeric marking',str(value),(-math.sin(a)*.158,math.cos(a)*.158,-.04),.015,ink)
txt('Frequency function label','FREQUENCY',(0,-.198,-.045),.022,ink)
for x in (-.159,.159):
    for y in (-.159,.159): screw((x,y,-.038),.0045,12)
freqpivot=empty('PointerPivot',(0,0,-.10),frequency)
part('FREQUENCY_Knob',freqpivot,unity_parent='Environment/SIGNAL_Module/FREQUENCY_Dial/PointerPivot')
cyl('Frequency knob rear shoulder',(0,0,.013),.086,.076,polymer,verts=64,bev=.006)
cyl('Frequency knob grip',(0,0,-.030),.079,.080,polymer,verts=64,bev=.009)
cyl('Frequency flat front insert',(0,0,-.071),.061,.005,frame,verts=64,bev=.002)
for i in range(32):
    a=math.tau*i/32
    cyl('Moulded longitudinal finger rib',(math.cos(a)*.077,math.sin(a)*.077,-.028),.004,.059,polymer,verts=8,bev=.001)
box('Frequency pointer inlay',(0,.061,-.076),(.006,.040,.002),printlight,.001)
cyl('Frequency center cap',(0,0,-.075),.011,.003,steel,verts=24,bev=.0005)

# Fader handles are exported in metres. Their old parents have non-unit scale;
# the handoff specifies inverse child scales while the original colliders remain.
phase=empty('PHASE_Slider',(.10,-.16,-.55),assembly)
part('PHASE_Housing',phase,unity_parent='Environment/SIGNAL_Module/PHASE_Slider')
box('Phase slider backing',(0,0,.005),(.66,.215,.105),ivory,.008)
box('Phase slider dark well',(0,0,-.047),(.564,.069,.008),rubber,.010)
for y in (-.030,.030): box('Phase guide edge',(0,y,-.048),(.548,.005,.005),steel,.001)
for x in (-.303,.303):
    box('Phase mechanical end stop',(x,0,-.048),(.02,.077,.010),oxid,.002)
    screw((x,.083,-.049),.004,0)
    screw((x,-.083,-.049),.004,0)
for i in range(24):
    x=-.25+.50*i/23
    box('Phase scale graduation',(x,.061,-.0505),(.0015,.017 if i%6==0 or i==23 else .009,.0004),ink,0)
for x,label in ((-.25,'0'),(-.25+.5*180/345,'180'),(.25,'345')):
    txt('Phase end marking',label,(x,.089,-.051),.014,ink)
txt('Phase function label','PHASE',(0,-.139,-.049),.022,ink)
phasehandle=empty('Phase moving Handle',(-.25,0,-.09),phase)
part('PHASE_Handle',phasehandle,unity_parent='Environment/SIGNAL_Module/PHASE_Slider/Handle')
mount_spec['PHASE_Handle']['model_child_local_scale']=[1/.07,1/.14,1/.07]
box('Phase fader foot',(0,0,.020),(.064,.13,.027),oxid,.005)
box('Phase tall finger cap',(0,0,-.003),(.062,.131,.058),polymer,.009)
box('Phase ivory inlay',(0,0,-.033),(.007,.096,.002),printlight,.001)
for y in (-.045,-.027,.027,.045): box('Phase grip score',(0,y,-.0328),(.043,.0015,.001),ink,.0004)

gain=empty('GAIN_Slider',(.64,-.28,-.55),assembly)
part('GAIN_Housing',gain,unity_parent='Environment/SIGNAL_Module/GAIN_Slider')
box('Gain slider backing',(0,0,.005),(.235,.512,.105),ivory,.008)
box('Gain slider dark well',(0,0,-.047),(.068,.438,.008),rubber,.010)
for x in (-.030,.030): box('Gain guide edge',(x,0,-.048),(.005,.414,.005),steel,.001)
for y in (-.230,.230):
    box('Gain mechanical end stop',(0,y,-.048),(.083,.018,.010),oxid,.002)
    for x in (-.092,.092): screw((x,y,-.050),.004,40)
for i in range(11):
    y=-.18+.36*i/10
    box('Gain engraved graduation',(-.064,y,-.0505),(.018 if i%5==0 else .010,.0015,.0004),ink,0)
for y,label in ((-.18,'MIN'),(.18,'MAX')): txt('Gain end marking',label,(.074,y,-.051),.012,ink)
txt('Gain function label','GAIN',(0,-.288,-.049),.022,ink)
gainhandle=empty('Gain moving Handle',(0,-.108,-.09),gain)
part('GAIN_Handle',gainhandle,unity_parent='Environment/SIGNAL_Module/GAIN_Slider/Handle')
mount_spec['GAIN_Handle']['model_child_local_scale']=[1/.14,1/.07,1/.07]
box('Gain fader foot',(0,0,.020),(.132,.064,.026),oxid,.005)
box('Gain ochre finger cap',(0,0,-.003),(.132,.063,.058),ochre,.009)
box('Gain black inlay',(0,0,-.033),(.10,.007,.002),ink,.001)
for x in (-.045,-.026,.026,.045): box('Gain grip score',(x,0,-.0328),(.0015,.043,.001),ink,.0004)

# Lock indicator: retain BOTH existing Unity lenses, including the controlled renderer.
lock=empty('LOCK_Indicator',(0,-.65,-.55),assembly)
part('LOCK_Housing',lock,unity_parent='Environment/SIGNAL_Module/LOCK_Indicator')
box('Sync lamp mounting plate',(0,-.015,.01),(.304,.16,.071),ivory,.006)
# aperture width .15, height .075 centered at y .025; old green face sits within.
for x in (-.086,.086): box('Sync bezel side',(x,.025,-.058),(.019,.108,.047),oxid,.004)
for y in (-.021,.071): box('Sync bezel end',(0,y,-.058),(.157,.017,.047),oxid,.003)
txt('Sync label','SYNC',(0,-.069,-.027),.019,ink)
for x in (-.130,.130): screw((x,-.017,-.027),.0045,20)

# Build one neutral mesh per attachable unit, preserving editable source objects.
bpy.context.view_layer.update()
manifest=dict(asset='RELAY SIGNAL v01',unity_modified=False,units='metres',front='Unity -Z',
    reference_scene='Assets/Scenes/Startup_Graybox.unity',reference_module_position=[1,1.2,4],
    import_note='New child position zero, rotation Y180. Scale1 except fader handles: use recorded reciprocal scale. Do not modify functional parents.',
    live_display_note='Keep existing Screen, ReferenceWave, CurrentWave, Lens_Off and Lens_On. Preview waves and lenses never enter exports.',parts=[],materials=material_specs.copy())
for name,pivot in parts.items():
    copies=[]
    for original in list(pivot.children):
        if original.type not in ('MESH','FONT','CURVE'): continue
        dupe=original.copy(); dupe.data=original.data.copy(); exports.objects.link(dupe)
        dupe.parent=None; dupe.matrix_world=original.matrix_world.copy(); copies.append(dupe)
    assert copies,name
    bpy.ops.object.select_all(action='DESELECT')
    for ob in copies: ob.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.convert(target='MESH')
    for ob in list(bpy.context.selected_objects):
        if len(ob.data.uv_layers)==0:
            selected=list(bpy.context.selected_objects)
            for other in selected: other.select_set(False)
            ob.select_set(True); bpy.context.view_layer.objects.active=ob
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.008); bpy.ops.object.mode_set(mode='OBJECT')
            for other in selected: other.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join()
    ob=bpy.context.object; ob.name=name+'_EXPORT'; scene.cursor.location=pivot.matrix_world.translation
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    saved=ob.matrix_world.copy(); ob.matrix_world=Matrix.Identity(4)
    filepath=os.path.join(OUT,'exports',name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=filepath,use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    bounds=[[min((P@p.co)[i] for p in ob.data.vertices),max((P@p.co)[i] for p in ob.data.vertices)] for i in range(3)]
    ob.matrix_world=saved; ob.hide_render=True; ob.hide_set(True)
    manifest['parts'].append(dict(name=name,file='exports/'+name+'.fbx',triangles=sum(len(p.vertices)-2 for p in ob.data.polygons),vertices=len(ob.data.vertices),materials=[m.name for m in ob.data.materials],bounds_unity_local=bounds,**mount_spec[name]))
manifest['triangles_total']=sum(p['triangles'] for p in manifest['parts'])
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,indent=2)

# Preview-only objects recreate the saved Unity screen and live lines for review.
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=6
scene.render.resolution_x=1200; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.19,.17,1); scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'
def preview_mat(name,h,strength=0):
    m=mat('PREVIEW_ONLY_'+name,h,0,.7)
    if strength:
        shader=m.node_tree.nodes.get('Principled BSDF'); shader.inputs['Emission Color'].default_value=rgba(h); shader.inputs['Emission Strength'].default_value=strength
    return m
screenmat=preview_mat('Screen','091B14')
refmat=preview_mat('ReferenceTrace','557666',.25)
wavemat=preview_mat('CurrentTrace','56C694',1.5)
offmat=preview_mat('OffLens','24362A')
def preview_box(name,loc,dims,m,parent):
    global active
    original_active=active; active=parent; o=box(name,loc,dims,m,.001); move(o,studio); active=original_active; return o
preview_box('Unity Screen preview only',(0,0,-.085),(1.28,.60,.02),screenmat,scope)
preview_box('Unity Lens_Off preview only',(0,.025,-.068),(.14,.065,.02),offmat,lock)
# Two different traces demonstrate the unlocked state; final game creates these itself.
for name,freq,phase_deg,amp,z,m in [('Reference trace PREVIEW ONLY',3.5,105,.16,-.110,refmat),('Current trace PREVIEW ONLY',1,0,.09,-.114,wavemat)]:
    points=[]
    for i in range(257):
        t=i/256; points.append(((t-.5)*1.18,math.sin(t*freq*math.tau-math.radians(phase_deg))*amp,z))
    oldactive=active; active=scope; o=tube(name,points,.0022,m,0); move(o,studio); active=oldactive
parts['FREQUENCY_Knob'].rotation_mode='QUATERNION'; parts['FREQUENCY_Knob'].rotation_quaternion=rot((0,0,135))
floormat=preview_mat('Floor','50554F')
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.202)); floor=bpy.context.object; floor.name='Studio floor PREVIEW ONLY'; floor.data.materials.append(floormat); move(floor,studio)
def aim(ob,at): ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=loc; aim(o,(0,-.12,0))
area('Large warm window',(-3,-4,4),700,3.6,(1,.95,.88))
area('Cool ceiling bounce',(2,.7,4),850,3.1,(.90,.96,1))
area('Front soft fill',(3,-4,1),170,2.5,(1,1,1))
camera=bpy.data.objects.new('REVIEW camera',bpy.data.cameras.new('Review camera')); studio.objects.link(camera)
camera.location=(3.8,-7.8,2.1); aim(camera,(0,-.06,0)); camera.data.type='ORTHO'; camera.data.ortho_scale=3.36; scene.camera=camera
scene.render.image_settings.file_format='PNG'
# Pack no external font dependency: source labels become editable meshes.
bpy.ops.object.select_all(action='DESELECT'); texts=[o for o in source.objects if o.type=='FONT']
for ob in texts: ob.select_set(True)
if texts: bpy.context.view_layer.objects.active=texts[0]; bpy.ops.object.convert(target='MESH')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL'; a.spaces.active.overlay.show_overlays=False; a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT'); assembly.select_set(True); bpy.context.view_layer.objects.active=assembly
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_SIGNAL_v01.blend'))
print('SIGNAL_BUILD_COMPLETE',manifest['triangles_total'],flush=True)
if '--skip-renders' not in sys.argv:
    scene.render.filepath=os.path.join(OUT,'previews','SIGNAL_hero.png'); bpy.ops.render.render(write_still=True)
    camera.location=(0,-7,.1); aim(camera,(0,-.06,0)); camera.data.ortho_scale=2.92
    scene.render.filepath=os.path.join(OUT,'previews','SIGNAL_front.png'); bpy.ops.render.render(write_still=True)
    camera.location=(1.7,-5.5,1.4); aim(camera,(0,-.58,.08)); camera.data.ortho_scale=1.85
    scene.render.resolution_x=1500; scene.render.resolution_y=1150
    scene.render.filepath=os.path.join(OUT,'previews','SIGNAL_controls.png'); bpy.ops.render.render(write_still=True)
    print('SIGNAL_PREVIEWS_COMPLETE',flush=True)
