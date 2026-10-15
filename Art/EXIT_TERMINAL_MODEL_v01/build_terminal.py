"""Standalone Blender authoring. Never opens or writes a Unity project.
Design coordinates: metres, X/right, Y/up, FRONT +Z (the exit-room side).
Same FBX conversion as existing RELAY assets; Unity child rotation Y=180.
"""
import bpy, bmesh, math, json, random, sys
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

assert bpy.app.background
OUT = Path(__file__).resolve().parent
assert not OUT.is_relative_to(Path(r'C:\Users\gonut\School_p2'))
for d in ('exports', 'textures', 'previews', 'checks'):
    (OUT / d).mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.threads_mode = 'FIXED'
scene.render.threads = 8
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
P = Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(p): return P @ Vector(p)
def color(h):
    c = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in c)+(1,)
def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
source=collection('01_EDITABLE_TERMINAL')
exportcol=collection('02_GAME_EXPORTS')
studio=collection('03_REVIEW_ONLY')
def move(o,c):
    for x in list(o.users_collection): x.objects.unlink(o)
    c.objects.link(o)
def material(name,h,rough=.6,metal=0,weather=False):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=color(h)
    n=m.node_tree.nodes; links=m.node_tree.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=color(h)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    m['roughness']=rough; m['metallic']=metal
    if weather:
        g=n.new('ShaderNodeNewGeometry'); noise=n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=55; noise.inputs['Detail'].default_value=3
        links.new(g.outputs['Position'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.15
        ramp.color_ramp.elements[0].color=tuple(x*.88 for x in color(h)[:3])+(1,)
        ramp.color_ramp.elements[1].position=.87
        ramp.color_ramp.elements[1].color=tuple(min(1,x*1.05) for x in color(h)[:3])+(1,)
        links.new(noise.outputs['Fac'],ramp.inputs[0]); links.new(ramp.outputs[0],p.inputs['Base Color'])
        r=n.new('ShaderNodeMapRange'); r.inputs['To Min'].default_value=max(0,rough-.08)
        r.inputs['To Max'].default_value=min(1,rough+.07)
        links.new(noise.outputs['Fac'],r.inputs['Value']); links.new(r.outputs[0],p.inputs['Roughness'])
    return m
case=material('SOURCE_AgedIvory','BDBBA7',.61,0,True)
frame=material('SOURCE_GrayGreenPaint','424C49',.62,0,True)
plate=material('SOURCE_ServicePanel','65706B',.68,0,True)
keys=material('SOURCE_KeyIvory','CFC9B4',.59,0,True)
darkkeys=material('SOURCE_KeyGraphite','535951',.67,0,True)
enter=material('SOURCE_EnterOchre','AA9361',.56,0,True)
rubber=material('SOURCE_Rubber','171D1B',.83)
steel=material('SOURCE_WornSteel','777D78',.45,.8,True)
oxid=material('SOURCE_Oxide','534A3D',.83,.25,True)
ink=material('RLYT_Ink','242D28',.8)
legend=material('RLYT_Legend','D5D2BD',.79)
screenmat=material('RLYT_CRTScreen','08140F',.16)
led=material('SOURCE_UnlitPowerLens','284D38',.28)

groups={k:[] for k in ('Body','Keys','EnterKey','Screen')}; group='Body'
def register(o,name,mat):
    move(o,source); o.name=name; o.data.materials.append(mat); groups[group].append(o); return o
def edge(o,width=.002,segments=2):
    if width:
        mod=o.modifiers.new('Small manufactured edge','BEVEL'); mod.width=width; mod.segments=segments
        no=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); no.keep_sharp=True
    return o
def box(name,p,d,m,bev=.002):
    bpy.ops.mesh.primitive_cube_add(size=1,location=v(p)); o=register(bpy.context.object,name,m)
    o.scale=v(d); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return edge(o,bev)
def cyl(name,p,r,depth,m,axis=(0,0,1),verts=20,bev=.0007):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=v(p))
    o=register(bpy.context.object,name,m); o.rotation_mode='QUATERNION'
    o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(axis))
    for face in o.data.polygons: face.use_smooth=len(face.vertices)==4
    return edge(o,bev)
