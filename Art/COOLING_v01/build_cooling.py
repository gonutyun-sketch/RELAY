"""RELAY cooling art. Standalone authoring: writes only beside this script.
Design dimensions use Unity X/right, Y/up, front/-Z, metres.
The preview is a workshop asset review, not a screenshot from Unity.
"""
import bpy, math, os, json, random, sys
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
source=coll('01_EDITABLE_COOLING'); exports=coll('02_NEUTRAL_FBX_MESHES'); studio=coll('03_PREVIEW_ONLY')
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
paint=mat('RLYC_PumpBlue','46686C',0,.59)
frame=mat('RLYC_FramePaint','414D49',0,.61)
ivory=mat('RLYC_InstrumentEnamel','C4C3AF',0,.62)
steel=mat('RLYC_Steel','838A85',.8,.37)
oxid=mat('RLYC_OxidizedSteel','414944',.65,.58)
rubber=mat('RLYC_Rubber','1B221F',0,.8)
polymer=mat('RLYC_Bakelite','30352F',0,.45)
brass=mat('RLYC_Brass','89794D',.72,.47)
red=mat('RLYC_ValveRed','87473C',0,.53)
ink=mat('RLYC_PrintDark','252C28',0,.78)
printlight=mat('RLYC_PrintLight','DDD8C3',0,.73)
glass=mat('RLYC_MeterGlass','F0F1E9',0,.1)
glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=1
glass.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45
material_specs[-1].update(surface='Transparent',alpha=.06,receive_shadows=False)
parts={}; mount_spec={}; active=None
def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None); source.objects.link(o); o.parent=parent; o.location=v(loc); o.empty_display_size=.045; return o
assembly=empty('RELAY_COOLING_V01')
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
def wheel_rim():
    # Eight rounded sides agree with the retained Unity rim colliders.
    points=[Vector((math.sin((i+.5)*math.tau/8)*(.240/math.cos(math.pi/8)),math.cos((i+.5)*math.tau/8)*(.240/math.cos(math.pi/8)),0)) for i in range(8)]
    smooth=[]
    for i,p in enumerate(points):
        a=points[(i-1)%8]; b=points[(i+1)%8]; d=.014
        p0=p+(a-p).normalized()*d; p2=p+(b-p).normalized()*d
        for k in range(9):
            t=k/8; smooth.append((1-t)**2*p0+2*(1-t)*t*p+t*t*p2)
    d=bpy.data.curves.new('Rounded octagonal cast rim','CURVE'); d.dimensions='3D'; d.bevel_depth=.018; d.bevel_resolution=3
    sp=d.splines.new('POLY'); sp.points.add(len(smooth)-1); sp.use_cyclic_u=True
    for pt,u in zip(sp.points,smooth): pt.co=(*v(u),1)
    o=bpy.data.objects.new('Rounded octagonal cast rim',d); source.objects.link(o); o.parent=active; d.materials.append(red)
def flange(name,loc,r=.061,axis='Y',m=paint):
    cyl(name+' cast flange',loc,r,.026,m,axis,48,.002)
    delta=dict(X=(.015,0,0),Y=(0,.015,0),Z=(0,0,.015))[axis]
    cyl(name+' gasket',tuple(loc[i]+delta[i] for i in range(3)),r*.94,.003,rubber,axis,48,0)
    for k in range(4):
        a=math.tau*k/4+math.pi/4; u=r*.72*math.cos(a); w=r*.72*math.sin(a)
        off=dict(X=(-.019,u,w),Y=(u,.019,w),Z=(u,w,-.019))[axis]
        fastener(name+' bolt',tuple(loc[i]+off[i] for i in range(3)),.006,axis)

# Open service rack: the actual pump and pipe circuit remain visible.
part('COOLING_Frame',assembly,unity_parent='Environment/COOLING_Module')
for x in (-.855,.855):
    for z in (-.435,.435): box('Welded upright',(x,0,z),(.05,2.32,.05),frame,.003)
