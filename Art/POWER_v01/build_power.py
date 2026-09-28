import bpy, math, os, json, random
import numpy as np
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__))
for folder in ('exports', 'textures', 'previews'):
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):
    bpy.data.materials.remove(data)
random.seed(18)
P = Matrix(((1,0,0), (0,0,1), (0,1,0)))
def v(u): return P @ Vector(u)
def rotation(u): return (P @ Euler(tuple(math.radians(a) for a in u), 'XYZ').to_matrix() @ P).to_quaternion()
def srgb(c): return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4
def material(name, color, metallic=0, rough=.5, texture=False):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    rgb=tuple(int(color[i:i+2],16)/255 for i in (0,2,4))
    base=tuple(srgb(c) for c in rgb)
    mat.diffuse_color=(*base,1)
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*base,1)
    bs.inputs['Metallic'].default_value=metallic; bs.inputs['Roughness'].default_value=rough
    if texture:
        n=1024; rng=np.random.default_rng(sum(map(ord,name)))
        pixels=np.ones((n,n,4),dtype=np.float32)
        grain=rng.normal(0,.012,(n,n))
        broad=rng.normal(0,.015,(32,32)).repeat(32,0).repeat(32,1)
        for _ in range(8): broad=(broad+np.roll(broad,5,0)+np.roll(broad,-5,0)+np.roll(broad,5,1)+np.roll(broad,-5,1))/5
        grain+=broad
        for _ in range(450):
            x,y=rng.integers(0,n,2); length=int(rng.integers(2,30))
            grain[y:y+1,x:min(n,x+length)] += float(rng.uniform(-.06,.06))
        for c in range(3): pixels[:,:,c]=np.clip(rgb[c]+grain,0,1)
        image=bpy.data.images.new(name+'_BaseColor',width=n,height=n,alpha=False)
        image.colorspace_settings.name='sRGB'; image.pixels.foreach_set(pixels.ravel())
        image.filepath_raw=os.path.join(OUT,'textures',name+'_BaseColor.png'); image.file_format='PNG'; image.save()
        node=mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image=image
        mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    return mat

paint=material('RLY_PaintedSteel','485B59',.6,.43,True)
edge=material('RLY_ExposedSteel','717B79',.82,.36,True)
dark=material('RLY_BlackMetal','222D2D',.7,.42,True)
rubber=material('RLY_Bakelite','252525',0,.55,True)
red=material('RLY_OxideRed','863C2E',.25,.45,True)
brass=material('RLY_AgedBrass','8E805C',.7,.42,True)
paper=material('RLY_MeterEnamel','C9CAB9',.1,.57,True)
ink=material('RLY_MarkingDark','182326',0,.7)
white=material('RLY_MarkingIvory','D5D6C8',0,.5)
yellow=material('RLY_SafetyOchre','AD8741',.15,.5,True)
orange=material('RLY_IndicatorAmber','DD902E',.15,.33)

parts={}; active_part=None
def root(name, location=(0,0,0), parent=None):
    ob=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(ob)
    ob.parent=parent; ob.location=v(location); return ob
assembly=root('RELAY_POWER_Assembly')
def part(name,parent,location=(0,0,0)):
    global active_part
    p=root(name,location,parent); p['unity_local_position']=list(location)
    parts[name]=p; active_part=p; return p
def register(ob,name,loc,mat):
    ob.name=name; ob.parent=active_part; ob.location=v(loc)
    ob.data.materials.append(mat); return ob
def bevel(ob,width=.005,segments=2):
    ob.data.materials.append(edge)
    mod=ob.modifiers.new('Manufactured edge','BEVEL'); mod.width=width; mod.segments=segments; mod.material=1
    mod=ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); mod.keep_sharp=True; mod.weight=50