def mesh(name,verts,faces,m):
    me=bpy.data.meshes.new(name); me.from_pydata([v(p) for p in verts],[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); source.objects.link(o); o.data.materials.append(m); groups[group].append(o); return o
def rounded(w,h,r,n=12):
    points=[]
    for cx,cy,start in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for k in range(n+1):
            a=math.radians(start+90*k/n); points.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return points
def loft(name,profiles,m,cap_start=False,cap_end=False):
    vertices=[]; n=52
    for w,h,r,z in profiles:
        vertices += [(x,1.25+y,z) for x,y in rounded(w,h,r)]
    faces=[]
    for k in range(len(profiles)-1):
        for i in range(n):
            j=(i+1)%n; faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    if cap_start: faces.append(tuple(range(n-1,-1,-1)))
    if cap_end: faces.append(tuple((len(profiles)-1)*n+i for i in range(n)))
    ob=mesh(name,vertices,faces,m)
    for face in ob.data.polygons: face.use_smooth=True
    return edge(ob,.0015)
def text(name,body,p,size,m=ink,surface='front',align='CENTER'):
    d=bpy.data.curves.new(name,'FONT'); d.body=body; d.size=size; d.align_x=align; d.align_y='CENTER'
    d.resolution_u=3; d.extrude=0
    o=bpy.data.objects.new(name,d); source.objects.link(o); groups[group].append(o); d.materials.append(m)
    o.location=v(p)
    # The terminal faces Unity +Z: text reads from that side, not through its back.
    o.rotation_euler=(math.pi/2,0,math.pi) if surface=='front' else (0,0,math.pi)
    return o
def screw(p,r=.005):
    cyl('Slotted steel screw',p,r,.003,steel,verts=16)
    box('Screw slot',(p[0],p[1],p[2]+.0016),(r*1.35,.001,.0003),ink,0)
def cable(name,pts,r=.007):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=r; c.bevel_resolution=2; c.use_fill_caps=True
    sp=c.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for a,p in zip(sp.bezier_points,pts): a.co=v(p); a.handle_left_type=a.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c); source.objects.link(o); c.materials.append(rubber); groups[group].append(o); return o

# Stand: all supports and cables physically terminate in another part.
for x in (-.235,.235):
    for z in (-.175,.175): box('Rubber isolation foot',(x,.0225,z),(.09,.045,.09),rubber,.006)
box('Footplate',(0,.060,0),(.60,.045,.45),frame,.007)
box('Pedestal folded shell',(0,.454,-.012),(.552,.748,.404),frame,.010)
box('Pedestal top shoulder',(0,.818,0),(.58,.035,.43),plate,.004)
box('Front panel gasket',(0,.448,.195),(.48,.625,.012),rubber,.005)
box('Removable front service door',(0,.448,.205),(.465,.610,.016),plate,.005)
for x in (-.207,.207):
    for y in (.166,.731): screw((x,y,.215),.006)
for i in range(8):
    x=-.13+i*.037
    box('Service ventilation recess',(x,.26,.214),(.018,.075,.0015),rubber,.005)
    box('Vent lip',(x,.298,.216),(.020,.002,.004),plate,.0005)
box('Service recessed handle',(0,.58,.217),(.13,.041,.008),rubber,.006)
box('Service handle edge',(0,.59,.228),(.115,.019,.016),frame,.003)
text('Small exit identification','EXIT CONTROL',(0,.69,.214),.023,legend)
box('Old inventory label',(.151,.395,.216),(.094,.050,.001),case,.001)
text('Inventory identifier','ET-04',(.151,.402,.217),.017)
text('Inventory secondary','LAB / 06',(.151,.382,.217),.008)

box('Keyboard steel tray',(0,.847,.195),(.82,.055,.73),frame,.008)
box('Tray front rolled edge',(0,.865,.554),(.82,.035,.018),plate,.005)
for x in (-.398,.398): box('Tray side return',(x,.868,.195),(.024,.027,.71),plate,.004)
box('Monitor neck',(0,.918,-.06),(.22,.17,.24),frame,.014)
box('Swivel support foot',(0,.976,-.015),(.35,.048,.32),rubber,.012)

