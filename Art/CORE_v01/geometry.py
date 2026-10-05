"""RELAY core geometry utilities. Standalone authoring: writes only beside this script.
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
source=coll('01_EDITABLE_CORE'); exports=coll('02_NEUTRAL_FBX_MESHES'); studio=coll('03_PREVIEW_ONLY')
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
paint=mat('RLYK_CasePaint','62655F',0,.56)
frame=mat('RLYK_FramePaint','303B3D',0,.57)
ivory=mat('RLYK_Enamel','C8C5B2',0,.60)
steel=mat('RLYK_Steel','939C9C',.82,.32)
oxid=mat('RLYK_DarkSteel','444B4A',.72,.48)
rubber=mat('RLYK_Rubber','191F1E',0,.83)
polymer=mat('RLYK_Bakelite','713E32',0,.43)
brass=mat('RLYK_Brass','8B7754',.73,.42)
ink=mat('RLYK_PrintDark','242B2A',0,.79)
printlight=mat('RLYK_PrintLight','DED8C3',0,.72)
ochre=mat('RLYK_SafetyPaint','AD8740',0,.49)
parts={}; mount_spec={}; active=None
def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None); source.objects.link(o); o.parent=parent; o.location=v(loc); o.empty_display_size=.045; return o
assembly=empty('RELAY_CORE_V01')
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


