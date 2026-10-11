"""RELAY lighting assets. Blender 5.2 background only; no Unity project writes."""
import bpy, math, json, bmesh, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Euler

assert bpy.app.background, 'Run in a separate background Blender process.'
OUT = Path(__file__).resolve().parent
UNITY = Path(r'C:\Users\gonut\School_p2').resolve()
assert not OUT.is_relative_to(UNITY)
for name in ('exports', 'previews', 'checks'):
    (OUT / name).mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != 'Collection':
        bpy.data.collections.remove(collection)
src = bpy.data.collections.get('Collection')
src.name = '01_SOURCE_Edit_parts_here'
exports = bpy.data.collections.new('02_EXPORT_MESHES')
bpy.context.scene.collection.children.link(exports)
P = Matrix(((1,0,0),(0,0,1),(0,1,0)))
def v(x): return P @ Vector(x)
def hexrgb(s):
    def linear(a): return a/12.92 if a <= .04045 else ((a+.055)/1.055)**2.4
    return tuple(linear(int(s[i:i+2],16)/255) for i in (0,2,4))
def mat(name, color, metallic=0, rough=.5):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*hexrgb(color),1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = m.diffuse_color
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    return m
paint = mat('RLYL_Paint','777C72',0,.56)
frame = mat('RLYL_Frame','303B3D',0,.57)
steel = mat('RLYL_Steel','939C9C',.82,.35)
rubber = mat('RLYL_Rubber','191F1E',0,.83)
lens = mat('RLYL_Lens','E9EEF5',0,.38)
glass = mat('RLYL_Glass','CFE0D8',0,.12)
gp = glass.node_tree.nodes.get('Principled BSDF')
gp.inputs['Transmission Weight'].default_value = 1
gp.inputs['IOR'].default_value = 1.46
glass.diffuse_color = (*hexrgb('CFE0D8'),.12)
glass['Unity_Remapping'] = 'URP Lit Transparent Alpha 0.12, front faces, shadows off'
lens['Unity_Remapping'] = 'Existing M_LightFace (URP Unlit); assign ONLY this renderer to roomFixtures.lens'

def link(obj, collection=src):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collection.objects.link(obj)
def empty(name, parent=None, pos=(0,0,0)):
    o = bpy.data.objects.new(name,None); src.objects.link(o)
    o.empty_display_type='PLAIN_AXES'; o.empty_display_size=.12
    o.parent=parent; o.location=v(pos)
    return o
def finish(o, name, material, parent, bevel=0):
    o.name=name; link(o); o.parent=parent
    o.data.materials.append(material)
    if bevel:
        m=o.modifiers.new('Manufactured edge radius','BEVEL'); m.width=bevel; m.segments=3
    if o.type=='MESH':
        n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True; n.weight=35
    return o
def box(name,pos,size,material,parent,bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=v(pos))
    o=bpy.context.object; o.scale=v(size)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,material,parent,bevel)
def cylinder(name,pos,radius,depth,material,parent,axis=(0,1,0),vertices=32,bevel=.002):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=v(pos))
    o=bpy.context.object
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v(axis).normalized())
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return finish(o,name,material,parent,bevel)
def outline(w,l,r,steps=8):
    pts=[]
    for cx,cz,start in ((w/2-r,l/2-r,0),(-w/2+r,l/2-r,90),(-w/2+r,-l/2+r,180),(w/2-r,-l/2+r,270)):
        for j in range(steps+1):
            a=math.radians(start+j*90/steps)
            pts.append((cx+r*math.cos(a),cz+r*math.sin(a)))
    return pts