# Deep tapered CRT housing; an open front aperture, never a solid box over the UI.
loft('Tapered CRT rear case',[(.774,.594,.060,.165),(.746,.565,.067,.105),(.650,.485,.060,-.175),(.620,.455,.055,-.218)],case,False,True)
loft('Dark shell split line',[(.779,.599,.060,.168),(.779,.599,.060,.177)],rubber)
loft('Moulded CRT front bezel',[(.774,.594,.060,.176),(.780,.600,.060,.202),(.768,.588,.058,.235),(.690,.454,.046,.237),(.660,.420,.043,.213)],case)
loft('CRT aperture seal',[(.662,.422,.043,.214),(.644,.402,.041,.218)],rubber)
for x in (-.344,.344):
    for y in (1.007,1.493): screw((x,y,.229),.0045)
for sign in (-1,1):
    for i in range(11):
        y=1.08+i*.029
        # Slots sit against the tapered side shell, with a short protective lip.
        box('Side ventilation inset',(sign*.353,y,.005),(.002,.010,.112),rubber,.003)
    for y in (1.075,1.425): cyl('Side cabinet screw',(sign*.351,y,-.028),.005,.004,steel,axis=(1,0,0),verts=16)
for i in range(14):
    x=-.245+i*.0375
    box('Rear CRT vent',(x,1.35,-.220),(.018,.09,.001),rubber,.004)
text('Restrained bezel label','LOCAL',(.265,1.006,.240),.013)
box('Power switch well',(-.288,1.007,.242),(.052,.026,.006),rubber,.004)
box('Power rocker',(-.288,1.007,.247),(.040,.020,.007),darkkeys,.003)
cyl('Dark power LED lens',(-.239,1.007,.245),.004,.004,led,verts=20)
for x in (-.273,-.256,-.222): box('Brightness trim mark',(x,1.475,.235),(.003,.005,.0004),ink,0)

# Routed cables terminate inside rear sockets and the stand; no floating ends.
for x in (-.145,.14):
    cyl('Rear cable gland',(x,1.055,-.221),.014,.022,rubber,verts=20)
cable('Power lead to stand',[(-.145,1.055,-.232),(-.16,.99,-.28),(-.195,.72,-.258),(-.16,.56,-.22)])
cable('Keyboard data cable',[(.14,1.055,-.23),(.19,.98,-.27),(.30,.91,-.04),(.28,.901,.265)],.0055)
cyl('Lower cable entry',(-.16,.56,-.216),.014,.012,rubber)

# Compact, believable mechanical keyboard with individually modelled keys.
box('Keyboard lower casing',(0,.898,.295),(.735,.055,.274),rubber,.010)
box('Keyboard upper casing',(0,.913,.295),(.725,.028,.264),case,.008)
box('Keyboard dark inset',(0,.929,.273),(.680,.003,.192),rubber,.007)
text('Keyboard maker mark','RELAY',(.284,.929,.407),.009,ink,'top')
text('Keyboard small identification','SECURITY / 04',(-.237,.929,.408),.006,ink,'top')
group='Keys'
key_count=0
enter_center=None
def key(label,x,z,width=.030,depth=.027,kind=None):
    global group,key_count,enter_center
    previous=group
    if label=='ENTER': group='EnterKey'; enter_center=(x,.939,z)
    m=kind or keys
    box('Keycap '+label,(x,.938,z),(width,.018,depth),m,.003)
    if label not in ('SPACE',''):
        text('Legend '+label,label,(x,.9473,z),.0057 if len(label)>2 else .0105,
             legend if m==darkkeys else ink,'top')
    if label in ('F','J'):
        box('Home key tactile bar',(x,.948,z+.009),(.009,.001,.0015),m,.0003)
    group=previous; key_count+=1

pitch=.034
def row(z,items):
    x=.326
    for label,units in items:
        width=units*pitch-.004
        key(label,x-width/2,z,width,kind=darkkeys if len(label)>1 and label!='ENTER' else enter if label=='ENTER' else None)
        x-=units*pitch
