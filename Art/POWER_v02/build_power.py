"""RELAY POWER V02. Standalone Blender authoring; never touches Unity files.
All dimensions below use Unity-style metres: X right, Y up, front is -Z.
"""
import bpy, math, os, json, struct, zlib
import numpy as np
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__))
for folder in ('exports', 'textures', 'previews'):
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
P = Matrix(((1,0,0), (0,0,1), (0,1,0)))
def v(u): return P @ Vector(u)
def rot(u): return (P @ Euler(tuple(math.radians(a) for a in u), 'XYZ').to_matrix() @ P).to_quaternion()
def linear(a):
    a=np.asarray(a); return np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)
def rgb(code): return np.array([int(code[i:i+2],16)/255 for i in (0,2,4)])
scene=bpy.context.scene
source=bpy.data.collections.new('01_EDITABLE_PARTS'); scene.collection.children.link(source)
exports=bpy.data.collections.new('02_EXPORT_MESHES'); scene.collection.children.link(exports)
studio=bpy.data.collections.new('03_PREVIEW_ONLY'); scene.collection.children.link(studio)
def move_collection(ob, coll):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)
def material(name, color, metal=0, rough=.5):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    mat.diffuse_color=(*linear(rgb(color)),1)
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=mat.diffuse_color
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    return mat
shell=material('RLY02_ShellPaint','59665F',0,.57)
fascia=material('RLY02_FasciaPaint','A3A496',0,.60)
cast=material('RLY02_CastIron','343B36',.25,.65)
steel=material('RLY02_Steel','77796E',.85,.40)
darksteel=material('RLY02_OxidizedSteel','3D403B',.65,.58)
black=material('RLY02_BlackPolymer','252821',0,.37)
rubber=material('RLY02_Gasket','141813',0,.79)
red=material('RLY02_RedGrip','76372B',0,.43)
cream=material('RLY02_DialEnamel','D2CBAB',0,.70)
ink=material('RLY02_Ink','262A22',0,.75)
ivory=material('RLY02_IvoryInk','D5D1B8',0,.58)
label=material('RLY02_InspectionPaper','C1B98A',0,.88)
brass=material('RLY02_BrassContact','776E49',.75,.50)

# A planar, location-aware finish: sparse chips at fasteners and panel margins.
# Blender image float buffers are linear; conversion prevents washed-out colour.
def panel_finish():
    n=2048; rng=np.random.default_rng(604)
    yy,xx=np.mgrid[0:n,0:n].astype(np.float32); x=(xx/(n-1)-.5)*1.714; y=(yy/(n-1)-.5)*2.254
    edge=np.minimum(.857-np.abs(x),1.127-np.abs(y))
    coarse=rng.normal(0,1,(64,64)).repeat(32,0).repeat(32,1)
    for _ in range(8): coarse=(coarse+np.roll(coarse,7,0)+np.roll(coarse,7,1)+np.roll(coarse,-7,0)+np.roll(coarse,-7,1))/5
    fine=rng.random((n,n))
    grime=np.exp(-np.maximum(edge,0)/.014)*.07
    chips=(edge<.0025)&(fine>.58)&(coarse>.0)
    for bx in (-.805,.805):
        for by in (-1.035,.99):
            d=np.sqrt((x-bx)**2+(y-by)**2)
            grime+=.13*np.exp(-d/.025)
            chips |= (d>.012)&(d<.0145)&(fine>.45)
    # A few short tool marks, confined to the lower service edge.
    for _ in range(22):
        cx=float(rng.uniform(-.74,.74)); cy=float(rng.uniform(-1.10,-1.04))
        length=float(rng.uniform(.003,.018)); width=float(rng.uniform(.0006,.0014))
        chips |= (np.abs(x-cx)<length)&(np.abs(y-cy)<width)&(fine>.16)
    pixels=np.ones((n,n,4),np.float32)
    colour=np.clip(rgb('A3A496')[None,None,:]-grime[:,:,None]+coarse[:,:,None]*.0015,0,1)
    colour[chips]=rgb('54574E'); pixels[:,:,:3]=colour
    def image_file(name,data,noncolor=False):
        # Write known sRGB bytes for colour and raw channel bytes for data maps.
        # Reloading gives Blender the same interpretation that Unity will use.
        path=os.path.join(OUT,'textures',name+'.png')
        raw=np.rint(np.clip(data,0,1)*255).astype(np.uint8)[::-1]
        rows=b''.join(b'\x00'+row.tobytes() for row in raw)
        def chunk(kind,payload):
            return struct.pack('!I',len(payload))+kind+payload+struct.pack('!I',zlib.crc32(kind+payload)&0xffffffff)
        with open(path,'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',n,n,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows,7))+chunk(b'IEND',b''))
        im=bpy.data.images.load(path,check_existing=False)
        im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
        if noncolor: im.alpha_mode='CHANNEL_PACKED'
        return im
    bc=image_file('POWER_Fascia_BaseColor',pixels)
    packed=np.zeros((n,n,4),np.float32); packed[:,:,:3]=chips[:,:,None]*.72
    packed[:,:,3]=np.clip(.40+coarse*.003-grime*.6,0,1); packed[chips,3]=.30
    ms=image_file('POWER_Fascia_MetallicSmoothness',packed,True)
    nodes=fascia.node_tree.nodes; links=fascia.node_tree.links; bs=nodes.get('Principled BSDF')
    a=nodes.new('ShaderNodeTexImage'); a.image=bc; links.new(a.outputs['Color'],bs.inputs['Base Color'])
    b=nodes.new('ShaderNodeTexImage'); b.image=ms
    separate=nodes.new('ShaderNodeSeparateColor'); links.new(b.outputs['Color'],separate.inputs['Color'])
    links.new(separate.outputs['Red'],bs.inputs['Metallic'])
    inv=nodes.new('ShaderNodeMath'); inv.operation='SUBTRACT'; inv.inputs[0].default_value=1
    links.new(b.outputs['Alpha'],inv.inputs[1]); links.new(inv.outputs[0],bs.inputs['Roughness'])
