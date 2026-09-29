"""Plate-only revision of the existing POWER v02 Blender asset.
Unity is never launched or modified. All non-plate source objects are checked.
"""
import bpy, math, os, json, shutil, hashlib, struct
from mathutils import Vector, Matrix

OUT=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.join(os.path.dirname(OUT),'POWER_v02')
for directory in ('exports','textures','previews'):
    os.makedirs(os.path.join(OUT,directory),exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE,'RELAY_POWER_v02.blend'))
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(u): return P @ Vector(u)
source=bpy.data.collections['01_EDITABLE_PARTS']
export_collection=bpy.data.collections['02_EXPORT_MESHES']
parent=bpy.data.objects['POWER_Cabinet']
scene=bpy.context.scene

# Identify the original plate and its own fasteners by both parent and position.
removed=[bpy.data.objects[name] for name in ('Engraved nameplate','Nameplate title','Nameplate rating')]
for ob in list(parent.children):
    u=P @ ob.location
    if ob.name.startswith(('Slotted steel fastener','Recessed screw slot')):
        if abs(u.y-.947)<.00001 and min(abs(u.x+.683),abs(u.x+.037))<.00001:
            removed.append(ob)
assert len(removed)==7,[o.name for o in removed]
removed_names=[o.name for o in removed]

def fingerprint(ob):
    h=hashlib.sha256()
    h.update(ob.type.encode())
    h.update(str(tuple(tuple(row) for row in ob.matrix_local)).encode())
    h.update(str(tuple(m.name if m else None for m in getattr(ob.data,'materials',[]))).encode())
    h.update(str((ob.hide_render,ob.hide_get(),ob.parent.name if ob.parent else None)).encode())
    if ob.type=='MESH':
        for vert in ob.data.vertices: h.update(struct.pack('3f',*vert.co))
        for face in ob.data.polygons:
            h.update(struct.pack(str(len(face.vertices))+'I',*face.vertices))
            h.update(struct.pack('I?',face.material_index,face.use_smooth))
        for uv in ob.data.uv_layers:
            for loop in uv.data: h.update(struct.pack('2f',*loop.uv))
    for mod in ob.modifiers: h.update(str((mod.name,mod.type)).encode())
    return h.hexdigest()
unchanged={ob.name:fingerprint(ob) for ob in source.objects if ob not in removed}
for ob in removed: bpy.data.objects.remove(ob,do_unlink=True)

def material(name,code,metallic,rough):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    def lin(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    rgba=(*[lin(int(code[i:i+2],16)/255) for i in (0,2,4)],1)
    mat.diffuse_color=rgba; bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=rgba
    bs.inputs['Metallic'].default_value=metallic; bs.inputs['Roughness'].default_value=rough
    return mat
enamel=material('RLY02_NameplateEnamel','30352F',0,.62)
lettering=material('RLY02_NameplatePrint','C8C7B4',0,.76)
steel=bpy.data.materials['RLY02_Steel']; ink=bpy.data.materials['RLY02_Ink']
def register(ob,name,position,mat):
    for collection in list(ob.users_collection): collection.objects.unlink(ob)
    source.objects.link(ob); ob.name=name; ob.parent=parent; ob.location=v(position)
    ob.data.materials.append(mat); return ob

# A 350 x 100 x 3 mm folded-edge-free enamel identification plate.
width=.35; height=.10; thickness=.003; radius=.006
outline=[]
for cx,cy,start in ((width/2-radius,height/2-radius,0),
                    (-width/2+radius,height/2-radius,90),
                    (-width/2+radius,-height/2+radius,180),
                    (width/2-radius,-height/2+radius,270)):
    for step in range(6):
        angle=math.radians(start+step*90/5)
        outline.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
n=len(outline)
vertices=[tuple(v((x,y,z))) for z in (-thickness/2,thickness/2) for x,y in outline]
faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
for i in range(n): j=(i+1)%n; faces.append((i,j,n+j,n+i))
mesh=bpy.data.meshes.new('Enamel plate sheet'); mesh.from_pydata(vertices,[],faces); mesh.update()
plate=bpy.data.objects.new('POWER compact nameplate',mesh); source.objects.link(plate)
plate.parent=parent; plate.location=v((-.30,.945,-.5155)); mesh.materials.append(enamel)
bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True); bpy.context.view_layer.objects.active=plate
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
bev=plate.modifiers.new('Fine enamel edge','BEVEL'); bev.width=.00035; bev.segments=2
plate.modifiers.new('Plate normals','WEIGHTED_NORMAL')

font=bpy.data.fonts.load('C:/Windows/Fonts/bahnschrift.ttf')
curve=bpy.data.curves.new('POWER print','FONT'); curve.body='POWER'; curve.font=font
curve.size=.06; curve.align_x='CENTER'; curve.align_y='CENTER'; curve.extrude=0; curve.resolution_u=3
word=bpy.data.objects.new('POWER printed lettering',curve); source.objects.link(word)
word.parent=parent; word.location=v((-.3,.945,-.5173)); word.rotation_euler=(math.pi/2,0,0)
curve.materials.append(lettering)
bpy.context.view_layer.update()
initial_bb=[word.matrix_world @ Vector(corner) for corner in word.bound_box]
initial_height=max(c.z for c in initial_bb)-min(c.z for c in initial_bb)
assert initial_height>0,initial_height
curve.size*=.035/initial_height
bpy.context.view_layer.update()
bb=[word.matrix_world @ Vector(corner) for corner in word.bound_box]
word.location.z+=.945-(min(c.z for c in bb)+max(c.z for c in bb))/2
# Two practical fasteners, no raised border or secondary microtext.
for x,angle in ((-.453,19),(-.147,-34)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.0047,depth=.002)
    head=register(bpy.context.object,'Nameplate slotted screw',(x,.945,-.518),steel)
    head.rotation_euler=(math.pi/2,0,0)
    bevel=head.modifiers.new('Screw edge','BEVEL'); bevel.width=.0004; bevel.segments=2
    head.modifiers.new('Screw normals','WEIGHTED_NORMAL')
    bpy.ops.mesh.primitive_cube_add(size=1)
    slot=register(bpy.context.object,'Nameplate screw slot',(x,.945,-.5191),ink)
    slot.scale=v((.0065,.00085,.00025)); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    slot.rotation_euler=(0,math.radians(-angle),0)

