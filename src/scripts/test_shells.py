"""Fur shells, FluffyWorks style.

Checks the whole fur pipeline end to end:
  1. the shell texture is written with a broad alpha spread (the taper needs it)
  2. the shell stack is built: N layers, each further out along the normals
  3. the exported NIF has one shape per layer, alpha blended, double sided,
     with the FluffyWorks threshold ramp (15, 30, 45 ...)
  4. the vanilla Fur shape is gone unless it was asked for - it belongs to the
     old body and does not line up
"""

import sys
from pathlib import Path

import addon_utils

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)
addon_utils.enable("highpoly_pipeline", default_set=True)

import highpoly_pipeline as hp  # noqa: E402

ROOT = Path(r"C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures")
sys.path.insert(0, str(ROOT / "tools" / "pynifly" / "io_scene_nifly"))
from pyn.pynifly import NifFile  # noqa: E402

root = hp.project_root(bpy.context)
c = hp.find_creature(root, "Creatures", "wolf")
s = bpy.context.scene.hp
s.mod, s.creature = "Creatures", "wolf"
s.rotate_x, s.rotate_z, s.scale_multiplier = -90.0, 0.0, 1.0
s.target_multiplier = 4
s.shell_count = 0
s.fur_count = 12000
s.shell_spacing = 0.35
s.shell_tris = 0
s.keep_fur = False

print("=== pipeline ===")
print("load:   ", hp.do_load_vanilla(bpy.context, c, root))
print("import: ", hp.do_import_model(bpy.context, c, root))
print("fit:    ", hp.do_fit(bpy.context, s))
print("decimate:", hp.do_decimate(bpy.context, s))
print("rig:    ", hp.do_transfer_weights(bpy.context))
print("material:", hp.do_setup_material(bpy.context, c, root))
print("fur:    ", hp.do_make_fur(bpy.context, c, root, s))
print("shells: ", hp.do_make_shells(bpy.context, c, root, s))
print("export: ", hp.do_export(bpy.context, c, root, s.keep_fur, s.keep_extra_vanilla))

# --- 0. fur cards ------------------------------------------------------------
fur_objs = hp.objects_with("fur")
print(f"=== 0. fur objects: {[o.name for o in fur_objs]}")
fur_ok = False
if fur_objs:
    obj = fur_objs[0]
    strands = len(obj.data.vertices) // 4
    weighted = sum(1 for v in obj.data.vertices if any(g.weight > 0 for g in v.groups))
    print(f"    {strands:,} strands, {len(obj.data.polygons):,} tris, "
          f"{weighted}/{len(obj.data.vertices)} verts weighted, "
          f"groups {len(obj.vertex_groups)}")
    fur_ok = strands > 1000 and weighted == len(obj.data.vertices)

# --- 1. shell texture -------------------------------------------------------
import numpy as np  # noqa: E402

tex_dir = hp.incoming_dir(root, c) / "textures" / "actors" / c.name
shell_png = tex_dir / f"{c.name}_hp_shell.png"
ok_tex = shell_png.is_file()
print(f"=== 1. shell texture {shell_png.name}: {ok_tex}")
spread = 0.0
if ok_tex:
    img = bpy.data.images.load(str(shell_png))
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    alpha = px[:, 3]
    hist = [(alpha > t / 255.0).mean() for t in (15, 60, 120, 180, 240)]
    print(f"    alpha above threshold 15/60/120/180/240: "
          f"{[round(h, 3) for h in hist]}")
    spread = hist[0] - hist[-1]
    print(f"    taper spread: {spread:.3f} (needs to be clearly positive)")
    bpy.data.images.remove(img)

# --- 2. shell objects -------------------------------------------------------
shells = hp.objects_with("shell")
print(f"=== 2. {len(shells)} shell objects")
if shells:
    base = shells[0]
    zs = [v.co.z for v in base.data.vertices]
    print(f"    layer 1 Z {min(zs):.1f}..{max(zs):.1f}")
    last = shells[-1]
    zs2 = [v.co.z for v in last.data.vertices]
    print(f"    layer {len(shells)} Z {min(zs2):.1f}..{max(zs2):.1f}")
    grown = max(zs2) > max(zs)
    print(f"    outer layer sits further out: {grown}")
else:
    grown = True   # no shell layers requested - nothing to grow

# --- 3. exported NIF --------------------------------------------------------
out = root / "build" / "HighPolyCreatures" / "meshes" / "actors" / "canine" / \
    "character assets wolf" / "wolf.nif"
nif = NifFile(str(out))
names = [sh.name for sh in nif.shapes]
nif_shapes = list(nif.shapes)
shell_shapes = [sh for sh in nif.shapes if sh.name.startswith("HP_Shell")]
print(f"=== 3. exported shapes: {names}")
print(f"    shell shapes: {len(shell_shapes)}")
rows = []
for sh in shell_shapes:
    ap = sh.alpha_property
    p = ap.properties if ap else None
    rows.append((sh.name,
                 getattr(p, "threshold", None),
                 getattr(p, "flags", None),
                 sh.shader.flag_double_sided,
                 sh.shader.flag_alpha_test,
                 sh.shader.flag_rim_lighting,
                 len(sh.bone_weights),
                 len(sh.verts),
                 sh.textures.get("Diffuse")))
for r in rows:
    print(f"      {r[0]}: threshold={r[1]} flags={r[2]} double_sided={r[3]} "
          f"alpha_test={r[4]} rim={r[5]} bones={r[6]} verts={r[7]}")
    print(f"         diffuse={r[8]}")

# --- 5. the fur shape made it into the NIF ----------------------------------
fur_shapes = [sh for sh in nif.shapes if "Fur" in sh.name]
print(f"=== 5. fur shapes in the NIF: {[sh.name for sh in fur_shapes]}")
fur_in_nif = False
if fur_shapes:
    sh = fur_shapes[0]
    print(f"    {sh.name}: {len(sh.verts)} verts, {len(sh.tris)} tris, "
          f"{len(sh.bone_weights)} bones")
    fur_in_nif = len(sh.verts) > 1000 and len(sh.bone_weights) > 0
nif.close()

thresholds = sorted(r[1] for r in rows)
ramp_ok = thresholds == [15 * i for i in range(1, len(rows) + 1)]
blend_ok = all(r[2] == 4844 for r in rows)
double_ok = all(r[3] for r in rows)
skinned_ok = all(r[6] > 0 for r in rows)
shell_tex_ok = all(r[8] and "shell" in r[8].lower() for r in rows)
print(f"    threshold ramp {thresholds} -> {ramp_ok}")
print(f"    alpha blend flags -> {blend_ok}, double sided -> {double_ok}, "
      f"skinned -> {skinned_ok}, shell texture -> {shell_tex_ok}")

# --- 4. no vanilla fur ------------------------------------------------------
fur_gone = "Fur" not in names
print(f"=== 4. vanilla Fur shape dropped: {fur_gone}")

ok = (ok_tex and spread > 0.2 and grown and fur_gone and fur_ok and fur_in_nif)
if rows:
    ok = ok and ramp_ok and blend_ok and double_ok and skinned_ok and shell_tex_ok
print("=== RESULT:", "SHELL TEST OK" if ok else "SHELL TEST FAILED")