panel_finish()

parts={}; active=None
def empty(name,location=(0,0,0),parent=None):
    ob=bpy.data.objects.new(name,None); source.objects.link(ob)
    ob.parent=parent; ob.location=v(location); ob.empty_display_size=.055; return ob
assembly=empty('RELAY_POWER_V02')
def part(name,parent,location=(0,0,0)):
    global active
    ob=empty(name,location,parent); ob['unity_local_position']=list(location)
    parts[name]=ob; active=ob; return ob
def register(ob,name,loc,mat):
    move_collection(ob,source); ob.name=name; ob.parent=active; ob.location=v(loc)
    ob.data.materials.append(mat); return ob
def bevel(ob,width=.002,segments=2):
    b=ob.modifiers.new('Formed edge radius','BEVEL'); b.width=width; b.segments=segments
    # Keep the surface material on the radius. No automatic exposed-metal rim.
    b.material=-1
    no=ob.modifiers.new('Corner normals','WEIGHTED_NORMAL'); no.keep_sharp=True
def box(name,loc,size,mat,bev=.002,angles=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob=register(bpy.context.object,name,loc,mat); ob.scale=v(size)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rot(angles)
    if bev: bevel(ob,bev)
    return ob
def cyl(name,loc,r,depth,mat,axis='Z',verts=32,bev=.001):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth)
    ob=register(bpy.context.object,name,loc,mat)
    ob.rotation_mode='QUATERNION'
    ob.rotation_quaternion=Vector((0,0,1)).rotation_difference(v({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]))
    if bev: bevel(ob,min(bev,r*.1),2)
    for p in ob.data.polygons: p.use_smooth=len(p.vertices)==4
    return ob
font=bpy.data.fonts.load('C:/Windows/Fonts/bahnschrift.ttf')
def txt(name,body,loc,size,mat=ink,align='CENTER',angles=(0,0,0)):
    data=bpy.data.curves.new(name,'FONT'); data.body=body; data.font=font
    data.size=size; data.align_x=align; data.align_y='CENTER'; data.extrude=0; data.resolution_u=2
    ob=bpy.data.objects.new(name,data); source.objects.link(ob); ob.parent=active
    ob.location=v(loc); ob.rotation_euler=(math.pi/2,0,0)
    if angles != (0,0,0): ob.rotation_euler.rotate(Euler(tuple(math.radians(a) for a in angles)))
    data.materials.append(mat); return ob
def screw(x,y,z,r=.008,angle=20):
    cyl('Slotted steel fastener',(x,y,z),r,.004,steel,verts=16)
    box('Recessed screw slot',(x,y,z-.0021),(r*1.45,.0015,.0004),ink,0,(0,0,angle))
