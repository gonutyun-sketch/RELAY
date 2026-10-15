"""Small RELAY hint asset. Standalone Blender only; never touches Unity."""
import bpy, math, json, zipfile
from pathlib import Path
from mathutils import Vector
import numpy as np

OUT = Path(__file__).resolve().parent
assert not OUT.is_relative_to(Path(r'C:\Users\gonut\School_p2'))
assert bpy.app.background
for name in ('exports', 'textures', 'previews', 'checks'):
    (OUT / name).mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.unit_settings.system = 'METRIC'
s.unit_settings.scale_length = 1
s.render.engine = 'CYCLES'
s.cycles.samples = 24
s.cycles.use_denoising = True
s.render.threads_mode = 'FIXED'
s.render.threads = 8
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGBA'
s.render.image_settings.color_depth = '8'
s.view_settings.view_transform = 'Standard'
s.render.film_transparent = True
s.world.color = (.15, .15, .15)

def linear(rgb):
    return tuple(c / 12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb)

def mat(name, rgb, rough=.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*linear(rgb), 1)
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = m.diffuse_color
    p.inputs['Roughness'].default_value = rough
    return m

def camera(name, pos, target, scale):
    d = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, d)
    s.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type = 'ORTHO'
    d.ortho_scale = scale
    d.lens = 50
    s.camera = o
    return o

def render(path, w, h):
    s.render.resolution_x, s.render.resolution_y = w,h
    s.render.resolution_percentage = 100
    s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

def mesh(name, verts, faces, material):
    d = bpy.data.meshes.new(name)
    d.from_pydata(verts, [], faces)
    d.update()
    o = bpy.data.objects.new(name, d)
    s.collection.objects.link(o)
    o.data.materials.append(material)
    return o

# Render the installed handwriting font into pixels. Font files are not shipped.
ink = mat('PRINT_SOURCE_Ink', (.15,.16,.145))
p = ink.node_tree.nodes.get('Principled BSDF')
p.inputs['Emission Color'].default_value = (*linear((.15,.16,.145)), 1)
p.inputs['Emission Strength'].default_value = 1
p.inputs['Base Color'].default_value = (0,0,0,1)
font = bpy.data.fonts.load(r'C:\Windows\Fonts\segoepr.ttf')
texts=[]
for value,z,angle,x in [('70',.057,-1.7,-.004),('30',-.063,1.1,.003)]:
    c=bpy.data.curves.new('Print_'+value,'FONT')
    c.body=value; c.font=font; c.align_x='CENTER'; c.align_y='CENTER'
    c.size=.095; c.space_character=1.12; c.resolution_u=8
    o=bpy.data.objects.new('Print_'+value,c); s.collection.objects.link(o)
    o.location=(x,0,z)
    o.rotation_euler=(math.pi/2,0,0)
    from mathutils import Quaternion
    o.rotation_mode='QUATERNION'
    o.rotation_quaternion=Quaternion((1,0,0),math.pi/2) @ Quaternion((0,0,1),math.radians(angle))
    o.data.materials.append(ink); texts.append(o)
printcam=camera('PrintCamera',(0,-1,0),(0,0,0),.42)
render(OUT/'checks'/'digits_source.png',1000,1400)

# Build an unlit base-color texture with understated paper grain.
im=bpy.data.images.load(str(OUT/'checks'/'digits_source.png'),check_existing=False)
pixels=np.empty(1000*1400*4,dtype=np.float32)
im.pixels.foreach_get(pixels)
pixels=pixels.reshape((1400,1000,4))
rng=np.random.default_rng(7030)
yy,xx=np.mgrid[0:1400,0:1000]
u=xx/999.; v=yy/1399.
base=np.array(linear((.875,.85,.775)),dtype=np.float32)
edge=(np.maximum(abs(u-.5)-.43,0)+np.maximum(abs(v-.5)-.43,0))*.065
grain=rng.normal(0,.0028,(1400,1000))
cloud=.003*np.sin(u*19+v*7)*np.cos(v*13-u*3)
paper=np.clip(base[None,None,:]+(grain+cloud-edge)[...,None],0,1)
alpha=pixels[...,3:4]
# PNG load yields straight alpha; use a fixed ink color for predictable export.
mixed=paper*(1-alpha)+np.array(linear((.15,.16,.145)))[None,None,:]*alpha
rgba=np.concatenate((mixed,np.ones((1400,1000,1))),axis=2).astype(np.float32)
tex=bpy.data.images.new('Paper_Print_BaseColor',width=1000,height=1400,alpha=False)
tex.pixels.foreach_set(rgba.ravel())
tex.filepath_raw=str(OUT/'textures'/'Paper_Print_BaseColor.png')
tex.file_format='PNG'; tex.save()
for o in texts: bpy.data.objects.remove(o,do_unlink=True)
bpy.data.objects.remove(printcam,do_unlink=True)
bpy.data.images.remove(im)

