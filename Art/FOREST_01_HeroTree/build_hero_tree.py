"""RELAY forest pass 01: irregular mountain spruce. Art-only, outside Unity."""
import bpy, bmesh, math, random, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.noise import noise_vector

OUT=Path(__file__).resolve().parent
PROJECT=Path('C:/Users/gonut/School_p2').resolve()
assert not OUT.is_relative_to(PROJECT)
assert bpy.app.background
for folder in ('exports','previews','checks'): (OUT/folder).mkdir(parents=True,exist_ok=True)
watched=[PROJECT/'Assets/Scenes/Startup_Graybox.unity',*sorted((PROJECT/'Assets/RELAY/Scripts').glob('*.cs'))]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
P=Matrix(((1,0,0),(0,0,1),(0,1,0)))
UP=Vector((0,1,0));R=random.Random(61009)

def col(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
def linear(h):
    a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in a)
def mat(name,h,rough):
    m=bpy.data.materials.new(name);m.diffuse_color=(*linear(h),1);m.use_nodes=True
    ns=m.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfPrincipled');output=ns.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(bs.outputs['BSDF'],output.inputs['Surface']);bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough
    return m,bs
def texture(m,name,space='sRGB'):
    p=OUT/'textures'/name
    if not p.exists():raise FileNotFoundError(p)
    im=bpy.data.images.load(str(p),check_existing=True);im.colorspace_settings.name=space
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.label=name;im.pack();return tex

bark,bs=mat('RLYF_SpruceBark','686153',.91)
tex=texture(bark,'RLYF_Bark_BaseColor.png');bark.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
n=texture(bark,'RLYF_Bark_Normal.png','Non-Color');nm=bark.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7
bark.node_tree.links.new(n.outputs['Color'],nm.inputs['Color']);bark.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
r=texture(bark,'RLYF_Bark_Roughness.png','Non-Color');bark.node_tree.links.new(r.outputs['Color'],bs.inputs['Roughness'])
wood,_=mat('RLYF_ExposedWood','9D8970',.95)
leaf,bs=mat('RLYF_SpruceNeedles','435546',.81)
tex=texture(leaf,'RLYF_Needles_Atlas.png');leaf.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
# A hard alpha mask avoids sorting artifacts; matches the Unity alpha-clip handoff.
cmp=leaf.node_tree.nodes.new('ShaderNodeMath');cmp.operation='GREATER_THAN';cmp.inputs[1].default_value=.45
leaf.node_tree.links.new(tex.outputs['Alpha'],cmp.inputs[0]);leaf.node_tree.links.new(cmp.outputs[0],bs.inputs['Alpha'])
leaf.use_backface_culling=False
bs.inputs['Subsurface Weight'].default_value=0
bs.inputs['Specular IOR Level'].default_value=.22