for y in (-1.145,1.145):
    for z in (-.435,.435): box('Frame crossmember',(0,y,z),(1.76,.065,.055),frame,.003)
    for x in (-.855,.855): box('Frame depth tie',(x,y,0),(.055,.065,.87),frame,.003)
box('Rear removable service panel',(0,.025,.452),(1.65,2.18,.018),paint,.006)
for x in (-.78,.78):
    for y in (-.99,.99): fastener('Back cover fastening',(x,y,.464),.010,'Z')
box('Drip tray',(0,-1.118,0),(1.68,.035,.83),oxid,.004)
for x in (-.808,.808): box('Tray folded side',(x,-1.074,0),(.025,.087,.80),frame,.003)
box('Tray front return',(0,-1.074,-.393),(1.64,.087,.025),frame,.003)
for x in (-.72,.72):
    for z in (-.32,.32): box('Isolating foot',(x,-1.177,z),(.19,.046,.18),rubber,.008)
box('Top cover',(0,1.175,0),(1.8,.034,.98),paint,.007)
box('Instrument header',(0,.990,-.465),(1.63,.24,.022),frame,.004)
box('Enamel identification plate',(-.27,.99,-.479),(.405,.096,.004),polymer,.004)
txt('Printed COOLING plate','COOLING',(-.27,.99,-.482),.048,printlight)
for x in (-.455,-.085): screw((x,.99,-.484),.0046,18)
txt('Small equipment identifier','05',(.657,1.008,-.479),.059,printlight)
txt('Service type','CIRCULATION',(.651,.96,-.479),.011,printlight)

# Upper gauge carrier and compact individual control mounting brackets.
box('Flow instrument bracket',(-.32,.35,-.480),(.69,.70,.026),ivory,.008)
for x in (-.625,-.015):
    for y in (.044,.655): screw((x,y,-.496),.006)
box('Pump switch mounting plate',(-.30,-.415,-.48),(.42,.43,.024),ivory,.005)
for x in (-.48,-.12): screw((x,-.588,-.495),.005,36)
box('Readout mounting bracket',(.28,-.2,-.47),(.58,.37,.03),frame,.007)
box('Readout rear mount',(.28,-.2,-.39),(.055,.25,.16),steel,.002)
# Bolted stand-offs visibly connect every front carrier to the rack.
for y in (.56,-.40):
    box('Rear instrument support beam',(0,y,-.285),(1.69,.047,.045),frame,.003)
    for x in (-.826,.826): box('Instrument beam end bracket',(x,y,-.367),(.040,.071,.19),frame,.003)
for x,y in ((-.54,.56),(-.1,.56),(-.46,-.40),(-.14,-.40),(.08,-.30),(.48,-.30)):
    box('Carrier stand-off',(x,y,-.375),(.035,.038,.204),steel,.003)

# Service reservoir and real pipe connections behind the controls.
cyl('Expansion reservoir',(.615,-.52,.15),.153,.84,paint,'Y',64,.006)
sphere('Reservoir upper pressed cap',(.615,-.10,.15),(.153,.068,.153),paint)
sphere('Reservoir lower pressed cap',(.615,-.94,.15),(.153,.068,.153),paint)
for y in (-.77,-.26):
    torus('Reservoir mounting strap',(.615,y,.15),.155,.010,steel,'Y')
    box('Reservoir strap anchor',(.615,y,.339),(.31,.032,.18),steel,.002)
cyl('Reservoir threaded filler',(.615,.006,.15),.039,.074,brass,'Y',12,.001)
cyl('Filler cap',(.615,.047,.15),.049,.020,oxid,'Y',12,.003)
box('Reservoir batch tag',(.615,-.52,-.008),(.135,.048,.002),printlight,.001)
txt('Tank tag print','RETURN',(.615,-.52,-.010),.017,ink)

# Pump assembly, bolted to the tray on a restrained base.
box('Pump machined mounting bed',(-.23,-1.052,.04),(.54,.072,.65),paint,.009)
for x in (-.438,-.022):
    for z in (-.218,.289): fastener('Pump foundation bolt',(x,-1.011,z),.012,'Y')