def mesh_obj(name,verts,faces,material,parent,bevel=0):
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata([v(a) for a in verts],[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); src.objects.link(o)
    return finish(o,name,material,parent,bevel)
def pan(name,sections,material,parent,offset=(0,0,0),bevel=.0015):
    # section: y, width, length, corner radius. Solid loft with no detached trim.
    pts=[outline(w,l,r) for y,w,l,r in sections]; n=len(pts[0])
    verts=[(x+offset[0],sec[0]+offset[1],z+offset[2]) for sec,ring in zip(sections,pts) for x,z in ring]
    faces=[tuple(range(n-1,-1,-1)),tuple((len(sections)-1)*n+i for i in range(n))]
    for k in range(len(sections)-1):
        for i in range(n): faces.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
    o=mesh_obj(name,verts,faces,material,parent,bevel)
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return o
def glass_shell(name,sections,material,parent,wall=.003):
    # Open at the ceiling side; thin closed shell leaves an air gap above the opal plate.
    outer=[outline(w,l,r) for y,w,l,r in sections]
    inner=[outline(w-2*wall,l-2*wall,max(.002,r-wall)) for y,w,l,r in sections]
    n=len(outer[0]); count=len(sections)
    verts=[(x,sec[0],z) for sec,pts in zip(sections,outer) for x,z in pts]
    verts += [(x,sec[0]+(wall if k else 0),z) for k,(sec,pts) in enumerate(zip(sections,inner)) for x,z in pts]
    off=n*count; faces=[]
    for k in range(count-1):
        for i in range(n):
            j=(i+1)%n
            faces += [(k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i),
                      (off+k*n+i,off+(k+1)*n+i,off+(k+1)*n+j,off+k*n+j)]
    for i in range(n):
        j=(i+1)%n; faces.append((i,off+i,off+j,j))
    faces += [tuple((count-1)*n+i for i in range(n)),
              tuple(off+(count-1)*n+i for i in range(n-1,-1,-1))]
    o=mesh_obj(name,verts,faces,material,parent,0)
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return o
def ring(name,y0,y1,w,l,r,thick,material,parent):
    outer=outline(w,l,r); inner=outline(w-2*thick,l-2*thick,max(.002,r-thick)); n=len(outer)
    verts=[(x,y,z) for y,pts in ((y0,outer),(y1,outer),(y0,inner),(y1,inner)) for x,z in pts]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    o=mesh_obj(name,verts,faces,material,parent,.001)
    for f in o.data.polygons: f.use_smooth=len(f.vertices)==4
    return o
def tube(name,points,radius,material,parent,closed=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=12
    cu.bevel_depth=radius; cu.bevel_resolution=3; cu.resolution_u=12; cu.use_fill_caps=True
    s=cu.splines.new('POLY'); s.points.add(len(points)-1)
    for p,c in zip(s.points,points): p.co=(*v(c),1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,cu); src.objects.link(o); o.parent=parent; cu.materials.append(material)
    return o
def screw(name,pos,parent,r=.010,material=steel):
    cylinder(name+'_washer',pos,r*1.35,.0025,material,parent,bevel=.0004)
    cylinder(name+'_head',(pos[0],pos[1]-.003,pos[2]),r,.006,material,parent,vertices=6,bevel=.001)
    box(name+'_slot',(pos[0],pos[1]-.0064,pos[2]),(r*1.1,.0006,.002),rubber,parent,.0002)

linear=empty('LIGHT_Linear_MountPlane_Y0')
lh=empty('LIGHT_LinearHousing',linear)
ll=empty('LIGHT_LinearLens',linear)
lg=empty('LIGHT_LinearGlass',linear)
for part in (lh,ll,lg): part['Pivot']='Top ceiling mount plane; Unity X width, Y up, Z length; output faces -Y'
# Mount feet are flush with ceiling; ribs support the pan below.
for z in (-.51,.51):
    for x in (-.19,.19):
        box('Mounting_foot',(x,-.005,z),(.10,.010,.09),steel,lh,.003)
        box('Mounting_web',(x,-.027,z),(.026,.038,.066),frame,lh,.002)
        screw('Mounting_bolt',(x,-.012,z),lh,.008)
pan('Folded_steel_pan',[(-.039,.49,1.58,.045),(-.052,.54,1.62,.055),(-.113,.51,1.58,.06),(-.128,.478,1.50,.06)],paint,lh)
# Longitudinal pressed stiffeners; shallow, functional, mostly visible at grazing angles.
for x in (-.166,.166):
    box('Pressed_stiffener',(x,-.044,0),(.034,.010,1.29),paint,lh,.004)
for z in (-.755,.755):
    box('End_service_cap',(0,-.080,z),(.49,.059,.080),frame,lh,.011)
    for x in (-.195,.195): screw('End_cap_fastener',(x,-.111,z),lh,.007)
ring('Continuous_dark_gasket',-.125,-.136,.485,1.505,.065,.020,rubber,lh)
ring('Diffuser_retaining_lip',-.133,-.146,.479,1.501,.064,.015,steel,lh)
pan('Opal_light_plate',[(-.136,.439,1.459,.050),(-.149,.431,1.445,.048),(-.153,.419,1.431,.047)],lens,ll,bevel=.001)
glass_shell('Protective_clear_cover',[(-.148,.447,1.461,.058),(-.162,.442,1.453,.056),(-.165,.425,1.436,.050)],glass,lg)
# Clips run from the pan side to the retaining lip, instead of floating beside it.
for side in (-1,1):
    for z in (-.53,0,.53):
        box('Latch_back',(side*.258,-.102,z),(.018,.044,.069),steel,lh,.003)
        box('Spring_latch',(side*.248,-.145,z),(.022,.052,.074),steel,lh,.004)
        box('Latch_return',(side*.231,-.168,z),(.039,.014,.074),steel,lh,.003)
        cylinder('Latch_pin',(side*.27,-.112,z),.008,.030,frame,lh,axis=(0,0,1),bevel=.001)
# Cable gland at one end of fixture, with short strain relief, all connected.
cylinder('Cable_gland_flange',(0,-.075,.818),.032,.035,frame,lh,axis=(0,0,1),vertices=12)
cylinder('Cable_gland_nut',(0,-.075,.843),.026,.029,steel,lh,axis=(0,0,1),vertices=6)
cylinder('Cable_strain_relief',(0,-.075,.875),.019,.037,rubber,lh,axis=(0,0,1),bevel=.003)
for z in (.863,.875,.887): cylinder('Strain_relief_rib',(0,-.075,z),.021,.004,rubber,lh,axis=(0,0,1),bevel=.001)
# A plain stamped service plate. No invented branding or large typography.
box('Service_plate',(0,-.115,-.757),(.15,.005,.039),steel,lh,.003)
for x in (-.061,.061): screw('Plate_rivet',(x,-.119,-.757),lh,.003)
for i in range(3): box('Stamp_mark',(-.038+i*.017,-.119,-.755),(.009,.001,.006),frame,lh,.0003)

bulk=empty('LIGHT_Bulkhead_MountPlane_Y0',pos=(.95,0,0))
bh=empty('LIGHT_BulkheadHousing',bulk)
bl=empty('LIGHT_BulkheadLens',bulk)
bg=empty('LIGHT_BulkheadGlass',bulk)
for part in (bh,bl,bg): part['Pivot']='Top ceiling mount plane; Unity X width, Y up, Z length; output faces -Y'
for z in (-.29,.29):
    for x in (-.162,.162):
        box('Cast_mounting_ear',(x,-.019,z),(.081,.038,.090),frame,bh,.008)
        screw('Ear_fastener',(x,-.039,z),bh,.008)
pan('Cast_oval_back',[(-.017,.362,.691,.16),(-.034,.422,.745,.189),(-.084,.412,.733,.185),(-.100,.388,.711,.174)],paint,bh,bevel=.002)
ring('Bulkhead_gasket',-.099,-.107,.385,.706,.174,.019,rubber,bh)
ring('Cast_retaining_ring',-.107,-.121,.394,.715,.177,.024,frame,bh)
pan('Bulkhead_opal_plate',[(-.106,.339,.660,.151),(-.120,.331,.650,.148)],lens,bl)
glass_shell('Bulkhead_cover',[(-.113,.345,.666,.154),(-.133,.337,.657,.150),(-.137,.324,.643,.146)],glass,bg)
# Cast retaining bosses plus captive bolts are placed on the rim.
for x in (-.169,.169):
    for z in (-.19,.19):
        cylinder('Captive_boss',(x,-.117,z),.018,.025,paint,bh,bevel=.002)
        screw('Captive_bolt',(x,-.132,z),bh,.008)
# Protective cage: perimeter and five arched transverse ribs meet the mounting rim.
cage_outline=outline(.372,.693,.168,12)
tube('Cage_perimeter',[(x,-.142,z) for x,z in cage_outline],.0065,steel,bh,True)
for z in (-.24,-.12,0,.12,.24):
    cap_offset=max(0,abs(z)-(.693/2-.168))
    width=2*(.372/2-.168+math.sqrt(.168**2-cap_offset**2))
    pts=[]
    for i in range(25):
        t=i/24
        pts.append(((t-.5)*width,-.141-.015*math.sin(math.pi*t),z))
    tube('Cage_transverse_rib',pts,.006,steel,bh)
tube('Cage_spine',[(0,-.143,-.341),(0,-.162,-.295),(0,-.162,.295),(0,-.143,.341)],.006,steel,bh)
for z in (-.327,.327):
    box('Cage_retaining_tab',(0,-.133,z),(.051,.026,.039),steel,bh,.004)
    screw('Cage_tab_screw',(0,-.15,z),bh,.006)
cylinder('Bulkhead_gland',(0,-.056,.380),.026,.039,frame,bh,axis=(0,0,1),vertices=12)
cylinder('Bulkhead_cable_seal',(0,-.056,.405),.017,.027,rubber,bh,axis=(0,0,1))

scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
manifest={'package':'RELAY LIGHTING v01','authoring':'Unity metres: X width, Y up, Z length; lens faces -Y',
          'mount_origin':'Ceiling contact plane at local Y=0',
          'manual_import_local_position':[0,.05,0],
          'parts':[],'source_parts':{}}
for part in (lh,ll,lg,bh,bl,bg):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.update()
    pivot=part.matrix_world.translation.copy()
    children=[o for o in part.children_recursive if o.type in {'MESH','CURVE','FONT'}]
    copies=[]
    for o in children:
        c=o.copy(); c.data=o.data.copy(); exports.objects.link(c)
        c.parent=None; c.matrix_world=o.matrix_world.copy(); c.select_set(True); copies.append(c)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.convert(target='MESH')
    if len(bpy.context.selected_objects)>1: bpy.ops.object.join()
    merged=bpy.context.object; merged.name=part.name+'_Export'
    scene.cursor.location=pivot
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Drop unused materials and repeated slots after joining, so lens uses exactly one slot.
    used=[]
    material_indices=[]
    for poly in merged.data.polygons:
        material=merged.data.materials[poly.material_index]
        if material not in used: used.append(material)
        material_indices.append(used.index(material))
    merged.data.materials.clear()
    for material in used: merged.data.materials.append(material)
    # Clearing Blender material slots resets face indices. Restore after rebuilding slots.
    for poly,index in zip(merged.data.polygons,material_indices):
        poly.material_index=index
    bm=bmesh.new(); bm.from_mesh(merged.data); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(merged.data); bm.free()
    saved=merged.matrix_world.copy(); merged.matrix_world=Matrix.Identity(4)
    fbx=OUT/'exports'/(part.name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
        add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    coords=[P @ vert.co for vert in merged.data.vertices]
    lo=[min(p[i] for p in coords) for i in range(3)]; hi=[max(p[i] for p in coords) for i in range(3)]
    info={'name':part.name,'fbx':str(fbx.relative_to(OUT)),
        'vertices':len(coords),'triangles':sum(len(p.vertices)-2 for p in merged.data.polygons),
        'unity_min':lo,'unity_max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)],
        'materials':[m.name for m in used],
        'material_face_counts':{m.name:sum(p.material_index==i for p in merged.data.polygons) for i,m in enumerate(used)},
        'uv_layers':len(merged.data.uv_layers)}
    manifest['parts'].append(info); manifest['source_parts'][part.name]=len(children)
    merged.matrix_world=saved; merged.hide_render=True; merged.hide_set(True)
exports.hide_render=True; exports.hide_viewport=True
scene.cursor.location=(0,0,0)
bpy.ops.object.select_all(action='DESELECT')
linear.select_set(True); bpy.context.view_layer.objects.active=linear
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=3
            area.spaces.active.region_3d.view_location=v((.40,-.06,0))
            area.spaces.active.clip_end=100
            area.spaces.active.shading.type='MATERIAL'
manifest['total_triangles']=sum(p['triangles'] for p in manifest['parts'])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_Lighting.blend'))
print('LIGHTING_BUILD_OK',json.dumps({'parts':len(manifest['parts']),'triangles':manifest['total_triangles']}))