class MeshBuilder:
    def __init__(self):self.v=[];self.f=[];self.uv=[];self.mi=[]
    def face(self,indices,uv,mi=0):self.f.append(tuple(indices));self.uv.extend(uv);self.mi.append(mi)
    def tube(self,points,radii,sides=9,groove=.025,phase=0,cap=True):
        pts=[Vector(p) for p in points];base=len(self.v);distance=0;vvals=[]
        for j,(p,rad) in enumerate(zip(pts,radii)):
            t=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
            ref=UP if abs(t.dot(UP))<.94 else Vector((1,0,0))
            a=t.cross(ref).normalized();b=t.cross(a).normalized()
            if j:distance+=(p-pts[j-1]).length
            vvals.append(distance/2)
            for i in range(sides):
                ang=math.tau*i/sides
                wav=1+groove*(math.sin(ang*7+phase)+.48*math.sin(ang*13+distance*.8))
                self.v.append(tuple(p+rad*wav*(a*math.cos(ang)+b*math.sin(ang))))
        # Circumference UV uses average tube radius; preserve the real vertical texture scale.
        circumference=max(.09,math.tau*sum(radii)/len(radii))
        for j in range(len(pts)-1):
            for i in range(sides):
                ni=(i+1)%sides
                ids=(base+j*sides+i,base+j*sides+ni,base+(j+1)*sides+ni,base+(j+1)*sides+i)
                self.face(ids,[(i/sides*circumference,vvals[j]),((i+1)/sides*circumference,vvals[j]),((i+1)/sides*circumference,vvals[j+1]),(i/sides*circumference,vvals[j+1])])
        if cap:
            for ring,rev in ((0,True),(len(pts)-1,False)):
                ix=list(range(sides));ix=ix[::-1] if rev else ix
                self.face([base+ring*sides+i for i in ix],[(.5+.45*math.cos(i*math.tau/sides),.5+.45*math.sin(i*math.tau/sides)) for i in ix],1)
    def spray(self,anchor,direction,normal,length,width,tile,roll=0,bend=.09,sections=3):
        origin=Vector(anchor);axis=Vector(direction).normalized();normal=Vector(normal)
        side=axis.cross(normal).normalized()
        if side.length<.1:side=axis.cross(Vector((1,0,0))).normalized()
        face_n=side.cross(axis).normalized()
        s=side*math.cos(roll)+face_n*math.sin(roll);n=s.cross(axis).normalized()
        base=len(self.v)
        for j in range(sections+1):
            t=j/sections;c=origin+axis*(length*t)+n*(bend*length*math.sin(t*math.pi*.8))
            for edge in (-1,1):self.v.append(tuple(c+s*width*.5*edge))
        tx=tile%2;ty=tile//2
        for j in range(sections):
            def uv(x,y):return ((tx+x)*.5,(ty+y)*.5)
            self.face((base+j*2,base+j*2+1,base+(j+1)*2+1,base+(j+1)*2),[uv(0,j/sections),uv(1,j/sections),uv(1,(j+1)/sections),uv(0,(j+1)/sections)])
    def make(self,name,collection,mats,recalc=False):
        me=bpy.data.meshes.new(name);me.from_pydata([P@Vector(v) for v in self.v],[],self.f);me.update()
        for m in mats:me.materials.append(m)
        for f,mi in zip(me.polygons,self.mi):f.material_index=mi;f.use_smooth=recalc
        uv=me.uv_layers.new(name='UVMap')
        for loop,xy in zip(uv.data,self.uv):loop.uv=xy
        if recalc:
            bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
        else:
            # Handedness conversion reverses winding. Reverse the leaves once.
            me.flip_normals()
        me.update();o=bpy.data.objects.new(name,me);collection.objects.link(o);return o