for x in (-.365,-.095): box('Motor cast foot',(x,-.966,.14),(.058,.17,.34),paint,.008)
cyl('Motor barrel',(-.23,-.79,.17),.147,.48,paint,'Z',64,.008)
for i in range(16):
    a=math.tau*i/16; x=-.23+math.sin(a)*.146; y=-.79+math.cos(a)*.146
    box('Motor longitudinal cooling fin',(x,y,.16),(.012,.034,.36),paint,.002,(0,0,-math.degrees(a)))
cyl('Motor rear cap',(-.23,-.79,.417),.155,.041,frame,'Z',48,.007)
box('Motor junction box',(-.23,-.598,.22),(.155,.10,.17),frame,.009)
for x in (-.285,-.175): screw((x,-.556,.131),.0045)
cyl('Pump bearing neck',(-.23,-.79,-.103),.068,.10,oxid,'Z',40,.005)
cyl('Cast centrifugal pump volute',(-.23,-.79,-.241),.19,.22,paint,'Z',64,.018)
annulus('Pump casing split line',(-.23,-.79,-.347),.178,.152,.012,oxid)
cyl('Pump service cover',(-.23,-.79,-.360),.151,.028,paint,'Z',64,.006)
for i in range(6):
    a=math.tau*i/6; fastener('Volute cover bolt',(-.23+math.sin(a)*.164,-.79+math.cos(a)*.164,-.370),.010)
cyl('Pump axial port',(-.23,-.79,-.398),.046,.058,brass,'Z',32,.002)
flange('Pump inlet',(-.23,-.79,-.437),.069,'Z')
tube('Main supply riser',[(-.23,-.79,-.463),(-.658,-.79,-.463),(-.658,.804,-.420),(.28,.804,-.420),(.28,.35,-.420)],.036,paint,.078)
for y in (-.61,.07,.64):
    cyl('Supply union collar',(-.658,y,-.434 if y<0 else -.426),.047,.049,oxid,'Y',12,.002)
    box('Riser stand-off',(-.658,y,-.358),(.086,.045,.095),steel,.003)
flange('Top service union',(.28,.67,-.420),.067,'Y')
tube('Valve return to reservoir',[(.28,.35,-.420),(.28,.014,-.420),(.615,.014,-.420),(.615,.014,.15),(.615,-.06,.15)],.036,paint,.057)
tube('Reservoir feed to pump',[(.615,-.977,.15),(.615,-1.017,.15),(.028,-1.017,.15),(.028,-.79,-.241),(-.047,-.79,-.241)],.036,paint,.045)
flange('Bottom service union',(.38,-1.017,.15),.062,'X')
# Instrument impulse line visibly terminates at the rear of the flow instrument.
tube('Flow instrument impulse line',[(-.658,.35,-.420),(-.32,.35,-.420),(-.32,.35,-.532)],.012,brass,.025)
# One insulated conduit connects the switch box to the pump motor terminal box.
tube('Pump control conduit',[(-.30,-.55,-.441),(-.43,-.55,-.335),(-.43,-.587,.22),(-.31,-.587,.22)],.013,rubber,.045)
for z in (-.25,.13): cyl('Motor conduit clamp',(-.43,-.587,z),.018,.018,steel,'Z',20,.001)

# Side slotted protection bars guard the reservoir without hiding the service loop.
for i in range(7):
    y=-.91+i*.235; box('Right-side protective rail',(.874,y,.01),(.018,.023,.77),frame,.002)
for y in (-.96,.84):
    for z in (-.34,.34): fastener('Guard fixing',(.889,y,z),.007,'X')