row(.203,[(s,1) for s in ['ESC','1','2','3','4','5','6','7','8','9','0','-','=']]+[('DEL',1)])
row(.238,[('TAB',1.4)]+[(s,1) for s in 'QWERTYUIOP']+[('[',1),(']',1),('\\',.6)])
row(.273,[('CTRL',1.6)]+[(s,1) for s in 'ASDFGHJKL']+[(';',1),('ENTER',2.4)])
row(.308,[('SHIFT',2.1)]+[(s,1) for s in 'ZXCVBNM']+[(',',1),('.',1),('/',1),('SHIFT',1.9)])
row(.343,[('CTRL',1.6),('ALT',1.4),('SPACE',7.2),('ALT',1.4),('CTRL',2.4)])
for row_index,labels in enumerate(['789','456','123','0.-']):
    for col,label in enumerate(labels):
        key(label,-.217-col*.038,.206+row_index*.040,.032,.031)

# The entire keyboard clears the CRT lip, including the function row.
for o in groups['Keys']+groups['EnterKey']:
    o.location+=v((0,0,.09))
for o in groups['Body']:
    if o.name.startswith(('Keyboard lower','Keyboard upper','Keyboard dark','Keyboard maker','Keyboard small')):
        o.location+=v((0,0,.09))
enter_center=(enter_center[0],enter_center[1],enter_center[2]+.09)

# Sparse real wear on exposed edges. Avoid uniform decorative grime everywhere.
group='Body'
rng=random.Random(4092)
for i in range(26):
    x=rng.uniform(-.36,.36); length=rng.uniform(.003,.014)
    box('Worn tray edge',(x,.879,.563),(length,.0018,.0006),steel if i%3 else oxid,0)
for i in range(12):
    x=rng.choice((-.225,.225))+rng.uniform(-.004,.004)
    box('Service edge paint nick',(x,rng.uniform(.18,.72),.215),(rng.uniform(.001,.004),rng.uniform(.003,.012),.0005),oxid,0)

# A shallow convex CRT face, opaque and separate from all UI/preview lettering.
group='Screen'
verts=[]; faces=[]; nx=40; ny=28; w=.644; h=.402; radius=.041
for j in range(ny+1):
    y=-h/2+h*j/ny; distance=h/2-abs(y)
    inset=0 if distance>=radius else radius-math.sqrt(max(0,radius*radius-(radius-distance)**2))
    half=w/2-inset
    for i in range(nx+1):
        x=-half+2*half*i/nx
        bulge=.0175*max(0,1-(x/(w/2))**2)*max(0,1-(y/(h/2))**2)
        verts.append((x,1.25+y,.216+bulge))
for j in range(ny):
    for i in range(nx):
        a=j*(nx+1)+i; faces.append((a,a+1,a+1+nx+1,a+nx+1))
screen=mesh('CRT dark convex glass',verts,faces,screenmat)
# Keep face normals outward on an intentionally open curved screen mesh.
for poly in screen.data.polygons: poly.use_smooth=True
if sum(p.normal.y for p in screen.data.polygons)<0:
    bm=bmesh.new(); bm.from_mesh(screen.data); bmesh.ops.reverse_faces(bm,faces=bm.faces); bm.to_mesh(screen.data); bm.free()

# Create evaluated meshes while retaining the full editable source collection.
bpy.context.view_layer.update(); deps=bpy.context.evaluated_depsgraph_get()
export_objects={}
for name,objects in groups.items():
    copies=[]
    for ob in objects:
        evaluated=ob.evaluated_get(deps)
        me=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
        dupe=bpy.data.objects.new(name+'_part',me); exportcol.objects.link(dupe)
        dupe.matrix_world=ob.matrix_world.copy(); copies.append(dupe)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in copies: ob.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join()
    ob=bpy.context.object; ob.name='TERMINAL_'+name
    scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    export_objects[name]=ob
source.hide_render=True
source.hide_viewport=True

# Pack one shared UV atlas for the fixed enclosure and both keyboard parts.
bpy.ops.object.select_all(action='DESELECT')
for name in ('Body','Keys','EnterKey'):
    ob=export_objects[name]; ob.select_set(True)
    if not ob.data.uv_layers: ob.data.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active=export_objects['Body']
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3)
bpy.ops.object.mode_set(mode='OBJECT')

