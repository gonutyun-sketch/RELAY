"""Save inspectable Blender art sources; no Unity access."""
import bpy,json,hashlib
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
bpy.context.preferences.filepaths.save_version=0
cam=bpy.data.objects['EXIT_01_From_Forest'];cam.location=(.4,8.2,1.9)
cam.rotation_euler=(Vector((0,-1.3,3.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28
bpy.context.scene.camera=cam
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_ForestExit_Review.blend'),compress=True)
# A separate editable source contains the delivered model parts, not old forest
# and elevator instances. The full review file retains their visual context.
keep={'01_Terrain_and_Path','03_Ferns_and_Forest_Litter','10_EXIT_Hillside','11_EXIT_Headwall','12_EXIT_Landing','13_EXIT_SealTrim_VISUAL_ONLY','14_MOVING_ELEVATOR_LandingApron','15_EXIT_BackTrees','90_Preview_Lighting_Fog_Cameras'}
for c in list(bpy.data.collections):
    if c.name not in keep:
        for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(c)
for o in list(bpy.data.objects):
    if not o.users_collection:bpy.data.objects.remove(o,do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RELAY_ForestExit.blend'),compress=True)
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.suffix.lower() in ('.fbx','.blend','.png'):
        files.append({'file':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'checks/delivery_files.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
print('EXIT_PACKAGE_FINALIZED',flush=True)