# Pump selector: same neutral +Y axis, but OFF is -25 and ON +25 in this project.
pump=empty('PUMP_Switch',(-.30,-.40,-.55),assembly)
part('PUMP_Housing',pump,unity_parent='COOLING_Module/PUMP_Switch')
box('Pump cast switch enclosure',(0,0,.007),(.292,.338,.093),frame,.011)
box('Pump switch face',(0,0,-.042),(.263,.311,.016),ivory,.007)
for x in (-.108,.108):
    for y in (-.131,.131): screw((x,y,-.053),.005,15 if x<0 else -31)
cyl('Pump selector gland',(0,0,-.063),.051,.034,oxid,'Z',12,.002)
cyl('Pump selector bearing',(0,0,-.081),.039,.020,polymer,'Z',48,.002)
txt('Pump ON mark','I',(-.061,.112,-.052),.025,ink)
txt('Pump OFF mark','0',(.061,.112,-.052),.024,ink)
txt('Pump label','PUMP',(0,-.205,.053),.024,ink)
part('PUMP_Handle',pump,(0,0,-.085),unity_parent='COOLING_Module/PUMP_Switch/HandlePivot')
cyl('Selector rotor',(0,0,-.008),.033,.038,polymer,'Z',40,.003)
box('Moulded switch toggle',(0,.074,-.017),(.052,.200,.055),polymer,.009)
box('Cream switch index',(0,.146,-.0455),(.014,.027,.002),printlight,.001)

# Valve housing is visibly piped; only the wheel itself rotates.
valve=empty('FLOW_Valve',(.28,.35,-.55),assembly)
part('VALVE_Housing',valve,unity_parent='COOLING_Module/FLOW_Valve')
sphere('Cast valve bonnet',(0,0,.068),(.095,.108,.09),paint)
cyl('Valve vertical body',(0,0,.13),.056,.25,paint,'Y',48,.006)
for y in (-.123,.123): flange('Valve service flange',(0,y,.13),.075,'Y')
cyl('Brass packing nut',(0,0,-.025),.047,.086,brass,'Z',6,.003)
cyl('Valve spindle',(0,0,-.113),.022,.121,steel,'Z',32,.001)
cyl('Spindle dust seal',(0,0,-.17),.032,.024,rubber,'Z',32,.001)
box('Valve identifier backing',(0,.326,.055),(.31,.062,.004),ivory,.003)
txt('Valve identifier','FLOW VALVE',(0,.326,.052),.024,ink)
box('Valve tag stand-off',(0,.326,.088),(.07,.025,.068),steel,.002)
part('VALVE_Wheel',valve,(0,0,-.2),unity_parent='COOLING_Module/FLOW_Valve/WheelPivot')
wheel_rim()
for i in range(4):
    a=math.tau*i/4
    pts=[(.03*math.sin(a),.03*math.cos(a),.003),(.241*math.sin(a),.241*math.cos(a),0)]
    tube('Cast handwheel spoke',pts,.016,red,.025)
cyl('Wheel cast hub',(0,0,.001),.052,.062,red,'Z',48,.006)
cyl('Wheel spindle washer',(0,0,-.034),.025,.006,steel,'Z',32,.001)
cyl('Wheel securing nut',(0,0,-.042),.018,.015,brass,'Z',6,.002)
box('Wheel position index',(0,.240,-.023),(.035,.027,.003),printlight,.002)

# Flow meter uses the original needle center and leaves a full .50 x .10m text area.
gauge=empty('FLOW_Gauge',(-.32,.35,-.55),assembly)
part('FLOW_Housing',gauge,unity_parent='COOLING_Module/FLOW_Gauge')
box('Flow meter pressed casing',(0,0,-.003),(.608,.546,.108),frame,.021)
box('Flow casing mounting gasket',(0,0,.054),(.57,.51,.010),rubber,.008)
box('Flow enamel face',(0,0,-.083),(.551,.484,.008),ivory,.012)
for x in (-.290,.290): box('Flow rolled side bezel',(x,0,-.073),(.026,.53,.088),oxid,.007)
for y in (-.252,.252): box('Flow rolled end bezel',(0,y,-.073),(.567,.026,.088),oxid,.007)
for x in (-.282,.282):
    for y in (-.241,.241): screw((x,y,-.119),.0054,28)