# Convert only the new word to keep the distributed model font-independent.
bpy.ops.object.select_all(action='DESELECT'); word.select_set(True); bpy.context.view_layer.objects.active=word
bpy.ops.object.convert(target='MESH')
assert all(fingerprint(bpy.data.objects[name])==value for name,value in unchanged.items())

# Carry the other eleven FBX parts over byte-for-byte. Only cabinet is re-exported.
copied_hashes={}
for directory in ('exports','textures'):
    for filename in os.listdir(os.path.join(BASE,directory)):
        if directory=='exports' and filename=='POWER_Cabinet.fbx': continue
        origin=os.path.join(BASE,directory,filename)
        if not os.path.isfile(origin): continue
        target=os.path.join(OUT,directory,filename); shutil.copy2(origin,target)
        def digest(path):
            with open(path,'rb') as f: return hashlib.sha256(f.read()).hexdigest()
        assert digest(origin)==digest(target)
        copied_hashes[directory+'/'+filename]=digest(target)
old_export=bpy.data.objects['POWER_Cabinet_EXPORT']; bpy.data.objects.remove(old_export,do_unlink=True)
copies=[]; bpy.context.view_layer.update()
for ob in list(parent.children):
    if ob.type!='MESH': continue
    duplicate=ob.copy(); duplicate.data=ob.data.copy(); export_collection.objects.link(duplicate)
    duplicate.parent=None; duplicate.matrix_world=ob.matrix_world.copy(); copies.append(duplicate)
bpy.ops.object.select_all(action='DESELECT')
for ob in copies: ob.select_set(True)
bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.convert(target='MESH')
for ob in list(bpy.context.selected_objects):
    if not ob.data.uv_layers:
        others=[o for o in bpy.context.selected_objects if o!=ob]
        for other in others: other.select_set(False)
        bpy.context.view_layer.objects.active=ob; bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.01)
        bpy.ops.object.mode_set(mode='OBJECT')
        for other in others: other.select_set(True)
bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join()
cabinet=bpy.context.object; cabinet.name='POWER_Cabinet_EXPORT'
scene.cursor.location=parent.matrix_world.translation; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
saved=cabinet.matrix_world.copy(); cabinet.matrix_world=Matrix.Identity(4)
export_path=os.path.join(OUT,'exports','POWER_Cabinet.fbx')
bpy.ops.export_scene.fbx(filepath=export_path,use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,
    mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
cabinet.matrix_world=saved; cabinet.hide_render=True; cabinet.hide_set(True)

# Check absolute vertex bounds, including the origin, after FBX round-trip.
def bounds(coords): return [[min(c[i] for c in coords),max(c[i] for c in coords)] for i in range(3)]
expected=bounds([vert.co for vert in cabinet.data.vertices]); previous=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=export_path); imported=set(bpy.data.objects)-previous
actual=bounds([ob.matrix_world @ vert.co for ob in imported if ob.type=='MESH' for vert in ob.data.vertices])
error=max(abs(a-b) for p,q in zip(expected,actual) for a,b in zip(p,q)); assert error<.0001,error
assert all(ob.data.uv_layers for ob in imported if ob.type=='MESH')
for ob in imported: bpy.data.objects.remove(ob,do_unlink=True)
assert all(fingerprint(bpy.data.objects[name])==value for name,value in unchanged.items())
with open(os.path.join(BASE,'manifest.json'),encoding='utf-8') as f: manifest=json.load(f)
manifest['asset']='RELAY POWER v02 - compact nameplate'
manifest['revision_scope']='POWER nameplate and its two fixing screws only'
for item in manifest['parts']:
    if item['name']=='POWER_Cabinet': item['triangles']=sum(len(p.vertices)-2 for p in cabinet.data.polygons)
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,indent=2)
with open(os.path.join(OUT,'nameplate_validation.json'),'w',encoding='utf-8') as f:
    json.dump({'unchanged_source_objects_checked':len(unchanged),'unchanged_export_parts':11,
       'copied_files_sha256':copied_hashes,'cabinet_roundtrip_bounds_error_m':error,
       'unity_modified':False,'unity_runtime_tested':False,
       'nameplate_dimensions_m':[width,height,thickness],'capital_height_m':.035},f,indent=2)

bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:
        im.filepath='//textures/'+os.path.basename(im.filepath); im.pack()
camera=scene.camera
scene.cycles.samples=20; scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=1200; scene.render.resolution_y=1500
scene.render.filepath=os.path.join(OUT,'previews','POWER_nameplate_hero.png')
bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True); bpy.context.view_layer.objects.active=plate
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'RELAY_POWER_v02_nameplate.blend'))
bpy.ops.render.render(write_still=True)
camera.location=(-.13,-3,1.19)
target=v((-.30,.925,-.52)); camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=.65
scene.render.resolution_x=1100; scene.render.resolution_y=620
scene.render.filepath=os.path.join(OUT,'previews','POWER_nameplate_detail.png')
bpy.ops.render.render(write_still=True)
print('NAMEPLATE_ONLY_COMPLETE',len(unchanged),'unchanged source objects;',error,'FBX bounds error')
