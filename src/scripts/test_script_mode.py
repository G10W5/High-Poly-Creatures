"""Regression test for running highpoly_pipeline.py the way the user does:
opening it in the Text Editor and pressing Run Script (so __name__ == "__main__").

That used to die with
    KeyError: 'bpy_prop_collection[key]: key "__main__" not found'
because AddonPreferences is keyed by the add-on module name.
"""

import addon_utils
import runpy
import sys
from pathlib import Path

import bpy

ADDON = Path(r"C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\src\blender_addon\highpoly_pipeline.py")

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)

# --- run the file exactly like the Text Editor "Run Script" button does -------
runpy.run_path(str(ADDON), run_name="__main__")

print("=== MODE: script run (__main__) ===")
print("hp ops:", sorted(o for o in dir(bpy.ops.hp) if not o.startswith("_"))[:4])
print("panel registered:", hasattr(bpy.types, "HP_PT_panel"))
print("preferences registered (should be False):", hasattr(bpy.types, "HPPreferences"))
print("scene.hp exists:", hasattr(bpy.context.scene, "hp"))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("hp_probe", ADDON)
hp = importlib.util.module_from_spec(spec)
sys.modules["hp_probe"] = hp
spec.loader.exec_module(hp)

root = hp.project_root(bpy.context)
print("project root:", root)
print("config found:", (root / "config" / "creatures.csv").is_file())
print("creatures for Creatures:",
      [c.name for c in hp.load_creatures(root) if c.mod == "Creatures"][:5], "...")

s = bpy.context.scene.hp
s.mod, s.creature = "Creatures", "wolf"
print("enum items:", [i[0] for i in hp.creature_items(s, bpy.context)][:5])

ret = bpy.ops.hp.load_vanilla()
print("load_vanilla:", ret, "| status:", s.status)

body = hp.objects_with("vanilla_body")
print("vanilla body loaded:", [o.name for o in body], hp.mesh_stats(body[0]) if body else "")

print("=== SCRIPT MODE OK ===" if body else "=== SCRIPT MODE FAILED ===")