def cut_box(target,name,loc,size,bev=.003):
    tool=box(name,loc,size,rubber,bev)
    bpy.context.view_layer.objects.active=tool; tool.select_set(True)
    # Apply tool bevel, so the opening has a stamped rounded end.
    for mod in list(tool.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active=target
    mod=target.modifiers.new(name,'BOOLEAN'); mod.operation='DIFFERENCE'; mod.object=tool
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool,do_unlink=True)
def planar_uv(ob,width,height):
    uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='UVMap')
    for polygon in ob.data.polygons:
        for i in polygon.loop_indices:
            co=ob.data.vertices[ob.data.loops[i].vertex_index].co
            uv.data[i].uv=(co.x/width+.5,co.z/height+.5)
def ring(name,loc,outer,inner,depth,mat):
    # Real open annulus, not a stack of cylinders hiding the face underneath.
    verts=[]; faces=[]; n=64
    for z,r in ((-depth/2,outer),(-depth/2,inner),(depth/2,outer),(depth/2,inner)):
        for i in range(n):
            a=i*2*math.pi/n; verts.append(tuple(v((r*math.cos(a),r*math.sin(a),z))))
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); source.objects.link(ob); ob.parent=active; ob.location=v(loc)
    me.materials.append(mat); bevel(ob,.001,2); return ob

# Folded enclosure, fixed instrument panel, independent right service cover.
part('POWER_Cabinet',assembly)
box('Rear sheet',(0,0,.483),(1.78,2.37,.022),shell,.008)
box('Left folded side',(-.885,0,0),(.025,2.37,.965),shell,.008)
side=box('Right folded side',(.885,0,0),(.025,2.37,.965),shell,0)
cut_box(side,'Service aperture',(.885,-.04,.08),(.07,1.80,.61),.012)
bevel(side,.006)
box('Top folded cap',(0,1.185,0),(1.8,.030,.99),shell,.008)
box('Bottom fold',(0,-1.165,0),(1.8,.035,.99),shell,.005)
box('Recessed plinth',(0,-1.14,.035),(1.66,.12,.84),rubber,.003)
# Open front flanges and rear baffle visible through actual ventilation slots.
for x in (-.86,.86): box('Panel fixing flange',(x,0,-.463),(.043,2.33,.045),shell,.002)
box('Top front flange',(0,1.14,-.462),(1.74,.055,.045),shell,.002)
box('Lower front flange',(0,-1.13,-.462),(1.74,.055,.045),shell,.002)
panel=box('Fixed instrument fascia',(0,0,-.5),(1.714,2.254,.028),fascia,0)
for i in range(6):
    y=-.865-i*.032
    cut_box(panel,'Punched ventilation',(-.34,y,-.5),(.54,.013,.08),.005)
    box('Pressed louver lip',(-.34,y+.008,-.518),(.524,.017,.012),shell,.002,(16,0,0))
planar_uv(panel,1.714,2.254); bevel(panel,.003)
box('Vent dust baffle',(-.34,-.946,-.435),(.62,.235,.018),rubber,.002)
for x in (-.805,.805):
    for y in (-1.035,.99): screw(x,y,-.517,.011,18 if x<0 else -39)
# Header and markings are restrained, with room left for the instruments.
box('Engraved nameplate',(-.36,.945,-.519),(.70,.19,.008),cast,.003)
txt('Nameplate title','POWER',(-.665,.977,-.524),.053,ivory,'LEFT')
txt('Nameplate rating','DC DISTRIBUTION   /   100 V',(-.665,.918,-.524),.016,ivory,'LEFT')
for x in (-.683,-.037): screw(x,.947,-.527,.005,-10)
txt('Fascia unit number','04',(.64,.97,-.515),.078,ink)
txt('Fascia unit type','PWR UNIT',(.64,.902,-.515),.014,ink)
txt('Meter caption','BUS VOLTAGE',(-.3,.795,-.516),.026,ink)
box('Service notice',(-.34,-.723,-.518),(.42,.105,.002),label,.001,(0,0,-1.7))
txt('Notice top','ISOLATE BEFORE SERVICE',(-.34,-.708,-.521),.014,ink)
txt('Notice bottom','INSPECTED  /  14.06',(-.34,-.743,-.521),.011,ink)
txt('Cabinet serial','RELAY     P-04   /   018',(-.64,-1.077,-.516),.012,ink,'LEFT')
# Real removable side cover; fasteners, hinges and latch belong to this cover.
cover=box('Side maintenance cover',(.905,-.04,.08),(.018,1.87,.68),shell,0)
for i in range(7):
    y=.47-i*.055
    cut_box(cover,'Side punched slot',(.905,y,.08),(.075,.020,.46),.005)
    box('Side formed louver',(.919,y+.012,.08),(.018,.027,.446),shell,.003,(0,0,-15))
