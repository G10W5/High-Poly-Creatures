"""Build every creature that has a model in incoming/.

Runs the whole pipeline for each one and reports the numbers that matter:
how well the model lined up with the vanilla body (the pose fit), the tri
count, the fur and the size of the NIF.

    blender --background --python src/scripts/07_build_all.py
"""

import os
import sys
import traceback
from pathlib import Path

import addon_utils

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_nifly", default_set=True)
addon_utils.enable("highpoly_pipeline", default_set=True)

import highpoly_pipeline as hp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "pynifly" / "io_scene_nifly"))
from pyn.pynifly import NifFile  # noqa: E402


def has_model(creature) -> bool:
    incoming = hp.incoming_dir(ROOT, creature)
    if not incoming.is_dir():
        return False
    for ext in (".glb", ".fbx", ".obj", ".blend"):
        if any(incoming.glob(f"*{ext}")):
            return True
    return False


def main() -> int:
    only = [a.lower() for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []
    settings = bpy.context.scene.hp
    settings.target_multiplier = 2.5
    settings.shell_tris = 0
    settings.shell_spacing = 0.4
    settings.shell_gap = 0.3
    settings.fur_count = 0

    creatures = [c for c in hp.load_creatures(ROOT) if c.mod == "Creatures"]
    if only:
        creatures = [c for c in creatures if c.name.lower() in only]
    todo = [c for c in creatures if has_model(c)]
    print(f"=== {len(todo)} creatures with a model: {[c.name for c in todo]}")

    for c in todo:
        print(f"\n=== {c.name} ({c.category}, fur={c.fur})")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        addon_utils.enable("io_scene_nifly", default_set=True)
        addon_utils.enable("highpoly_pipeline", default_set=True)
        settings = bpy.context.scene.hp
        settings.mod, settings.creature = c.mod, c.name
        settings.target_multiplier = 2.5
        settings.shell_tris = 0
        settings.shell_spacing = 0.4
        settings.shell_gap = 0.3
        settings.fur_count = 0
        settings.auto_orient = True
        try:
            hp.do_load_vanilla(bpy.context, c, ROOT)
            hp.do_import_model(bpy.context, c, ROOT)
            fit = hp.do_fit(bpy.context, settings)
            print("    fit:", fit)
            hp.do_decimate(bpy.context, settings)
            hp.do_smooth_shading(bpy.context, settings)
            hp.do_transfer_weights(bpy.context)
            hp.do_setup_material(bpy.context, c, ROOT)
            print("    shells:", hp.do_make_shells(bpy.context, c, ROOT, settings))
            hp.do_export(bpy.context, c, ROOT, False, False)

            nif = (ROOT / "build" / "HighPolyCreatures" / "meshes")
            for path in nif.rglob(f"{c.name}.nif"):
                pass
            out = ROOT / "build" / "HighPolyCreatures"
            found = [p for p in out.rglob("*.nif") if p.stem.lower() == c.name.lower()]
            if found:
                n = NifFile(str(found[0]))
                tris = sum(len(s.tris) for s in n.shapes)
                shapes = [f"{s.name}:{len(s.tris)}" for s in n.shapes]
                n.close()
                size = found[0].stat().st_size / 1048576
                print(f"    NIF {found[0].name}: {size:.2f} MB, {tris:,} tris")
                print(f"    shapes: {shapes}")
        except Exception:
            print("    FAILED:")
            traceback.print_exc()
    return 0


if __name__ == "__main__":
    sys.exit(main())

