"""Render every creature's vanilla bind pose, as an image to generate from.

Skyrim's animation clips are authored against the vanilla mesh's bind pose, so
a replacement mesh has to be delivered in exactly that pose.  An AI generator
produces whatever stance the prompt asks for - which is why the bear comes out
standing on all fours while Skyrim's bear rears up on its hind legs.

These renders are the reference: feed them to the image generator and ask for
the same pose, then the model needs no pose fixing at all.

    py src/scripts/05_render_pose_reference.py                # everything
    py src/scripts/05_render_pose_reference.py bear wolf       # only these
    py src/scripts/05_render_pose_reference.py --front         # front view too

Output: reference/<Mod>/<creature>/pose_side.png (and pose_front.png)
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "blender_addon"))

MOD_FOLDERS = {"Creatures": "HighPolyCreatures", "Enemies": "HighPolyEnemies"}
NON_BODY = ("skeleton", "face", "hair", "eye", "weapon", "shield", "arrow", "quiver")


def creatures():
    """(mod, name, prefixes) rows from config/creatures.csv."""
    import csv

    with (ROOT / "config" / "creatures.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            prefixes = row.get("prefixes", "").strip()
            yield (row["mod"], row["creature"],
                   [p for p in prefixes.split(";") if p])


def main_nif(mod: str, name: str) -> Path | None:
    """The main body NIF of a creature, from the reference tree."""
    folder = ROOT / "reference" / MOD_FOLDERS[mod] / name / "meshes"
    if not folder.is_dir():
        return None
    best = None
    for path in sorted(folder.rglob("*.nif")):
        if any(p in path.name.lower() for p in NON_BODY):
            continue
        if path.stem.lower() == name.lower():
            return path
        size = path.stat().st_size
        if best is None or size > best.stat().st_size:
            best = path
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="creatures to render (default: all)")
    ap.add_argument("--front", action="store_true", help="also render a front view")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=640)
    # Blender puts its own flags in sys.argv before the script path; only the
    # arguments after the script (or after "--") belong to us.
    argv = sys.argv
    if "--" in argv:
        extra = argv[argv.index("--") + 1:]
    else:
        script = str(Path(__file__).resolve())
        idx = argv.index(script) if script in argv else -1
        extra = argv[idx + 1:] if idx >= 0 else []
    args = ap.parse_args(extra)

    import addon_utils

    import bpy

    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("io_scene_nifly", default_set=True)

    wanted = {n.lower() for n in args.names}
    done = 0
    skipped = 0
    for mod, name, _prefixes in creatures():
        if wanted and name.lower() not in wanted:
            continue
        nif = main_nif(mod, name)
        if nif is None:
            print(f"  {name}: no reference NIF")
            skipped += 1
            continue
        out_dir = ROOT / "reference" / MOD_FOLDERS[mod] / name
        out_dir.mkdir(parents=True, exist_ok=True)

        bpy.ops.wm.read_factory_settings(use_empty=True)
        addon_utils.enable("io_scene_nifly", default_set=True)
        bpy.ops.import_scene.pynifly(filepath=str(nif))
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        if not meshes:
            print(f"  {name}: no mesh in {nif.name}")
            skipped += 1
            continue

        mins = [1e9] * 3
        maxs = [-1e9] * 3
        for ob in meshes:
            for v in ob.data.vertices:
                w = ob.matrix_world @ v.co
                for i in range(3):
                    mins[i] = min(mins[i], w[i])
                    maxs[i] = max(maxs[i], w[i])
        centre = [(mins[i] + maxs[i]) / 2 for i in range(3)]
        extent = [maxs[i] - mins[i] for i in range(3)]

        cam_data = bpy.data.cameras.new("cam")
        cam = bpy.data.objects.new("cam", cam_data)
        bpy.context.scene.collection.objects.link(cam)
        cam_data.lens = 55
        cam_data.sensor_width = 36
        bpy.context.scene.camera = cam

        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", type="SUN"))
        sun.rotation_euler = (math.radians(55), 0, math.radians(125))
        sun.data.energy = 4.5
        bpy.context.scene.collection.objects.link(sun)
        fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", type="SUN"))
        fill.rotation_euler = (math.radians(70), 0, math.radians(-60))
        fill.data.energy = 2.0
        bpy.context.scene.collection.objects.link(fill)
        world = bpy.data.worlds.new("w")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.65, 0.70, 1.0)
        world.node_tree.nodes["Background"].inputs[1].default_value = 1.4
        bpy.context.scene.world = world

        for ob in bpy.data.objects:
            ob.hide_render = ob.type != "MESH"

        # The camera has to frame the body exactly, so the distance is solved
        # from the field of view: a fixed multiple of the longest axis crops
        # everything that is tall (the rearing bear) or long (the mammoth).
        scene = bpy.context.scene
        scene.render.resolution_x = args.width
        scene.render.resolution_y = args.height
        scene.render.image_settings.file_format = "PNG"

        aspect = args.width / args.height
        sensor = cam_data.sensor_width
        half_fov_x = math.atan((sensor / 2) / cam_data.lens)
        # a landscape frame is shorter than it is wide
        half_fov_y = math.atan((sensor / 2 * (1 / aspect)) / cam_data.lens)

        def distance_for(width: float, height: float) -> float:
            """How far back the camera has to be to fit width x height."""
            need_x = (width / 2) / math.tan(half_fov_x)
            need_y = (height / 2) / math.tan(half_fov_y)
            return max(need_x, need_y) * 1.08

        # side view: the camera looks along +X, so the image is the Y/Z plane
        views = {
            "side": ((extent[1], extent[2]), (1, 0, 0), (90.0, 0.0, 90.0)),
            "front": ((extent[0], extent[2]), (0, -1, 0), (90.0, 0.0, 0.0)),
        }
        if not args.front:
            views.pop("front")

        for view, ((span_x, span_y), axis, rot) in views.items():
            dist = distance_for(span_x, span_y)
            cam.location = (centre[0] + axis[0] * dist, centre[1] + axis[1] * dist,
                            centre[2])
            cam.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]),
                                  math.radians(rot[2]))
            scene.render.filepath = str(out_dir / f"pose_{view}.png")
            bpy.ops.render.render(write_still=True)
        size = (extent[0], extent[1], extent[2])
        print(f"  {name}: pose_side.png  size {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f}")
        done += 1

    print(f"done: {done} rendered, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
