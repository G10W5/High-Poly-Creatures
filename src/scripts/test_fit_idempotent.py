"""Auto Fit must be repeatable, reversible, and live.

Historically every press baked a new transform onto the vertices, so changing
Rotate X after a fit could never do anything - the -90 was already in the mesh.
Checks:
  1. import now auto-fits (right size/orientation immediately)
  2. fitting twice gives identical results (idempotent), and how long it takes
  3. changing Rotate Z moves the model WITHOUT pressing anything (live update)
  4. rotate_x 0 -> -90 returns to the original vertex positions (reversible)
  5. re-fitting keeps decimation and skin weights

Note: with "Match vanilla silhouette" the fitted bbox always equals vanilla's,
so orientation is checked through vertex positions, not dimensions.
"""

import time

import addon_utils

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)
addon_utils.enable("highpoly_pipeline", default_set=True)

import highpoly_pipeline as hp  # noqa: E402

root = hp.project_root(bpy.context)
c = hp.find_creature(root, "Creatures", "wolf")
s = bpy.context.scene.hp
s.mod, s.creature = "Creatures", "wolf"
s.rotate_x, s.rotate_z, s.scale_multiplier = -90.0, 0.0, 1.0
s.fit_mode = "AXIS"
s.target_multiplier = 6

hp.do_load_vanilla(bpy.context, c, root)
hp.do_import_model(bpy.context, c, root)          # now auto-fits on import

model = hp.objects_with("model")[0]


def fp(obj, n=32):
    """Positions spread across the mesh - vertex 0 sits at the model's origin
    and survives rotate+scale+centre unchanged, so it is useless as a probe."""
    vs = obj.data.vertices
    step = max(1, len(vs) // n)
    out = []
    for i in range(0, len(vs), step):
        co = vs[i].co
        out.extend((co.x, co.y, co.z))
    return out


def diff(a, b):
    return max((abs(x - y) for x, y in zip(a, b)), default=0.0)


co1 = fp(model)
print("=== 1. auto-fitted on import, dims:", tuple(round(v, 3) for v in model.dimensions),
      "| fit record:", tuple(model.get("hp_fit_rot")))

# --- idempotent + timing ----------------------------------------------------
t0 = time.perf_counter()
hp.do_fit(bpy.context, s)
ms = (time.perf_counter() - t0) * 1000
drift = diff(co1, fp(model))
print(f"=== 2. re-fit {ms:.0f} ms | drift {drift:.9f} | idempotent: {drift < 1e-4}")

# --- live update ------------------------------------------------------------
s.rotate_z = 30.0                                   # no do_fit call on purpose
live = diff(co1, fp(model))
print("=== 3. rotate_z=30 moved the mesh by itself: drift", round(live, 4),
      "| recorded:", tuple(model.get("hp_fit_rot")))
s.rotate_z = 0.0

# --- reversible -------------------------------------------------------------
s.rotate_x = 0.0
away = diff(co1, fp(model))
s.rotate_x = -90.0
drift2 = diff(co1, fp(model))
print(f"=== 4. rotate_x 0 moved mesh: {away > 1e-4} (drift {away:.3f}) | "
      f"back to -90 drift {drift2:.9f}")

# --- keeps decimation and weights ------------------------------------------
print("=== 5.", hp.do_decimate(bpy.context, s))
print("=== 6.", hp.do_transfer_weights(bpy.context))
tris_before = hp.tri_count(model)
weighted_before = sum(1 for v in model.data.vertices if any(g.weight > 0 for g in v.groups))

hp.do_fit(bpy.context, s)                          # re-fit AFTER decimate + weights
tris_after = hp.tri_count(model)
weighted_after = sum(1 for v in model.data.vertices if any(g.weight > 0 for g in v.groups))
print(f"=== 7. after re-fit: tris {tris_before} -> {tris_after}, "
      f"weighted {weighted_before} -> {weighted_after}")

ok = (drift < 1e-4 and live > 1e-4 and away > 1e-4 and drift2 < 1e-4
      and tris_after == tris_before and weighted_after == weighted_before)
print("=== RESULT:", "FIT TEST OK" if ok else "FIT TEST FAILED")
