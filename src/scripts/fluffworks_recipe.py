"""Reverse-engineer FluffyWorks' shell stack.

Prints, for every shell shape:
  * NiAlphaProperty threshold (the per-layer taper)
  * bounding box (how far the shell sits from the body)
  * how many vertices each shell has

Usage:  py src/scripts/fluffworks_recipe.py <fluffworks wolf.nif>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pynifly" / "io_scene_nifly"))

from pyn.pynifly import NifFile  # noqa: E402


def main(path: str) -> None:
    n = NifFile(path)
    shapes = {s.name: s for s in n.shapes}
    body = shapes.get("WolfREDUCED")
    if body:
        bx = [v[0] for v in body.verts]
        by = [v[1] for v in body.verts]
        bz = [v[2] for v in body.verts]
        print(f"body   WolfREDUCED   verts {len(body.verts):>5} tris {len(body.tris):>5}  "
              f"bbox X {min(bx):7.1f}..{max(bx):7.1f}  Y {min(by):7.1f}..{max(by):7.1f}  "
              f"Z {min(bz):7.1f}..{max(bz):7.1f}")
    print()
    for name in sorted(shapes, key=lambda k: (not k.startswith("WolfShell"), k)):
        s = shapes[name]
        if not name.startswith("WolfShell"):
            continue
        xs = [v[0] for v in s.verts]
        ys = [v[1] for v in s.verts]
        zs = [v[2] for v in s.verts]
        # mean radius from the body axis, to see how far the shell floats
        radii = sorted(((x * x + y * y) ** 0.5) for x, y in zip(xs, ys))
        med = radii[len(radii) // 2] if radii else 0.0
        print(f"  {name:<16} verts {len(s.verts):>5} tris {len(s.tris):>5}  "
              f"X {min(xs):7.1f}..{max(xs):7.1f}  Y {min(ys):7.1f}..{max(ys):7.1f}  "
              f"Z {min(zs):7.1f}..{max(zs):7.1f}  medRadius {med:6.1f}")
    n.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         r"C:\Users\Uporabnik\AppData\Roaming\Vortex\skyrimse\mods\Fluffworks Quality-56361"
         r"-1-1f-1646241621\meshes\actors\canine\character assets wolf\wolf.nif")