bevel(cover,.006)
box('Side internal baffle',(.858,.302,.08),(.012,.5,.50),rubber,.002)
for y in (-.69,.64):
    box('Side hinge leaf',(.922,y,.39),(.016,.11,.07),shell,.002)
    cyl('Service hinge pin',(.938,y,.416),.011,.132,steel,'Y',20)
cyl('Quarter turn latch',(.925,-.12,-.193),.025,.014,darksteel,'X',24)
box('Latch thumb tab',(.943,-.12,-.193),(.023,.065,.018),steel,.003)
# Cable-entry ports face downward and end at the enclosure instead of hanging.
for x in (-.5,.1):
    cyl('Capped conduit gland',(x,-1.179,.29),.037,.042,darksteel,'Y',12)

# Compact rotary AUX: threaded mounting collar, moulded handle, clear 0/I marks.
aux=empty('AUX_Switch',(-.3,-.4,-.55),assembly)
part('AUX_Housing',aux)
box('Aux escutcheon',(0,0,.028),(.28,.31,.024),cast,.010)
cyl('Aux threaded collar',(0,0,-.006),.067,.043,steel,verts=12)
cyl('Aux black bezel',(0,0,-.045),.056,.044,black,verts=48)
for x in (-.11,.11): screw(x,-.12,.012,.006,35)
txt('Aux OFF','0',(-.067,.115,.013),.026,ivory)
txt('Aux ON','I',(.067,.115,.013),.025,ivory)
txt('Aux function','AUX POWER',(0,-.216,.033),.024,ink)
part('AUX_Handle',aux,(0,0,-.085))
cyl('Aux selector root',(0,0,.003),.039,.057,black,verts=32)
box('Aux moulded paddle',(0,.052,-.020),(.044,.13,.040),black,.009)
box('Aux pointer insert',(0,.091,-.042),(.009,.031,.002),ivory,.001)

# MAIN uses a cast clevis and a forged shaft; no slab identical to the AUX.
lever=empty('MAIN_Lever',(.28,-.75,-.55),assembly)
part('MAIN_Housing',lever)
box('Main cast backplate',(0,0,.019),(.36,.72,.046),cast,.014)
box('Main travel recess',(0,0,-.008),(.115,.565,.014),rubber,.003)
for x in (-.14,.14):
    for y in (-.303,.303): screw(x,y,-.008,.010,45)
for x in (-.079,.079):
    box('Forged bearing cheek',(x,0,-.077),(.035,.112,.14),cast,.014)
    cyl('Exposed axle cap',(x+(-.023 if x<0 else .023),0,-.1),.028,.009,steel,'X',24)
cyl('Static cross pin',(0,0,-.1),.025,.183,darksteel,'X',32)
txt('Lever off marking','OFF',(-.123,.20,-.007),.019,ivory)
txt('Lever on marking','ON',(-.123,-.20,-.007),.019,ivory)
txt('Main function','MAIN',(0,.43,.033),.026,ink)
part('MAIN_Handle',lever,(0,0,-.1))
cyl('Main rotating hub',(0,0,0),.037,.112,darksteel,'X',32)
box('Forged lever arm',(0,.18,0),(.031,.36,.038),steel,.007)
cyl('Moulded red crossbar',(0,.36,0),.046,.28,red,'X',48,bev=.009)
for x in (-.144,.144): cyl('Recessed grip end',(x,.36,0),.035,.005,black,'X',32)
for x in (-.113,.113): cyl('Grip moulding collar',(x,.36,0),.048,.013,red,'X',48,bev=.002)

def fluted_knob(name):
    n=96; verts=[]; faces=[]
    profile=[(.032,.101),(.023,.112),(-.039,.112),(-.052,.097)]
    for z,r in profile:
        for i in range(n):
            a=2*math.pi*i/n; groove=.004*(.5+.5*math.cos(a*24))
            verts.append(tuple(v(((r-groove)*math.cos(a),(r-groove)*math.sin(a),z))))
    for k in range(len(profile)-1):
        for i in range(n): j=(i+1)%n; faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces.extend([tuple(reversed(range(n))),tuple(range((len(profile)-1)*n,len(profile)*n))])
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); source.objects.link(ob); ob.parent=active; me.materials.append(black)
    # Winding may differ under the Unity-to-Blender reflection; recalculate.
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.use_smooth=len(p.vertices)==4
    return ob
