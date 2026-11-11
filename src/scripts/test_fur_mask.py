"""Fur mask: create it, paint nothing yet, rebuild, and verify it is applied."""

import os
from pathlib import Path

import numpy as np

import addon_utils

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)
addon_utils.enable("highpoly_pipeline", default_set=True)

import highpoly_pipeline as hp  # noqa: E402

ROOT = Path(r"C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures")
c = hp.find_creature(ROOT, "Creatures", "wolf")
s = bpy.context.scene.hp
s.mod, s.creature = "Creatures", "wolf"

# This test paints the mask and rebuilds the shell, and both live in the
# production texture folder - so keep a copy and put the originals back.
tex_dir = hp.incoming_dir(ROOT, c) / "textures" / "actors" / "wolf"
backup = {p.name: p.read_bytes() for p in tex_dir.glob("*.png")}

# 1. the mask is created from the diffuse's coverage
mask = hp.ensure_fur_mask(ROOT, c)
print("=== mask created:", mask.name, tuple(mask.size),
      "at", hp.fur_mask_png(ROOT, c).name)

px = np.array(mask.pixels[:], dtype=np.float32).reshape(-1, 4)
alpha = px[:, 0]
print(f"    coverage: mean {alpha.mean():.3f}  "
      f"zeros {(alpha <= 0.02).mean():.3f}  ones {(alpha >= 0.98).mean():.3f}")

# 2. opening it for painting must not crash in background mode
print("=== open:", hp._open_image_in_editor(bpy.context, mask)[:80])

# 3. paint a black stripe across the mask, rebuild, check it took effect
w, h = mask.size
buf = np.array(mask.pixels[:], dtype=np.float32).reshape(h, w, 4)
buf[:, : w // 8, :3] = 0.0            # bare: no fur on the first eighth
buf[:, w // 4: w // 2, :3] = 1.0      # a very furry stripe
mask.pixels = buf.ravel().tolist()

# what will the rebuild actually see? (Blender's name for a loaded file may
# or may not carry the extension)
hits = [im.name for im in bpy.data.images
        if im.filepath.endswith("wolf_furmask.png") or im.name.startswith("wolf_furmask")]
print("=== datablock lookup:", hits)
for im in bpy.data.images:
    if im.name in hits:
        fp = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)
        print(f"    {im.name}: mean {fp[:, 0].mean():.3f} "
              f"zeros {(fp[:, 0] <= 0.02).mean():.3f} nan {int(np.isnan(fp).sum())}")

note = hp.do_rebuild_fur(ROOT, c)
print("=== rebuild:", note)

shell_png = hp.incoming_dir(ROOT, c) / "textures" / "actors" / "wolf" / "wolf_shell.png"
sh = bpy.data.images.load(str(shell_png))
print("    shell image size:", tuple(sh.size))
sp = np.array(sh.pixels[:], dtype=np.float32).reshape(-1, 4)[:, 3].reshape(tuple(sh.size)[::-1])
print(f"    shell alpha nan: {int(np.isnan(sp).sum())}  "
      f"mean {np.nanmean(sp):.3f}")
print(f"    shell alpha where mask = 0 : {np.nanmean(sp[:, : w // 8]):.3f} (expect ~0)")
print(f"    shell alpha where mask = 1 : {np.nanmean(sp[:, w // 4:w // 2]):.3f} (expect 0.3-1.0)")
ok = (np.nanmax(sp[:, : w // 8]) < 0.05 and 0.2 < np.nanmean(sp[:, w // 4:w // 2]))
print("=== RESULT:", "MASK TEST OK" if ok else "MASK TEST FAILED")

# put the production textures back - the painted mask and the striped shell
# must not survive the test
for name, data in backup.items():
    (tex_dir / name).write_bytes(data)
print(f"    restored {len(backup)} production texture(s)")