def trunk(y):return Vector((.08*math.sin(y*.62)+.014*y,y,.065*math.sin(y*.78)+.004*y))
def radius(y):return .30*(max(.012,1-y/11.85)**.85)+.26*math.exp(-y*2.3)
def bez(a,b,c,t):return (1-t)**2*a+2*t*(1-t)*b+t*t*c
segments=[];sprays=[]
# The tree is not generated as identical radial tiers. Each major limb gets its own sweep and gap.
levels=[2.05,2.75,3.43,4.2,4.98,5.67,6.35,7.08,7.75,8.40,9.00,9.61,10.16,10.68,11.14]
for level,y in enumerate(levels):
    count=R.randint(5,7) if level<10 else R.randint(4,6)
    turn=R.uniform(0,math.tau)
    for i in range(count):
        if level in (1,4,7) and i==2:continue
        h=y+R.uniform(-.35,.33);ang=turn+math.tau*i/count+R.uniform(-.28,.28)
        d=Vector((math.cos(ang),0,math.sin(ang)))
        sweep=Vector((-d.z,0,d.x))*R.uniform(-.2,.2)
        length=(2.85*(max(.04,1-h/12)**.57))*R.uniform(.8,1.14)
        if level==0:length*=.83
        root=trunk(h);tip=root+d*length+sweep+UP*(R.uniform(-.6,.25)+.22*(h/12))
        ctrl=root+d*length*.46+UP*(-.48 if h<8 else -.18)
        pts=[bez(root,ctrl,tip,t/9) for t in range(10)]
        r0=.061*(1-h/13)**.7*R.uniform(.8,1.13)
        segments.append((pts,[r0*(1-j/10)**1.2+.004 for j in range(10)],'primary'))
        for j in range(2,10):
            t=j/10;origin=bez(root,ctrl,tip,t)
            tangent=(bez(root,ctrl,tip,min(1,t+.03))-origin).normalized()
            across=UP.cross(tangent).normalized()
            for sign in (-1,1):
                u=R.uniform(.04,.16);side=across*sign
                slen=(.68*(1-t)+.19)*R.uniform(.85,1.18)
                end=origin+tangent*slen*.48+side*slen+UP*R.uniform(-.32,.12)
                mid=(origin+end)*.5-UP*.025
                ps=[bez(origin,mid,end,k/4) for k in range(5)]
                segments.append((ps,[.011*(1-k/5)**1.4+.0018 for k in range(5)],'secondary'))
                for k in (1,2,3):
                    q=ps[k];forward=(ps[k+1]-q).normalized()
                    stemdir=(forward+UP*R.uniform(-.34,.10)+side*R.uniform(-.1,.15)).normalized()
                    l=R.uniform(.68,.95)*(1-.40*h/12)
                    # Alpha tile margin is included; overlap its stem with actual twig geometry.
                    q=q-stemdir*l*.06
                    sprays.append((q,stemdir,UP,l,l*.46,R.randrange(4),R.uniform(-.85,.85),R.uniform(.06,.18)))
                    if k==2:sprays.append((q,stemdir-UP*.35,UP,l*.92,l*.44,R.randrange(4),1.28+R.uniform(-.3,.3),.11))
        for k in (6,8,9):
            q=pts[k];direction=(pts[min(9,k+1)]-pts[k-1]).normalized();l=R.uniform(.64,.86)*(1-.35*h/12)
            sprays.append((q-direction*l*.1,direction+UP*.08,UP,l,l*.40,R.randrange(4),R.uniform(-.5,.5),.07))

# Dead lower limbs, a broken side branch and a single asymmetric leader sell the scale at eye height.
for i in range(11):
    y=R.uniform(.85,2.4);a=R.uniform(0,math.tau);d=Vector((math.cos(a),0,math.sin(a)));p=trunk(y)
    leng=R.uniform(.18,.8);ps=[p,p+d*leng*.38-UP*.04,p+d*leng-UP*R.uniform(.06,.28)]
    segments.append((ps,[.032,.021,.009],'dead'))
    if i%2==0:
        q=ps[1];segments.append(([q,q+d*.2+Vector((-d.z,.12,d.x))*.25],[.012,.003],'dead'))

roots=[]
for i in range(9):
    a=math.tau*i/9+R.uniform(-.15,.15);d=Vector((math.cos(a),0,math.sin(a)))
    l=R.uniform(.72,1.6);side=Vector((-d.z,0,d.x))*R.uniform(-.25,.25)
    ps=[UP*.43,d*.31+UP*.16,d*l*.63+side*.4-UP*.005,d*l+side-UP*.075]
    roots.append((ps,[.18,.135,.06,.009]))
    if i%2==0:
        q=ps[2];roots.append(([q,q+d*.35+side*.8-UP*.04,q+d*.57+Vector((-d.z,0,d.x))*.23-UP*.055],[.06,.029,.008]))

