"""Regression test: PyNifly switched off (what the user's GUI had).

Two paths:
1. auto-fix   - the step switches PyNifly on itself, then succeeds
2. unfixable  - PyNifly really is missing (e.g. the folder was never installed);
                the operator must return CANCELLED with a clean message, never a
                Python traceback.
"""

import addon_utils

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
# deliberately NOT enabling io_scene_nifly, so the NIF operators are missing
addon_utils.enable("highpoly_pipeline", default_set=True)

import highpoly_pipeline as hp  # noqa: E402

s = bpy.context.scene.hp
s.mod, s.creature = "Creatures", "wolf"

print("=== ready before:", hp.pynifly_ready())

# --- 1. auto-fix ------------------------------------------------------------
ret = bpy.ops.hp.load_vanilla()
print("=== auto-fix load:", ret, "| status:", s.status, "| ready:", hp.pynifly_ready())
auto_ok = ret == {"FINISHED"} and hp.pynifly_ready() and hp.objects_with("vanilla_body")

# --- 2. unfixable -----------------------------------------------------------
orig_ensure = hp.ensure_pynifly
hp.ensure_pynifly = lambda: False          # simulate a missing PyNifly install
s.status = "Ready"
raised = ""
try:
    # Called from Python, Blender re-raises an operator's ERROR report as
    # RuntimeError; from the UI the user just sees a red toast.
    ret2 = bpy.ops.hp.load_vanilla()
except RuntimeError as exc:
    ret2 = {"CANCELLED"}
    raised = str(exc)
print("=== unfixable load:", ret2, "| status:", s.status, "| reported:", raised[:60])
guard_ok = ret2 == {"CANCELLED"} and s.status.startswith("FAILED: ") \
    and "PyNifly is not available" in s.status \
    and "PyNifly is not available" in raised
hp.ensure_pynifly = orig_ensure

print("=== auto-fix path:", "OK" if auto_ok else "FAILED")
print("=== guard path:", "OK" if guard_ok else "FAILED")
print("=== RESULT:", "GUARD TEST OK" if (auto_ok and guard_ok) else "GUARD TEST FAILED")
