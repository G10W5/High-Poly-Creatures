"""Colour variants: the tinted textures and the repointed NIFs.

    py src/scripts/test_variants.py

Needs the wolf built (07_build_all.py) and its textures converted
(03_build_textures.py) to have run at least once.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "pynifly" / "io_scene_nifly"))

from pyn.pynifly import NifFile  # noqa: E402

from variants import load_variants, retarget_nif, tint_textures  # noqa: E402

WOLF_TEX = (ROOT / "raw_assets" / "HighPolyCreatures" / "wolf" / "incoming"
            / "textures" / "actors" / "wolf")
WOLF_MESH = (ROOT / "build" / "HighPolyCreatures" / "meshes" / "actors" / "canine"
             / "character assets wolf")

failures = []


def check(ok: bool, what: str):
    print(f"    {'ok  ' if ok else 'FAIL'}  {what}")
    if not ok:
        failures.append(what)


def mean_rgb(path: Path):
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB"), dtype=np.float32)
    return a.mean(axis=(0, 1))


def main() -> int:
    rows = load_variants()
    print(f"=== 1. config: {len(rows)} variant rows")
    check(len(rows) >= 4, "config/variants.csv has rows")
    check(("wolf", "wolfblack") in rows, "the wolf's colour variants are listed")

    if not (WOLF_MESH / "wolf.nif").is_file():
        print("    the wolf is not built - run 07_build_all.py first")
        return 1

    print("=== 2. the tinted textures")
    base = mean_rgb(WOLF_TEX / "wolf_d.png")
    black = mean_rgb(WOLF_TEX / "wolfblack_d.png")
    red = mean_rgb(WOLF_TEX / "wolfred_d.png")
    fire = mean_rgb(WOLF_TEX / "wolffire_d.png")
    print(f"    wolf     {base.round(1)}")
    print(f"    wolfblack{black.round(1)}")
    print(f"    wolfred  {red.round(1)}")
    print(f"    wolffire {fire.round(1)}")
    check(black.mean() < base.mean(), "the black coat is darker than the base")
    check(red[0] > red[2], "the red coat is redder than it is blue")
    check(fire[0] > fire[2], "the fire coat is orange")

    print("=== 3. the fur shell keeps its strand mask")
    with Image.open(WOLF_TEX / "wolf_shell.png") as im:
        base_alpha = np.asarray(im.convert("RGBA"))[..., 3]
    for name in ("wolfblack", "wolfred", "wolffire"):
        path = WOLF_TEX / f"{name}_shell.png"
        if not path.is_file():
            check(False, f"{name}_shell.png exists")
            continue
        with Image.open(path) as im:
            alpha = np.asarray(im.convert("RGBA"))[..., 3]
        check(np.array_equal(alpha, base_alpha),
              f"{name}_shell.png has the same strand mask as the base shell")

    print("=== 4. the variant NIFs point at their own textures")
    for name in ("wolfblack", "wolfred", "wolffire"):
        path = WOLF_MESH / f"{name}.nif"
        if not path.is_file():
            check(False, f"{name}.nif was built")
            continue
        nif = NifFile(str(path))
        shapes = list(nif.shapes)
        pointing = [s for s in shapes
                    if name in (s.shader.textures.get("Diffuse") or "")]
        check(len(shapes) == 17, f"{name}.nif has all 17 shapes")
        check(len(pointing) == len(shapes), f"{name}.nif points every shape at {name}_*.dds")
        normals = {s.shader.textures.get("Normal") for s in shapes}
        check(normals == {"textures\\actors\\wolf\\wolf_n.dds"},
              f"{name}.nif shares the normal map with the base wolf")
        nif.close()

    print("=== 5. the repointing is idempotent")
    before = (WOLF_MESH / "wolfred.nif").read_bytes()
    retarget_nif(WOLF_MESH / "wolfred.nif", "wolf", "wolfred")
    after = (WOLF_MESH / "wolfred.nif").read_bytes()
    check(before == after, "running it twice changes nothing")

    print("=== RESULT:", "VARIANT TEST OK" if not failures else f"{len(failures)} FAILURES")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