def dial(name,location,wing=False):
    ctrl=empty(name,location,assembly); part(name+'_Housing',ctrl)
    cyl('Inset dial back',(0,0,.012),.176,.062,cast,verts=64)
    cyl('Dial graduated face',(0,0,-.024),.166,.010,cream,verts=64)
    ring('Thin rolled bezel',(0,0,-.031),.175,.164,.014,darksteel)
    for i in range(21):
        a=135-270*i/20; r=.150; ar=math.radians(a)
        box('Engraved dial graduation',(-math.sin(ar)*r,math.cos(ar)*r,-.032),(.0018,.016 if i%2==0 else .008,.0005),ink,0,(0,0,a))
    for value in (0,50,100):
        a=math.radians(135-270*value/100)
        txt('Dial scale number',str(value),(-math.sin(a)*.193,math.cos(a)*.193,.033),.019,ink)
    txt('Dial function','LOAD BALANCE' if wing else 'VOLTAGE',(0,-.225,.033),.024,ink)
    part(name+'_Knob',ctrl,(0,0,-.1))
    cyl('Dial spindle',(0,0,.052),.023,.058,darksteel,verts=24)
    if not wing:
        fluted_knob('One piece fluted knob')
        cyl('Recessed knob face',(0,0,-.055),.083,.008,black,verts=64)
        box('Inlaid voltage index',(0,.062,-.060),(.009,.038,.0015),ivory,.0008)
    else:
        cyl('Balance moulded boss',(0,0,.008),.086,.054,black,verts=48,bev=.004)
        box('Balance wing grip',(0,0,-.032),(.057,.217,.053),black,.012)
        box('Balance index insert',(0,.086,-.060),(.010,.028,.002),ivory,.001)
    return ctrl
dial('VOLTAGE',(.28,.45,-.55))
dial('BALANCE',(.28,-.05,-.55),True)

# Thin pressed meter rim. The transparent lens is a separate optional export.
gauge=empty('VOLTAGE_Gauge',(-.3,.45,-.55),assembly)
part('Gauge_Housing',gauge)
box('Meter rear casing',(0,0,-.012),(.60,.54,.11),cast,.012)
box('Meter cream face',(0,0,-.080),(.534,.474,.006),cream,.008)
for x in (-.282,.282): box('Meter folded side',(x,0,-.085),(.030,.524,.07),black,.009)
for y in (-.252,.252): box('Meter folded end',(0,y,-.085),(.556,.030,.07),black,.008)
for x in (-.278,.278):
    for y in (-.248,.248): screw(x,y,-.123,.006,15)
for i in range(51):
    a=135-270*i/50; ar=math.radians(a); length=.019 if i%5==0 else .010
    box('Meter scale stroke',(-math.sin(ar)*.190,.035+math.cos(ar)*.190,-.084),(.002 if i%5==0 else .001,length,.0005),ink,0,(0,0,a))
for value in range(0,101,20):
    a=math.radians(135-270*value/100)
    txt('Meter scale numeral',str(value),(-math.sin(a)*.145,.035+math.cos(a)*.145,-.085),.023,ink)
txt('Meter unit','V',(0,.096,-.085),.043,ink)
txt('Meter class','DC   1.5',(0,-.073,-.085),.015,ink)
box('Live readout well',(0,-.174,-.085),(.414,.055,.002),rubber,.001)
txt('Meter serial','M-118   /   OUTPUT',(0,-.220,-.085),.011,ink)
part('Gauge_Needle',gauge,(0,.035,-.095))
box('Painted needle',(0,.086,0),(.004,.172,.003),red,.0006)
box('Needle counterweight',(0,-.023,0),(.015,.034,.003),ink,.002)
cyl('Needle brass pivot',(0,0,-.002),.014,.008,brass,verts=32)
glass=material('RLY02_MeterGlass','F0F1E9',0,.025)
gbs=glass.node_tree.nodes.get('Principled BSDF'); gbs.inputs['Transmission Weight'].default_value=1.0; gbs.inputs['IOR'].default_value=1.45
part('Gauge_Glass',gauge)
box('Replaceable meter lens',(0,0,-.114),(.528,.468,.002),glass,.006)