for i in range(41):
    a=135-270*i/40; ar=math.radians(a)
    box('Flow scale graduation',(-math.sin(ar)*.185,.035+math.cos(ar)*.185,-.088),(.0022 if i%4==0 else .0012,.017 if i%4==0 else .009,.0005),ink,0,(0,0,a))
for value in (0,20,40,60,80,100):
    a=math.radians(135-270*value/100)
    txt('Flow scale number',str(value),(-math.sin(a)*.146,.035+math.cos(a)*.146,-.089),.021,ink)
txt('Flow meter unit','L/min',(0,.087,-.089),.033,ink)
txt('Flow meter marking','FLOW',(0,-.058,-.089),.018,ink)
# No static numeric readout is exported; existing TMP occupies the clear lower face.
box('Readout separator',(0,-.107,-.088),(.475,.0014,.0004),ink,0)
part('FLOW_Needle',gauge,(0,.035,-.095),unity_parent='COOLING_Module/FLOW_Gauge/NeedlePivot')
box('Flow needle',(0,.082,0),(.005,.164,.003),red,.0005)
box('Flow needle counterweight',(0,-.022,0),(.013,.033,.003),ink,.001)
cyl('Flow needle pivot cap',(0,0,-.004),.014,.009,brass,'Z',32,.001)
part('FLOW_Glass',gauge,unity_parent='COOLING_Module/FLOW_Gauge')
box('Optional replaceable flow meter lens',(0,0,-.123),(.551,.484,.0015),glass,.004)

# Compact pressure/temperature display; keep its original dark TMP on light enamel.
readout=empty('Cooling_Readout',(.28,-.2,-.55),assembly)
part('THERMAL_Housing',readout,unity_parent='COOLING_Module/Cooling_Readout')
box('Thermal instrument casing',(0,0,0),(.508,.305,.124),frame,.012)
box('Thermal light display face',(0,0,-.076),(.461,.257,.007),ivory,.006)
for x in (-.240,.240): box('Thermal display side rim',(x,0,-.065),(.023,.288,.04),oxid,.004)
for y in (-.139,.139): box('Thermal display end rim',(0,y,-.065),(.475,.022,.04),oxid,.004)
for x in (-.233,.233): screw((x,.132,-.090),.0045)
box('Thermal caption enamel tag',(0,-.166,.043),(.438,.039,.004),polymer,.003)
txt('Thermal instrument caption','PRESSURE / TEMPERATURE',(0,-.166,.040),.018,printlight)

# Authoring data and exports. Each FBX is centered on the EXISTING functional pivot.
bpy.context.view_layer.update()
manifest=dict(asset='RELAY COOLING v01',unity_modified=False,units='metres',front='Unity -Z',
    reference_scene='Assets/Scenes/Startup_Graybox.unity',reference_module_position=[-1,1.2,4],
    import_note='Children local position 0, local rotation Y 180, local scale 1; same established FBX convention as POWER. Unity import/gameplay still requires user verification.',
    live_readout_note='No fake dynamic values in exported meshes. Keep existing TMP objects.',parts=[],materials=material_specs)
mesh_parts={}
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
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.01); bpy.ops.object.mode_set(mode='OBJECT')
            for other in selected: other.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join()
    ob=bpy.context.object; ob.name=name+'_EXPORT'; scene.cursor.location=pivot.matrix_world.translation
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    # Resolve all normals after the authoring coordinate reflection.
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    saved=ob.matrix_world.copy(); ob.matrix_world=Matrix.Identity(4)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'exports',name+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    bounds=[[min((P@p.co)[i] for p in ob.data.vertices),max((P@p.co)[i] for p in ob.data.vertices)] for i in range(3)]
    ob.matrix_world=saved; ob.hide_render=True; ob.hide_set(True); mesh_parts[name]=ob
    manifest['parts'].append(dict(name=name,file='exports/'+name+'.fbx',triangles=sum(len(p.vertices)-2 for p in ob.data.polygons),vertices=len(ob.data.vertices),materials=[m.name for m in ob.data.materials],bounds_unity_local=bounds,**mount_spec[name]))