size=2048
def bake_image(name,typ):
    img=bpy.data.images.new(name,width=size,height=size,alpha=True)
    if typ!='DIFFUSE': img.colorspace_settings.name='Non-Color'
    allmats=set(m for k in ('Body','Keys','EnterKey') for m in export_objects[k].data.materials)
    nodes=[]
    for m in allmats:
        node=m.node_tree.nodes.new('ShaderNodeTexImage'); node.image=img
        m.node_tree.nodes.active=node; nodes.append((m,node))
    scene.render.bake.use_clear=True; scene.render.bake.margin=8
    scene.render.bake.use_selected_to_active=False
    if typ=='DIFFUSE': bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'})
    else: bpy.ops.object.bake(type=typ)
    for m,n in nodes: m.node_tree.nodes.remove(n)
    return img

print('BAKE_BASE_COLOR',flush=True)
base=bake_image('TERMINAL_BaseColor','DIFFUSE')
base.filepath_raw=str(OUT/'textures/TERMINAL_BaseColor.png'); base.file_format='PNG'; base.save()
print('BAKE_ROUGHNESS',flush=True)
rough=bake_image('TERMINAL_Roughness','ROUGHNESS')
rough.filepath_raw=str(OUT/'textures/TERMINAL_Roughness.png'); rough.file_format='PNG'; rough.save()

# Bake metallic through emission; restore every original surface link afterward.
original_links=[]
allmats=set(m for k in ('Body','Keys','EnterKey') for m in export_objects[k].data.materials)
for m in allmats:
    n=m.node_tree.nodes; l=m.node_tree.links; out=n.get('Material Output')
    original=out.inputs['Surface'].links[0].from_socket
    em=n.new('ShaderNodeEmission'); value=m.get('metallic',0)
    em.inputs['Color'].default_value=(value,value,value,1)
    l.new(em.outputs[0],out.inputs['Surface']); original_links.append((m,out,original,em))
print('BAKE_METALLIC',flush=True)
metal=bake_image('TEMP_Metallic','EMIT')
for m,out,sock,em in original_links: m.node_tree.links.new(sock,out.inputs['Surface']); m.node_tree.nodes.remove(em)
rv=np.empty(size*size*4,dtype=np.float32); rough.pixels.foreach_get(rv)
mv=np.empty(size*size*4,dtype=np.float32); metal.pixels.foreach_get(mv)
packed=np.zeros_like(rv).reshape(-1,4); packed[:,0]=mv.reshape(-1,4)[:,0]; packed[:,3]=1-rv.reshape(-1,4)[:,0]
ms=bpy.data.images.new('TERMINAL_MetallicSmoothness',width=size,height=size,alpha=True)
ms.colorspace_settings.name='Non-Color'; ms.pixels.foreach_set(packed.ravel())
ms.filepath_raw=str(OUT/'textures/TERMINAL_MetallicSmoothness.png'); ms.file_format='PNG'; ms.save()

atlas=material('RLYT_Surface','FFFFFF',.6)
n=atlas.node_tree.nodes; l=atlas.node_tree.links; p=n.get('Principled BSDF')
tex=n.new('ShaderNodeTexImage'); tex.image=base; l.new(tex.outputs['Color'],p.inputs['Base Color'])
texr=n.new('ShaderNodeTexImage'); texr.image=rough; l.new(texr.outputs['Color'],p.inputs['Roughness'])
texm=n.new('ShaderNodeTexImage'); texm.image=ms
sep=n.new('ShaderNodeSeparateColor'); l.new(texm.outputs['Color'],sep.inputs['Color']); l.new(sep.outputs['Red'],p.inputs['Metallic'])
for name in ('Body','Keys','EnterKey'):
    ob=export_objects[name]
    old=list(ob.data.materials)
    for index,m in enumerate(old):
        if m not in (ink,legend): ob.data.materials[index]=atlas

# Independent Enter cap has a meaningful local origin for a later key-press animation.
entry=export_objects['EnterKey']; scene.cursor.location=v(enter_center)
bpy.ops.object.select_all(action='DESELECT'); entry.select_set(True); bpy.context.view_layer.objects.active=entry
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

manifest={'asset':'RELAY Exit Terminal v01','unity_modified':False,'units':'metres','front':'Unity +Z',
          'root_parent':'Environment/EXIT_Module','root_local_position':[2.1,0,.55],
          'root_local_rotation':[0,0,0],'root_local_scale':[1,1,1],
          'world_status_canvas_position':[0,1.25,.245], 'world_status_canvas_rotation':[0,180,0],
          'world_status_canvas_scale':[.001,.001,.001], 'keyboard_key_count':key_count,'parts':[]}