paper_mat=mat('RLYP_Paper',(.875,.85,.775),.94)
node=paper_mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image=tex; node.label='Use as URP Base Map; leave Base Color white'
paper_mat.node_tree.links.new(node.outputs['Color'],paper_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
tape_mat=mat('RLYP_Tape',(.70,.64,.48),.88)

def depth(x,z):
    # Mostly flat sheet, a soft lifted lower edge and one mild folded corner.
    bottom=max(0,(-z-.10)/.11)
    corner=max(0,(x-.075)+(-z-.145))
    return .0003+.0014*bottom*bottom+.055*corner+.00025*math.sin(x*18)*math.sin(z*13)

nx,nz=20,28
verts=[]; faces=[]
for j in range(nz+1):
    z=-.21+.42*j/nz
    for i in range(nx+1):
        x=-.15+.30*i/nx
        # Tiny uneven edge; shape stays near the nominal 30 x 42 cm rectangle.
        if i==0: x+=.00025*math.sin(j*1.7)
        if i==nx: x+=.0003*math.sin(j*2.4)
        verts.append((x,-depth(x,z),z))
for j in range(nz):
    for i in range(nx):
        a=j*(nx+1)+i
        faces.append((a,a+1,a+1+nx+1,a+nx+1))
page=mesh('Paper_Sheet',verts,faces,paper_mat)
uv=page.data.uv_layers.new(name='UVMap')
for f in page.data.polygons:
    for loop in f.loop_indices:
        idx=page.data.loops[loop].vertex_index
        uv.data[loop].uv=(idx%(nx+1)/nx,idx//(nx+1)/nz)
    f.use_smooth=True
solid=page.modifiers.new('Paper thickness 0.35mm','SOLIDIFY')
solid.thickness=.00035; solid.offset=-1

# A short piece of opaque masking tape bridges the top edge onto the wall.
verts=[]; faces=[]
for j in range(4):
    for i in range(9):
        x=-.066+.092*i/8
        z=.197+.028*j/3+.0012*math.sin(i*.4)
        d=depth(x,min(z,.21)) if z<=.21 else .0001
        d+=.0005+.00018*math.sin(i*1.8+j)
        verts.append((x,-d,z))
for j in range(3):
    for i in range(8):
        a=j*9+i; faces.append((a,a+1,a+10,a+9))
tape=mesh('Top_MaskingTape',verts,faces,tape_mat)
solid=tape.modifiers.new('Tape thickness 0.12mm','SOLIDIFY')
solid.thickness=.00012; solid.offset=-1

# Keep two editable parts and export a single centered mesh with two slots.
bpy.ops.object.select_all(action='DESELECT')
copies=[]
for o in (page,tape):
    cp=o.copy(); cp.data=o.data.copy(); s.collection.objects.link(cp)
    cp.select_set(True); copies.append(cp)
bpy.context.view_layer.objects.active=copies[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.join()
game=bpy.context.object; game.name='POWER_HintPaper'
s.cursor.location=(0,0,0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/'POWER_HintPaper.fbx'),
    use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',
    add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
game.hide_render=True; game.hide_set(True)

def area(name,pos,power,size,target):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); s.collection.objects.link(o); o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
key=area('Softbox',(-.38,-.65,.6),35,.65,(0,0,0))
fill=area('Fill',(.45,-.35,.1),7,.5,(0,0,0))
ui=camera('UI_PreviewCamera',(0,-1,0),(0,0,.007),.46)
s.view_settings.view_transform='AgX'
render(OUT/'previews'/'Paper_UI.png',1000,1400)

wallmat=mat('REVIEW_ONLY_Wall',(.22,.25,.25),.95)
wall=mesh('REVIEW_ONLY_Wall',[(-2,.004,-2),(2,.004,-2),(2,.004,2),(-2,.004,2)],[(0,1,2,3)],wallmat)
hero=camera('ReviewCamera',(.20,-.9,.10),(0,0,.005),.54)
s.render.film_transparent=False
s.view_settings.view_transform='AgX'
render(OUT/'previews'/'POWER_HintPaper_preview.png',1200,1400)

# Source is portable: the only texture is packed, and text is already pixels.
tex.pack()
for f in list(bpy.data.fonts):
    if f.users==0 and f.name!='Bfont': bpy.data.fonts.remove(f)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'POWER_HintPaper.blend'))

# FBX round-trip checks without opening Unity.
original=[game.matrix_world@v.co for v in game.data.vertices]
before=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(OUT/'exports'/'POWER_HintPaper.fbx'))
imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
assert len(imported)==1
other=[imported[0].matrix_world@v.co for v in imported[0].data.vertices]
def bounds(points):
    return [[min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]]
a,b=bounds(original),bounds(other)
error=max(abs(a[i][j]-b[i][j]) for i in range(2) for j in range(3))
assert error<.00005, error
assert all(math.isfinite(float(n)) for v in original for n in v)
assert len(game.data.materials)==2
assert len(game.data.uv_layers)>=1
assert list(game.location)==[0,0,0]
assert sum(p.normal.y<-.5 for p in page.data.polygons)==len(page.data.polygons)
result={'dimensions_m':{'width':a[1][0]-a[0][0],'height_including_tape':a[1][2]-a[0][2],'depth':a[1][1]-a[0][1]},
    'vertices':len(game.data.vertices),'triangles':sum(len(p.vertices)-2 for p in game.data.polygons),
    'material_slots':[m.name for m in game.data.materials],'fbx_roundtrip_bounds_error_m':error,
    'printed_text':['70','30'],'front_authored':'-Z in Unity design coordinates; Blender -Y',
    'unity_visual_child_rotation_degrees':[0,180,0], 'unity_project_modified':False}
(OUT/'checks'/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('RELAY_PAPER_DONE '+json.dumps(result))
