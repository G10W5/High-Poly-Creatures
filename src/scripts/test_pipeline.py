import bpy
import addon_utils
import traceback

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)
addon_utils.enable("highpoly_pipeline", default_set=True)

print("=== OPS ===", hasattr(bpy.ops, "hp"))

s = bpy.context.scene.hp
s.mod = "Creatures"
s.creature = "wolf"
s.target_multiplier = 4
s.rotate_x = -90.0
s.scale_multiplier = 1.0
s.keep_fur = False

try:
    ret = bpy.ops.hp.run_all()
    print("=== RET ===", ret)
except Exception:
    traceback.print_exc()

print("=== STATUS ===")
print(s.status)