for name,ob in export_objects.items():
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    # Compact duplicate slots from the shared atlas without altering polygons.
    old=list(ob.data.materials); unique=[]; remap={}
    for i,m in enumerate(old):
        if m not in unique: unique.append(m)
        remap[i]=unique.index(m)
    ids=[remap[p.material_index] for p in ob.data.polygons]
    ob.data.materials.clear()
    for m in unique: ob.data.materials.append(m)
    for face,idx in zip(ob.data.polygons,ids): face.material_index=idx
    localpos=list(P@ob.location); old_matrix=ob.matrix_world.copy(); ob.matrix_world=Matrix.Identity(4)
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/('TERMINAL_'+name+'.fbx')),
        use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,
        bake_space_transform=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,
        path_mode='RELATIVE',embed_textures=False)
    coordinates=[P@p.co for p in ob.data.vertices]
    manifest['parts'].append({'name':'TERMINAL_'+name,'file':'exports/TERMINAL_'+name+'.fbx',
        'child_local_position':localpos,'child_local_rotation':[0,180,0],'child_local_scale':[1,1,1],
        'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons),
        'bounds':[[min(p[i] for p in coordinates),max(p[i] for p in coordinates)] for i in range(3)],
        'materials':[m.name for m in ob.data.materials]})
    ob.matrix_world=old_matrix
manifest['triangles_total']=sum(p['triangles'] for p in manifest['parts'])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')

# Review studio, never exported. Offline glass remains blank in actual FBX.
def preview_material(name,h,strength=0):
    m=material('PREVIEW_ONLY_'+name,h,.5)
    if strength:
        p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Emission Color'].default_value=color(h)
        p.inputs['Emission Strength'].default_value=strength
    return m
phosphor=preview_material('Phosphor','A9CEAC',.8)
group='Screen'
before=set(bpy.data.objects)
lines=['SECURITY SEQUENCE','CORRUPTED','','01 : 2','02 : 6','03 : 15','04 : 31','05 : 56','06 : [ ? ]','','RECOVER MISSING VALUE','INPUT: [    ]_']
for i,line in enumerate(lines):
    if line: text('Review screen text '+str(i),line,(0,1.403-i*.026,.239),.018,phosphor)
for o in set(bpy.data.objects)-before:
    move(o,studio)
    o.visible_glossy=False
groundmat=preview_material('Ground','202B2B')
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001)); floor=bpy.context.object; floor.name='Review ground'; move(floor,studio); floor.data.materials.append(groundmat)
def aim(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,h):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=color(h)[:3]
    o=bpy.data.objects.new(name,d); studio.objects.link(o); o.location=loc; aim(o,(0,0,.9))
area('Large warm key',(-3,4,4),500,3,'F5EBDD')
area('Cool edge',(2,-2,3),600,2,'A9C7DB')
area('Soft front fill',(3,3,2),180,2,'D7E4DC')
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.16,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.23
d=bpy.data.cameras.new('ReviewCamera'); cam=bpy.data.objects.new('ReviewCamera',d); studio.objects.link(cam); scene.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=2.05
cam.location=(-2.9,4.5,2.45); aim(cam,(0,.055,.82))
scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=1100; scene.render.resolution_y=1300; scene.render.resolution_percentage=100
for im in (base,rough,ms): im.pack()
for ob in export_objects.values(): ob.select_set(False)
bpy.context.view_layer.objects.active=export_objects['Body']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_ExitTerminal.blend'))
print('MODEL_READY '+json.dumps({'triangles':manifest['triangles_total'],'keys':key_count}),flush=True)
if '--render' in sys.argv:
    scene.render.filepath=str(OUT/'previews/TERMINAL_hero.png'); bpy.ops.render.render(write_still=True)
    cam.location=(0,4.5,2.7); aim(cam,(0,.12,1.21)); cam.data.ortho_scale=1.12
    scene.render.resolution_x=1300; scene.render.resolution_y=1050
    scene.render.filepath=str(OUT/'previews/TERMINAL_details.png'); bpy.ops.render.render(write_still=True)
print('TERMINAL_BUILD_COMPLETE',flush=True)