manifest={'name':'RELAY Forest 01 - mountain spruce A','stage':'One reusable hero tree; forest terrain, rocks, additional trees and Unity placement deferred','metres':True,'unity_root':'trunk base at (0,0,0), P0 R0 S1','layers':[],'spray_count_source':len(sprays),'source_hashes_before':before}
lodcols=[]
for lod in range(3):
    coll=col('0%d_SPRUCE_A_LOD%d'%(lod+1,lod));lodcols.append(coll)
    wb=MeshBuilder();fb=MeshBuilder()
    n=(86,49,26)[lod];sides=(36,22,12)[lod]
    ys=[11.82*j/(n-1) for j in range(n)]
    wb.tube([trunk(y) for y in ys],[radius(y) for y in ys],sides,.065,1.7)
    for ps,rs in roots:wb.tube(ps,rs,(16,10,6)[lod],.09,1.2)
    for index,(ps,rs,kind) in enumerate(segments):
        if lod==2 and kind=='secondary' and index%2:continue
        if lod==2 and kind=='dead' and index%2:continue
        if lod>0 and len(ps)>4:
            step=2 if lod==1 else 3;indices=list(range(0,len(ps),step))
            if indices[-1]!=len(ps)-1:indices.append(len(ps)-1)
            ps=[ps[k] for k in indices];rs=[rs[k] for k in indices]
        wb.tube(ps,rs,(9,6,4)[lod] if kind=='primary' else (6,5,3)[lod],.035)
    for index,spray in enumerate(sprays):
        # Deterministic thinning retains a consistent silhouette at each distance.
        keep=(index*0.61803398875)%1
        if lod==1 and keep>.65:continue
        if lod==2 and keep>.30:continue
        q,d,n,l,w,t,r,b=spray;factor=(1,1.12,1.34)[lod]
        fb.spray(q,d,n,l*factor,w*factor,t,r,b,sections=(3,2,1)[lod])
    objs=[wb.make('SPRUCE_A_Wood_LOD%d'%lod,coll,[bark,wood],True),fb.make('SPRUCE_A_Needles_LOD%d'%lod,coll,[leaf],False)]
    info={'level':lod,'parts':[]}
    for o in objs:
        me=o.data;me.calc_loop_triangles();coords=[P@v.co for v in me.vertices]
        assert len(me.uv_layers.active.data)==len(me.loops)
        assert all(math.isfinite(c) for v in coords for c in v)
        assert all((Vector(me.vertices[t.vertices[1]].co)-me.vertices[t.vertices[0]].co).cross(Vector(me.vertices[t.vertices[2]].co)-me.vertices[t.vertices[0]].co).length>1e-12 for t in me.loop_triangles)
        info['parts'].append({'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'min':[min(v[k] for v in coords) for k in range(3)],'max':[max(v[k] for v in coords) for k in range(3)],'materials':[m.name for m in me.materials]})
    info['total_triangles']=sum(p['triangles'] for p in info['parts']);manifest['layers'].append(info)
    turn=Matrix.Rotation(math.pi,4,'Z')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.data.transform(turn);o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/('FOREST_Spruce_A_LOD%d.fbx'%lod)),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=True,mesh_smooth_type='FACE',bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    for o in objs:o.data.transform(turn.inverted());o.data.update()
    if lod>0:coll.hide_render=True;coll.hide_viewport=True
    print('TREE_LOD_EXPORTED',lod,info['total_triangles'],flush=True)

manifest['source_hashes_after']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
assert before==manifest['source_hashes_after'],'Source project changed during generation'
manifest['unity_project_unchanged']=True
sample=min((s for s in sprays if 3<float(s[0].y)<5),key=lambda s:s[0].z)
manifest['needle_detail_target']=[float(v) for v in Vector(sample[0])+Vector(sample[1])*.16]
manifest['export_convention']='Unity design (x,y,z) -> Blender (x,z,y); export geometry Z180 baked; -Z forward Y up FBX. Expected Unity P0 R0 S1.'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for sc in bpy.data.screens:
    for a in sc.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=15;a.spaces.active.region_3d.view_location=P@Vector((0,5.5,0))
scene.cursor.location=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_FOREST_Spruce_A.blend'))
print('FOREST_HERO_BUILD_OK',len(sprays),flush=True)