# Duplicate for FBX consolidation. Editable primitives, text and modifiers remain.
mesh_parts={}; manifest={'asset':'RELAY POWER v02','units':'meters','parts':[],
    'unity_modified':False,'coordinate_input':'Unity XYZ; front -Z',
    'note':'FBX files are neutral at their functional pivots. Unity import not tested.'}
for name,pivot in parts.items():
    bpy.context.view_layer.update(); copies=[]
    for original in list(pivot.children):
        if original.type not in ('MESH','FONT','CURVE'): continue
        dupe=original.copy(); dupe.data=original.data.copy(); exports.objects.link(dupe)
        dupe.parent=None; dupe.matrix_world=original.matrix_world.copy(); copies.append(dupe)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in copies: ob.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.convert(target='MESH')
    # Curves/letters lack UVs. Unwrap only those; preserve the fascia planar atlas.
    for ob in list(bpy.context.selected_objects):
        if len(ob.data.uv_layers)==0:
            bpy.context.view_layer.objects.active=ob
            others=[o for o in bpy.context.selected_objects if o!=ob]
            for o in others: o.select_set(False)
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=.01); bpy.ops.object.mode_set(mode='OBJECT')
            for o in others: o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join()
    me=bpy.context.object; me.name=name+'_EXPORT'
    scene.cursor.location=pivot.matrix_world.translation; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    saved=me.matrix_world.copy(); me.matrix_world=Matrix.Identity(4)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'exports',name+'.fbx'),use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
        add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    me.matrix_world=saved; me.hide_render=True; me.hide_set(True); mesh_parts[name]=me
    manifest['parts'].append({'name':name,'triangles':sum(len(p.vertices)-2 for p in me.data.polygons),
        'unity_parent_local_position':list(pivot['unity_local_position']),'file':'exports/'+name+'.fbx'})
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,indent=2)
for name,angles in {'AUX_Handle':(0,0,25),'MAIN_Handle':(-25,0,0),'VOLTAGE_Knob':(0,0,0),
                    'BALANCE_Knob':(0,0,135),'Gauge_Needle':(0,0,135)}.items():
    parts[name].rotation_mode='QUATERNION'; parts[name].rotation_quaternion=rot(angles)

scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=1200; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
scene.world.use_nodes=True; bg=scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value=(.20,.20,.18,1); bg.inputs[1].default_value=.40
scene.view_settings.view_transform='AgX'
floor=material('PreviewConcrete','555750',0,.85)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.205))
ob=bpy.context.object; ob.name='Preview floor'; ob.data.materials.append(floor); move_collection(ob,studio)
def aim(ob,at): ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color=(1,1,1)):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=color
    ob=bpy.data.objects.new(name,d); studio.objects.link(ob); ob.location=loc; aim(ob,(0,-.15,0))
area('Broad workshop window',(-3,-4,4),750,3.6,(1,.95,.86))
area('Ceiling bounce',(2,.6,4),900,3,(.90,.95,1))
area('Soft front bounce',(4,-3,.9),160,2.5)
cam=bpy.data.cameras.new('Review camera'); camera=bpy.data.objects.new('Review camera',cam); studio.objects.link(camera)
camera.location=(3.6,-7.8,2.15); aim(camera,(0,-.08,0)); cam.type='ORTHO'; cam.ortho_scale=3.45
scene.camera=camera; scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.path.join(OUT,'previews','POWER_v02_hero.png')
bpy.context.preferences.filepaths.save_version=0
for im in bpy.data.images:
    if im.filepath: im.pack()
# Convert the editable font shapes to meshes before saving; do not pack font files.
bpy.ops.object.select_all(action='DESELECT')
textobs=[ob for ob in source.objects if ob.type=='FONT']
for ob in textobs: ob.select_set(True)
if textobs:
    bpy.context.view_layer.objects.active=textobs[0]; bpy.ops.object.convert(target='MESH')
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v02.blend'))
bpy.ops.render.render(write_still=True)
camera.location=(0,-7,.10); aim(camera,(0,-.5,0)); cam.ortho_scale=2.75
scene.render.resolution_x=1100; scene.render.resolution_y=1400
scene.render.filepath=os.path.join(OUT,'previews','POWER_v02_front.png'); bpy.ops.render.render(write_still=True)
print('POWER_V02_COMPLETE',OUT)
