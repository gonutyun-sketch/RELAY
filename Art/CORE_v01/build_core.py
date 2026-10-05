"""Build RELAY CORE art outside Unity. Metre units, centre-pivot reactor.
No Unity file, asset, importer, scene, or running application is changed.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geometry import *

RUNTIME_ROOT=Path(r'C:\Users\gonut\School_p2')
# Fresh read-only baseline, never the older October 4 baseline.
baseline_files=[RUNTIME_ROOT/'Assets/Scenes/Startup_Graybox.unity']
baseline_files+=list((RUNTIME_ROOT/'Assets/_STARTUP/Scripts').glob('*'))
baseline_files+=list((RUNTIME_ROOT/'ProjectSettings').glob('*'))
baseline={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline_files if p.is_file()}
with open(os.path.join(OUT,'checks','authoring_baseline.json'),'w',encoding='utf-8') as f: json.dump(baseline,f,indent=2)

# A separate console preserves the already working control positions exactly.
cabinet=empty('CONTROL_CONSOLE',(2.55,-.55,-.10),assembly)
part('CORE_Cabinet',cabinet,unity_parent='Environment/CORE_Module')
box('Cabinet rear shell',(0,0,.478),(1.75,2.30,.044),paint,.008)
for x in (-.873,.873):
    box('Folded enclosure side',(x,0,0),(.047,2.32,.956),paint,.01)
    box('Front jamb',(x,0,-.466),(.044,2.30,.064),frame,.004)
for y in (-1.168,1.168): box('Folded cabinet cap',(0,y,0),(1.80,.058,1.0),paint,.008)
box('Front recess',(0,0,-.464),(1.714,2.24,.05),rubber,.004)
box('Control mounting face',(0,-.018,-.482),(1.69,1.61,.04),ivory,.008)
box('Upper service cover',(0,.965,-.480),(1.69,.322,.042),paint,.004)
box('Lower status backing',(0,-.925,-.481),(1.69,.272,.042),ivory,.004)
box('Lower folded lip',(0,-1.102,-.475),(1.69,.045,.041),frame,.003)
for x in (-.813,.813):
    for y in (-1.02,-.76,.755,1.08): screw((x,y,-.505),.005,24)
box('Plain screwed nameplate',(-.44,.978,-.505),(.39,.105,.006),frame,.002)
txt('Cabinet identity','CORE',(-.44,.978,-.509),.041,printlight)
for x in (-.61,-.27): screw((x,.978,-.51),.003,18)
txt('Small cabinet index','07',(.739,.955,-.506),.034,printlight)
for x in (-.878,.878):
    for y in (-.90,.02,.90):
        cyl('Side panel captive screws',(x,y,.30),.007,.004,steel,'X',12,.0004)
# Ventilation belongs to the lower rear, not across live controls.
for i in range(9):
    box('Side ventilation dark slot',(.899,-.56+i*.065,.17),(.002,.021,.37),ink,.003)
    box('Side ventilation folded lip',(.902,-.545+i*.065,.17),(.009,.014,.38),paint,.002)
box('Console rear wiring trunk',(0,-.43,.521),(.31,1.17,.044),frame,.006)
for x in (-.17,.17): tube('Rear cable gland',[(x,-1.15,.27),(x,-1.07,.40),(x,-.94,.46)],.032,rubber,.05)

lever=empty('START_Lever',(0,-.2,-.55),cabinet)
part('START_Housing',lever,unity_parent='Environment/CORE_Module/START_Lever')
box('Starter enamel mounting plate',(0,0,.016),(.414,.828,.078),ivory,.01)
box('Starter mechanical housing',(0,0,-.035),(.236,.224,.060),frame,.014)
for x in (-.095,.095):
    box('Hinge bearing cheek',(x,0,-.096),(.04,.094,.104),oxid,.012)
    cyl('Hinge end cap',(x*1.24,0,-.10),.031,.008,steel,'X',32,.001)
for x in (-.177,.177):
    for y in (-.371,.371): screw((x,y,-.025),.006,18)
txt('Starter upper marking','OFF',(0,.289,-.025),.030,ink)
txt('Starter lower marking','START',(0,-.295,-.025),.032,ink)
for y in (-.329,.326): box('End position registration',(0,y,-.025),(.043,.003,.001),ink,0)
handlepivot=empty('HandlePivot',(0,0,-.10),lever)
part('START_Handle',handlepivot,unity_parent='Environment/CORE_Module/START_Lever/HandlePivot')
cyl('Lever hinge pin',(0,0,0),.031,.149,steel,'X',32,.001)
box('Forged lever stem',(0,.184,0),(.054,.319,.042),steel,.007)
box('Bakelite grip',(0,.360,0),(.276,.086,.094),polymer,.014)
box('Grip center insert',(0,.360,-.0475),(.10,.025,.002),ink,.003)
for x in (-.117,-.097,.097,.117): box('Grip mould seam',(x,.360,-.046),(.0015,.054,.001),rubber,.0004)

gauge=empty('Startup_Gauge',(-.12,.55,-.55),cabinet)
part('STARTUP_GaugeHousing',gauge,unity_parent='Environment/CORE_Module/Startup_Gauge')
box('Progress meter rear case',(0,0,.019),(1.112,.253,.080),frame,.006)
# The actual Unity Track/Fill remain at Z-.067/-.08, in this open aperture.
for x in (-.538,.538): box('Progress meter bezel end',(x,0,-.064),(.046,.168,.062),oxid,.005)
for y in (-.083,.083): box('Progress meter bezel rail',(0,y,-.064),(1.031,.047,.062),oxid,.003)
for x in (-.537,.537):
    for y in (-.099,.099): screw((x,y,-.097),.0037,25)
for i in range(11): box('Startup progress graduation',(-.49+i*.098,.106,-.023),(.0015,.009 if i%5 else .014,.001),printlight,0)
txt('Progress function label','STARTUP',(-.12,.191,-.034),.033,ink)

indicator_roots={}
for name,pos,size,label in [
 ('HEAT',(.67,.55,-.55),(.253,.253),'HIGH TEMP'),
 ('COLD',(.67,.15,-.55),(.253,.253),'LOW TEMP'),
 ('STARTUP',(-.55,-.55,-.55),(.372,.372),'RUN')]:
    indicator=empty(name+'_Indicator',pos,cabinet); indicator_roots[name]=indicator
    part(name+'_Housing',indicator,unity_parent='Environment/CORE_Module/'+name+'_Indicator')
    box(label+' enclosure',(0,0,.015),(size[0],size[1],.076),ivory,.009)
    for x in (-.088,.088): box(label+' bezel side',(x,.025,-.059),(.020,.105,.057),oxid,.004)
    for y in (-.020,.070): box(label+' bezel edge',(0,y,-.059),(.156,.017,.057),oxid,.003)
    txt(label+' legend',label,(0,-.073,-.025),.022 if name!='STARTUP' else .032,ink)
    for x in (-size[0]*.40,size[0]*.40): screw((x,-size[1]*.38,-.024),.004,20)

# Reactor coordinates have their origin at the centre of the old 3x3.5x3 cube.
# Source presentation remains centred on this reactor; the separate console is aside.
reactor=empty('REACTOR',parent=assembly)
containment=part('CORE_Containment',reactor,unity_parent='Environment/Core_Block')
box('Protected machine footprint',(0,-1.685,0),(2.992,.130,2.992),frame,.032)
box('Recessed maintenance deck',(0,-1.602,0),(2.89,.035,2.89),oxid,.020)
# A circular deck on a square plinth avoids a misleading walkable corner inside the old box collider.
for a in range(4):
    ang=math.radians(a*90)
    x,z=math.sin(ang)*1.447,math.cos(ang)*1.447
    box('Deck edge angle',(x,-1.56,z),(2.77,.058,.035),steel,.003,(0,a*90,0))
for i in range(-17,18):
    x=i*.078
    available=math.sqrt(max(0,1.37**2-x*x))
    blocked=math.sqrt(max(0,1.065**2-x*x)) if abs(x)<1.065 else 0
    if available-blocked<.04: continue
    for sign in (-1,1):
        length=available-blocked
        box('Open deck grating bar',(x,-1.569,sign*(available+blocked)/2),(.012,.039,length),steel,0)
for x in (-1.33,1.33):
    for z in (-1.33,1.33): fastener('Base anchor',(x,-1.581,z),.020,'Y')

def ring_y(name,y,outer,inner,height,m):
    o=annulus(name,(0,y,0),outer,inner,height,m)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=rot((90,0,0))
    return o

cyl('Reactor lower barrel',(0,-1.22,0),.921,.61,paint,'Y',96,.014)
cyl('Low plinth seating flange',(0,-1.51,0),1.035,.085,oxid,'Y',96,.006)
cyl('Low flange bright edge',(0,-1.452,0),1.007,.028,steel,'Y',96,.003)
ring_y('Lower primary flange',-.875,1.041,.68,.115,frame)
ring_y('Lower chamber sealing flange',-.782,.874,.679,.066,steel)
ring_y('Lower glass compressing gasket',-.734,.79,.696,.025,rubber)
cyl('Upper barrel',(0,1.13,0),.962,.50,paint,'Y',96,.012)
ring_y('Upper primary flange',.86,1.041,.681,.106,frame)
ring_y('Upper chamber sealing flange',.770,.88,.679,.055,steel)
ring_y('Upper glass compressing gasket',.728,.79,.696,.025,rubber)
cyl('Upper neck joint',(0,1.426,0),.794,.12,oxid,'Y',80,.005)
cyl('Upper service lid',(0,1.533,0),.733,.118,paint,'Y',80,.010)
ring_y('Upper lid retaining ring',1.60,.79,.63,.04,steel)

# Matching bolted joints follow the same mechanical spacing at top and bottom.
for y in (-.937,.923):
    for i in range(16):
        a=math.tau*i/16
        fastener('Flange clamp bolt',(.962*math.cos(a),y,.962*math.sin(a)),.020,'Y')
for i in range(12):
    a=math.tau*i/12
    fastener('Service lid bolt',(.695*math.cos(a),1.626,.695*math.sin(a)),.015,'Y')

# Six load-bearing tie columns; clear front and rear windows, no decorative floating parts.
for i in range(6):
    a=math.radians(30+i*60); x,z=math.sin(a)*.89,-math.cos(a)*.89
    box('Outer tie column',(x,0,z),(.091,1.76,.106),frame,.009,(0,-math.degrees(a),0))
    for y in (-.729,.729):
        box('Column bolted shoe',(x,y,z),(.165,.193,.139),oxid,.009,(0,-math.degrees(a),0))
        # Dressed nuts face radially out, not random screw scatter.
        bolt=cyl('Column shoe nut',(x*1.09,y,z*1.09),.019,.015,steel,'Z',6,.002)
        bolt.rotation_quaternion=rot((0,-math.degrees(a),0))
    # Side wiring is restrained by clips and disappears into the flange.
    tube('Tie column cable',[(x*1.08,-.75,z*1.08),(x*1.08,.75,z*1.08)],.014,rubber,.03)
    for y in (-.47,.46):
        box('Cable saddle',(x*1.085,y,z*1.085),(.039,.025,.038),steel,.003,(0,-math.degrees(a),0))

# Real electrodes and insulators stay visible with the chamber powered off.
for sign in (-1,1):
    cyl('Electrode mounting disc',(0,sign*.635,0),.568,.077,oxid,'Y',80,.005)
    cyl('Ceramic feedthrough',(0,sign*.537,0),.276,.132,ivory,'Y',64,.008)
    for step in range(4):
        ring_y('Ceramic creepage rib',sign*(.481+step*.036),.317,.248,.019,ivory)
    cyl('Electrode stem',(0,sign*.365,0),.148,.168,steel,'Y',64,.008)
    cyl('Electrode end face',(0,sign*.270,0),.184,.046,steel,'Y',64,.006)
    ring_y('Electrode corona ring',sign*.259,.245,.211,.021,brass)
    for i in range(8):
        a=math.tau*i/8
        cyl('Electrode bus fastener',(.425*math.cos(a),sign*.58,.425*math.sin(a)),.023,.055,brass,'Y',12,.001)

# Purposeful service plumbing on the rear; connects both housings without occupying a walkway.
for x in (-.46,.46):
    tube('External cooling return',[(x,-1.20,.72),(x,-1.20,1.075),(x,1.14,1.075),(x,1.14,.78)],.038,oxid,.14)
    for y in (-.88,.15,1.05):
        box('Pipe support bracket',(x,y,1.025),(.113,.065,.106),frame,.006)
        cyl('Pipe union nut',(x,y,1.075),.055,.07,steel,'Y',8,.002)
for x in (-.36,0,.36):
    tube('Top power lead',[(x,1.612,0),(x,1.688,.0),(x,1.688,.40),(x,1.44,.78)],.033 if x else .046,rubber,.075)
    cyl('Top cable compression gland',(x,1.622,0),.054 if x else .073,.055,brass,'Y',12,.003)

# Restrained service plates and a hinged access lid; legible short labels only.
box('Reactor face identity plate',(0,1.106,-.964),(.54,.151,.014),oxid,.007)
txt('Reactor embossed name','CORE',(0,1.111,-.973),.082,printlight)
for x in (-.23,.23): screw((x,1.106,-.975),.006,14)
box('Reactor lower inspection cover',(0,-1.216,-.925),(.51,.298,.034),frame,.013)
for x in (-.209,.209):
    for y in (-1.33,-1.106): screw((x,y,-.947),.006,25)
box('Inspection label',(0,-1.209,-.946),(.24,.071,.002),ivory,.002)
txt('Inspection hatch marking','SERVICE',(0,-1.209,-.948),.025,ink)
for x in (-.077,.077): box('Lid latch',(x,-1.302,-.951),(.04,.026,.012),steel,.003)

# Transparent six-piece chamber, deliberately separate for URP transparent material.
glassmat=mat('RLYK_ChamberGlass','CFE4E2',0,.075)
glassmat.diffuse_color=(*glassmat.diffuse_color[:3],.16)
gb=glassmat.node_tree.nodes.get('Principled BSDF')
gb.inputs['Transmission Weight'].default_value=1.0; gb.inputs['IOR'].default_value=1.46
# Cycles preview uses mostly straight-through transmission to approximate the
# simple alpha glass supplied for URP, rather than magnifying the electrodes.
gn=glassmat.node_tree.nodes; gl=glassmat.node_tree.links
transparent=gn.new('ShaderNodeBsdfTransparent')
mixglass=gn.new('ShaderNodeMixShader'); mixglass.inputs[0].default_value=.16
gl.new(transparent.outputs[0],mixglass.inputs[1]); gl.new(gb.outputs[0],mixglass.inputs[2])
gl.new(mixglass.outputs[0],gn.get('Material Output').inputs['Surface'])
material_specs[-1].update(surface='Transparent',alpha=.16,render_face='Front',cast_shadows=False)
part('CORE_Glass',reactor,unity_parent='Environment/Core_Block')
for panel in range(6):
    # Panel edges sit behind the load columns at 30,90,... degrees from the front.
    start=math.radians(-29.65+panel*60); end=math.radians(29.65+panel*60)
    count=18; coords=[]
    for yy,rr in ((-.724,.722),(-.724,.714),(.724,.722),(.724,.714)):
        for i in range(count+1):
            a=start+(end-start)*i/count; coords.append((math.sin(a)*rr,yy,-math.cos(a)*rr))
    n=count+1; faces=[]
    for i in range(count):
        j=i+1
        faces.extend([(i,j,2*n+j,2*n+i),(n+i,3*n+i,3*n+j,n+j),(i,n+i,n+j,j),(2*n+i,2*n+j,3*n+j,3*n+i)])
    faces.extend([(0,2*n,3*n,n),(count,n+count,3*n+count,2*n+count)])
    ob=mesh('Laminated chamber glass segment',coords,faces,(0,0,0),glassmat)
    for poly in ob.data.polygons: poly.use_smooth=poly.index<count*4 and poly.index%4<2

emitter=mat('RLYK_Emitter','B2D8DC',0,.32)
part('CORE_Emitter',reactor,unity_parent='Environment/Core_Block')
for y in (-.584,.584): ring_y('Electrode luminous ceramic ring',y,.524,.483,.033,emitter)
for y in (-.823,.819):
    for i in range(6):
        a=math.radians(i*60)
        x,z=math.sin(a)*1.039,-math.cos(a)*1.039
        box('Reactor flange indicator window',(x,y,z),(.103,.027,.010),emitter,.003,(0,-math.degrees(a),0))
for i in (0,2,4):
    a=math.radians(30+i*60)
    x,z=math.sin(a)*.89,-math.cos(a)*.89
    box('Column status strip',(x*1.063,0,z*1.063),(.022,1.014,.009),emitter,.003,(0,-math.degrees(a),0))

# Low guardrail keeps the entire existing collision footprint visibly out of bounds.
part('CORE_Guardrail',reactor,unity_parent='Environment/Core_Block')
for y in (-.675,-1.071): torus('Continuous tubular safety rail',(0,y,0),1.398,.026,ochre,'Y')
for i in range(12):
    a=math.tau*i/12; x,z=1.398*math.sin(a),1.398*math.cos(a)
    cyl('Welded handrail post',(x,-1.103,z),.025,.952,ochre,'Y',16,.003)
    box('Handrail foot flange',(x,-1.566,z),(.105,.027,.105),oxid,.007,(0,-math.degrees(a),0))
    for dx in (-.027,.027): fastener('Handrail fixing',(x+dx,-1.549,z),.006,'Y')

for name in ('CORE_Containment','CORE_Glass','CORE_Emitter','CORE_Guardrail'):
    mount_spec[name]['model_child_local_scale']=[1/3,1/3.5,1/3]
    mount_spec[name]['note']='Centre-pivot model under existing scaled Core_Block. Exact inverse scale; local position ZERO. Preserve old collider.'

# Export neutral attachable units. Every material and mesh is self-contained.
bpy.context.view_layer.update()
manifest=dict(asset='RELAY CORE v01',unity_modified=False,units='metres',front='Unity -Z',
 reference_scene='Assets/Scenes/Startup_Graybox.unity',reactor_reference_position=[0,1.75,6.5],
 reference_module_position=[5,1.2,4],reactor_reference_bounds=[[-1.5,1.5],[-1.75,1.75],[-1.5,1.5]],
 emitter_default='Unpowered. Emission is zero. Any energized preview is presentation only.',
 live_display_note='Keep Track,FillPivot,Fill,all Lens_Off/Lens_On,and Startup_Status. Preview-only values/lenses not exported.',
 parts=[],materials=material_specs.copy())
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
    bpy.context.view_layer.objects.active=copies[0]
    if len(copies)>1: bpy.ops.object.join()
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

# Explicit preview-only recreations of existing Unity dynamic faces, never in FBX.
oldactive=active
def preview_box(name,loc,dims,m,parent):
    ob=box(name,loc,dims,m,.0005)
    ob.parent=parent; ob.location=v(loc); move(ob,studio); return ob
previewdark=mat('PREVIEW_ONLY_LensOff','253127',0,.35)
previewbar=mat('PREVIEW_ONLY_Progress','92AF95',0,.5)
preview_box('EXISTING Unity progress Track',(0,0,-.067),(1,.1,.01),previewdark,gauge)
preview_box('EXISTING Unity progress Fill',(-.28,0,-.08),(.44,.075,.012),previewbar,gauge)
for name,parent in indicator_roots.items():
    preview_box('EXISTING Unity '+name+' off lens',(0,.025,-.068),(.14,.065,.02),previewdark,parent)
txt('EXISTING Unity live status PREVIEW ONLY','STANDBY',(0,-.9,-.512),.065,ink,parent=cabinet,collection=studio)
active=oldactive
handlepivot.rotation_mode='QUATERNION'; handlepivot.rotation_quaternion=rot((-25,0,0))

scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.cycles.transmission_bounces=8; scene.cycles.max_bounces=10
scene.render.threads_mode='FIXED'; scene.render.threads=6
scene.render.resolution_x=1450; scene.render.resolution_y=1400; scene.render.resolution_percentage=100
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.16,.17,1); scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'; scene.render.image_settings.file_format='PNG'
floormat=mat('PREVIEW_ONLY_Floor','464B49',0,.60)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.752)); floor=bpy.context.object; floor.name='Studio floor PREVIEW ONLY'; floor.data.materials.append(floormat); move(floor,studio)
def aim(ob,at): ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=loc; aim(o,(0,0,0)); return o
area('Workshop softbox',(-4,-5,6),1250,5,(1,.92,.82))
area('High cool bounce',(3,2,5),1550,4,(.77,.88,1))
area('Front reflected light',(5,-4,1.4),460,3,(1,.98,.92))
camera=bpy.data.objects.new('CORE review camera',bpy.data.cameras.new('Core camera')); studio.objects.link(camera)
camera.location=(6.5,-10,4.5); aim(camera,(.63,0,-.10)); camera.data.type='ORTHO'; camera.data.ortho_scale=6.0; scene.camera=camera
# Keep labels portable without an external font file.
bpy.ops.object.select_all(action='DESELECT'); texts=[o for o in source.objects if o.type=='FONT']
for ob in texts: ob.select_set(True)
if texts: bpy.context.view_layer.objects.active=texts[0]; bpy.ops.object.convert(target='MESH')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL'; a.spaces.active.overlay.show_overlays=False; a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT'); assembly.select_set(True); bpy.context.view_layer.objects.active=assembly
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_CORE_v01.blend'))
print('CORE_BUILD_COMPLETE',manifest['triangles_total'],flush=True)
if '--draft' in sys.argv:
    scene.cycles.samples=12; scene.render.resolution_percentage=55
    scene.render.filepath=os.path.join(OUT,'previews','CORE_draft.png'); bpy.ops.render.render(write_still=True)