def box(name,loc,size,mat,bev=.003,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob=register(bpy.context.object,name,loc,mat)
    ob.scale=v(size); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rotation(rot)
    if bev: bevel(ob,bev)
    return ob
def cylinder(name,loc,r,depth,mat,axis='Z',verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth)
    ob=register(bpy.context.object,name,loc,mat)
    direction=v({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis])
    ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=Vector((0,0,1)).rotation_difference(direction)
    bevel(ob,min(.002,r*.12),2)
    for poly in ob.data.polygons: poly.use_smooth=len(poly.vertices)==4
    return ob
def text(name,body,loc,size,mat=white,align='CENTER'):
    curve=bpy.data.curves.new(name,'FONT'); curve.body=body; curve.size=size
    curve.align_x=align; curve.align_y='CENTER'; curve.extrude=.00015; curve.resolution_u=3
    ob=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(ob)
    ob.parent=active_part; ob.location=v(loc); ob.rotation_euler=(math.pi/2,0,0)
    ob.data.materials.append(mat); return ob
def bolt(x,y,z,r=.009):
    cylinder('Fastener', (x,y,z),r,.004,edge,verts=12)
    box('Screw slot',(x,y,z-.0025),(r*1.2,.0018,.001),dark,0)
def wire(name,points,r,mat):
    curve=bpy.data.curves.new(name,'CURVE'); curve.dimensions='3D'; curve.resolution_u=8; curve.bevel_depth=r; curve.bevel_resolution=2
    spl=curve.splines.new('BEZIER'); spl.bezier_points.add(len(points)-1)
    for bp,coord in zip(spl.bezier_points,points): bp.co=v(coord); bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(ob); ob.parent=active_part; ob.data.materials.append(mat); return ob

# Cabinet. Dimensions and control origins match the existing Unity graybox.
part('POWER_Cabinet',assembly)
box('Enclosure',(0,0,.015),(1.8,2.4,.97),paint,.028)
box('Door gasket',(0,0,-.476),(1.67,2.27,.035),rubber,.012)
box('Service door',(0,0,-.504),(1.63,2.23,.035),paint,.014)
box('Toe plinth',(0,-1.14,-.01),(1.78,.12,.97),dark,.009)
box('Header recess',(0,.963,-.529),(1.4,.24,.014),dark,.005)
text('Power title','POWER',(-.62,.992,-.54),.092,white,'LEFT')
text('Unit identity','RLY / 04',(.60,1.005,-.541),.035,white,'RIGHT')
text('Header descriptor','DISTRIBUTION  /  100 VDC',(-.62,.916,-.541),.025,white,'LEFT')
for y in (.66,-.68):
    box('Hinge leaf',(.807,y,-.528),(.055,.16,.025),edge)
    cylinder('Hinge pin',(.834,y,-.542),.018,.19,dark,'Y',20)
for x in (-.75,.75):
    for y in (-1.035,.82): bolt(x,y,-.532,.009)
for i in range(8):
    y=-.88-i*.028
    box('Vent shadow',(-.37,y,-.527),(.50,.012,.004),dark,.002)
    box('Louver lip',(-.37,y+.006,-.533),(.5,.01,.008),edge,.002)
box('Inspection plate',(-.37,-.695,-.534),(.49,.11,.007),dark,.002)
text('Inspection inscription','SERVICE  /  ISOLATE FIRST',(-.37,-.694,-.54),.020,white)
for x in (-.58,-.16): bolt(x,-.695,-.545,.006)
for z in (-.24,-.12,0,.12,.24,.36):
    box('Side ventilation',(.902,.35,z),(.005,.46,.035),dark,.002)
wire('Left loom',[(-.78,-.83,-.535),(-.80,-.55,-.548),(-.78,.22,-.548),(-.7,.77,-.535)],.011,rubber)
for y in (-.55,-.05,.46): box('Loom clamp',(-.8,y,-.554),(.04,.035,.018),edge,.002)
text('Cabinet serial','RELAY  //  P-04-018',(-.37,-1.095,-.534),.014,white)

# AUX housing and independent Z-rotation handle.
aux=root('AUX_Switch',(-.3,-.4,-.55),assembly)
part('AUX_Housing',aux)
box('Aux mounting plate',(0,0,0),(.32,.4,.12),dark,.014)
box('Aux enamel face',(0,0,-.066),(.283,.36,.015),paint,.007)
cylinder('Selector ring',(0,0,-.078),.066,.023,brass,verts=48)
cylinder('Selector insert',(0,0,-.092),.045,.023,rubber)
for x in (-.125,.125):
    for y in (-.16,.16): bolt(x,y,-.077,.008)
text('Aux label','AUX', (0,-.135,-.079),.035)
text('Selector zero','0',(-.105,.106,-.079),.025)
text('Selector one','I',(.105,.106,-.079),.025)
part('AUX_Handle',aux,(0,0,-.085))
cylinder('Aux hub',(0,0,-.02),.032,.053,dark)
box('Aux stem',(0,.057,-.025),(.031,.135,.043),edge,.006)
box('Aux grip',(0,.112,-.03),(.072,.065,.056),rubber,.009)
box('Aux index',(0,.116,-.060),(.012,.033,.002),white,.001)

# MAIN mechanism, independently pivoted around local X.
lever=root('MAIN_Lever',(.28,-.75,-.55),assembly)
part('MAIN_Housing',lever)
box('Main mounting plate',(0,0,0),(.42,.84,.12),dark,.013)
box('Main front',(0,0,-.065),(.379,.795,.016),paint,.008)
box('Recessed travel channel',(0,0,-.077),(.135,.57,.008),rubber,.005)
for x in (-.162,.162):
    for y in (-.36,.36): bolt(x,y,-.08,.011)
for x in (-.085,.085): box('Hinge cheek',(x,0,-.105),(.035,.115,.095),brass,.004)
cylinder('Hinge axle',(0,0,-.10),.024,.22,edge,'X',24)
text('Main upper marking','OFF',(-.125,.22,-.082),.021)
text('Main lower marking','MAIN',(0,-.315,-.082),.035)
box('Stop upper',(0,.27,-.09),(.13,.02,.028),edge,.003)
box('Stop lower',(0,-.27,-.09),(.13,.02,.028),edge,.003)
part('MAIN_Handle',lever,(0,0,-.1))
cylinder('Rotating axle',(0,0,0),.031,.136,dark,'X',24)
box('Lever forged stem',(0,.18,0),(.037,.36,.043),edge,.008)
box('Lever grip',(0,.36,0),(.28,.09,.1),red,.015)
for x in (-.135,.135): box('Grip end',(x,.36,0),(.013,.083,.094),dark,.004)
for x in (-.082,-.041,0,.041,.082): box('Grip seam',(x,.36,-.051),(.007,.051,.003),dark,.001)

def dial(name,loc,kind):
    control=root(name,loc,assembly)
    part(name+'_Housing',control)
    cylinder('Dial bezel',(0,0,0),.18,.12,dark,verts=64)
    cylinder('Dial face',(0,0,-.066),.167,.014,paint,verts=64)
    for i in range(21):
        a=math.radians(135-270*i/20); r=.149
        x=-math.sin(a)*r; y=math.cos(a)*r
        box('Dial tick',(x,y,-.075),(.0025,.017 if i%2==0 else .009,.0015),white,0,(0,0,math.degrees(a)))
    for value in (0,50,100):
        a=math.radians(135-270*value/100)
        text('Dial numeral',str(value),(-math.sin(a)*.192,math.cos(a)*.192,-.079),.019,white)
    text('Dial function','VOLTAGE' if kind==0 else 'LOAD BALANCE',(0,-.237,-.03),.025,white)
    part(name+'_Knob',control,(0,0,-.1))
    if kind==0:
        cylinder('Rotor base',(0,0,.002),.116,.06,rubber,verts=48)
        for i in range(24):
            a=2*math.pi*i/24
            cylinder('Rotor fluting',(.11*math.cos(a),.11*math.sin(a),0),.01,.055,rubber,verts=8)
        cylinder('Rotor cap',(0,0,-.033),.098,.014,dark,verts=48)
        box('Rotor pointer',(0,.065,-.044),(.013,.066,.004),white,.001)
    else:
        cylinder('Balance drum',(0,0,0),.10,.062,dark,verts=48)
        box('Balance wing',(0,0,-.025),(.075,.225,.068),rubber,.016)
        box('Balance index',(0,.078,-.062),(.014,.037,.004),yellow,.001)
    return control

dial('VOLTAGE',(.28,.45,-.55),0)
dial('BALANCE',(.28,-.05,-.55),1)

# Analog voltage gauge. Needle origin matches the existing NeedlePivot.
gauge=root('VOLTAGE_Gauge',(-.3,.45,-.55),assembly)
part('Gauge_Housing',gauge)
box('Meter shell',(0,0,0),(.62,.56,.12),dark,.018)
box('Meter flange',(0,0,-.064),(.586,.526,.025),edge,.012)
box('Meter gasket',(0,0,-.079),(.55,.492,.012),rubber,.009)
box('Meter dial',(0,0,-.085),(.526,.468,.005),paper,.006)
for x in (-.287,.287):
    for y in (-.252,.252): bolt(x,y,-.08,.008)
for i in range(51):
    a=math.radians(135-270*i/50); r=.19; length=.019 if i%5==0 else .01
    box('Meter graduation',(-math.sin(a)*r,.035+math.cos(a)*r,-.089),(.0025,length,.001),ink,0,(0,0,math.degrees(a)))
for i in range(0,101,20):
    a=math.radians(135-270*i/100); r=.145
    text('Scale numeral',str(i),(-math.sin(a)*r,.035+math.cos(a)*r,-.090),.022,ink)
text('Meter unit','V',(0,.105,-.090),.042,ink)
text('Meter standard','DC   /   CLASS 1.5',(0,-.075,-.090),.016,ink)
box('Live readout recess',(0,-.176,-.09),(.41,.061,.002),dark,.002)
text('Meter label','OUTPUT', (0,-.221,-.092),.016,ink)
part('Gauge_Needle',gauge,(0,.035,-.095))
box('Needle blade',(0,.088,0),(.005,.176,.004),red,.001)
box('Needle counterweight',(0,-.023,0),(.019,.037,.004),dark,.003)
cylinder('Needle hub',(0,0,-.003),.018,.009,brass,verts=24)

# Convert and consolidate by functional part, preserving every moving origin.
mesh_parts={}
for name,pivot in parts.items():
    objs=list(pivot.children)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs: ob.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.convert(target='MESH')
    objs=[o for o in pivot.children if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs: ob.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join()
    mesh=bpy.context.object; mesh.name=name+'_Mesh'
    bpy.context.scene.cursor.location=pivot.matrix_world.translation
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh_parts[name]=mesh

# Separate FBX files: all meshes centered on their functional pivot.
manifest={'asset':'RELAY POWER v01','authoring_units':'meters','parts':[],
          'note':'Unity scene/scripts untouched. FBX import axis/material verification required in Unity.'}
for name,mesh in mesh_parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    copy=mesh.copy(); copy.data=mesh.data.copy(); bpy.context.collection.objects.link(copy)
    copy.parent=None; copy.matrix_world=Matrix.Identity(4); copy.name=name
    copy.select_set(True); bpy.context.view_layer.objects.active=copy
    path=os.path.join(OUT,'exports',name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
        add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri_count=sum(len(p.vertices)-2 for p in copy.data.polygons)
    manifest['parts'].append({'name':name,'triangles':tri_count,
        'unity_parent_local_position':list(parts[name]['unity_local_position']),
        'file':'exports/'+name+'.fbx'})
    bpy.data.objects.remove(copy,do_unlink=True)

# Preview uses the existing game's initial poses.
for name,angles in {'AUX_Handle':(0,0,25),'MAIN_Handle':(-25,0,0),
                    'VOLTAGE_Knob':(0,0,0),'BALANCE_Knob':(0,0,135),'Gauge_Needle':(0,0,135)}.items():
    parts[name].rotation_mode='QUATERNION'; parts[name].rotation_quaternion=rotation(angles)

scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
scene.render.resolution_x=1400; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
scene.world.color=(.1,.1,.1)
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.14,.16,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'
studio=bpy.data.collections.new('PREVIEW_ONLY'); scene.collection.children.link(studio)
def to_studio(ob):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    studio.objects.link(ob)
floor=material('Preview_Ground','20292E',.1,.6)
active_part=None
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.205)); ground=bpy.context.object
ground.name='Preview ground'; ground.data.materials.append(floor); to_studio(ground)
def aim(ob,target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.color=color; data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); studio.objects.link(ob); ob.location=loc; aim(ob,target)
area('Soft key',(-3,-4,5),1100,(.78,.9,1),4,(0,0,0))
area('Warm rim',(3,1,3),1500,(1,.66,.38),3,(0,0,0))
area('Front fill',(1,-4,.4),250,(.78,.87,1),3,(0,-.5,0))
camera_data=bpy.data.cameras.new('Preview camera'); camera=bpy.data.objects.new('Preview camera',camera_data)
studio.objects.link(camera); camera.location=(3.5,-6.4,2.5); aim(camera,(0,-.1,0)); camera_data.type='ORTHO'; camera_data.ortho_scale=3.9
scene.camera=camera
scene.render.image_settings.file_format='PNG'; scene.render.filepath=os.path.join(OUT,'previews','POWER_hero.png')
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,indent=2,ensure_ascii=False)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v01.blend'))
bpy.ops.render.render(write_still=True)
camera.location=(0,-7,.25); aim(camera,(0,-.5,0)); camera_data.ortho_scale=2.85
scene.render.resolution_x=1300; scene.render.resolution_y=1600
scene.render.filepath=os.path.join(OUT,'previews','POWER_front.png'); bpy.ops.render.render(write_still=True)
print('POWER_ASSETS_COMPLETE',OUT)