manifest['triangles_total']=sum(p['triangles'] for p in manifest['parts'])
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,indent=2)

# Presentation poses are separate from neutral exported art. Everything starts OFF.
for name,angle in (('PUMP_Handle',-25),('FLOW_Needle',135)):
    parts[name].rotation_mode='QUATERNION'; parts[name].rotation_quaternion=rot((0,0,angle))
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=1200; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
scene.world.use_nodes=True; bg=scene.world.node_tree.nodes['Background']; bg.inputs[0].default_value=(.20,.21,.20,1); bg.inputs[1].default_value=.42
scene.view_settings.view_transform='AgX'
floormat=mat('PREVIEW_ONLY_Concrete','50554F',0,.85)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.202)); ob=bpy.context.object; ob.name='Preview floor (not exported)'; ob.data.materials.append(floormat); move(ob,studio)
def aim(ob,at): ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color=(1,1,1)):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=loc; aim(o,(0,-.12,0))
area('Broad workshop window',(-3,-4,4),800,3.4,(1,.95,.87))
area('Ceiling bounce',(2,.7,4),900,3,(.90,.96,1))
area('Front reflection card',(4,-3,1),230,2.5)
camera=bpy.data.objects.new('REVIEW camera (not exported)',bpy.data.cameras.new('Review camera')); studio.objects.link(camera)
camera.location=(3.8,-7.8,2.3); aim(camera,(0,-.04,0)); camera.data.type='ORTHO'; camera.data.ortho_scale=3.38; scene.camera=camera
scene.render.image_settings.file_format='PNG'
# Example dynamic labels are PREVIEW ONLY and never copied to any FBX.
for name,body,parent,loc,size in (
    ('Preview of existing Unity flow text','FLOW: 0 L/min\nVALVE: 0%',gauge,(0,-.17,-.095),.036),
    ('Preview of existing Unity thermal text','PRESS: 0 kPa\nTEMP: 100.0 C',readout,(0,0,-.082),.032)):
    txt(name,body,loc,size,ink,parent=parent,collection=studio)
# Convert lettering to meshes to keep the deliverable independent of installed fonts.
bpy.ops.object.select_all(action='DESELECT'); texts=[o for o in source.objects if o.type=='FONT']
for ob in texts: ob.select_set(True)
if texts: bpy.context.view_layer.objects.active=texts[0]; bpy.ops.object.convert(target='MESH')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL'; a.spaces.active.overlay.show_overlays=False
            a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT'); assembly.select_set(True); bpy.context.view_layer.objects.active=assembly
bpy.context.preferences.filepaths.save_version=0
blendfile=os.path.join(OUT,'RELAY_COOLING_v01.blend')
bpy.ops.wm.save_as_mainfile(filepath=blendfile)
print('COOLING_BLEND_READY',blendfile,flush=True)
if '--skip-renders' in sys.argv:
    print('COOLING_BUILD_COMPLETE',manifest['triangles_total'],flush=True)
    sys.exit(0)
scene.render.filepath=os.path.join(OUT,'previews','COOLING_hero.png'); bpy.ops.render.render(write_still=True)
camera.location=(0,-7,.14); aim(camera,(0,-.10,0)); camera.data.ortho_scale=2.92
scene.render.resolution_x=1200; scene.render.resolution_y=1500
scene.render.filepath=os.path.join(OUT,'previews','COOLING_front.png'); bpy.ops.render.render(write_still=True)
camera.location=(2.2,-5,1.25); aim(camera,(.02,-.59,.3)); camera.data.ortho_scale=1.53
scene.render.resolution_x=1200; scene.render.resolution_y=1000
scene.render.filepath=os.path.join(OUT,'previews','COOLING_controls.png'); bpy.ops.render.render(write_still=True)
print('COOLING_BUILD_COMPLETE',manifest['triangles_total'],flush=True)
