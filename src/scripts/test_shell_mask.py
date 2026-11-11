"""The strand mask: does it still comb the way FluffyWorks' does?

Comparing against FluffyWorks' own mask is the only honest yardstick we have
for "does this look like fur".  FluffyWorks' wolf_shell.dds measures:

    anisotropy 5.28   (how one-directional the strands are; 1 = isotropic)
    crossings  929    (strand edges along one scanline)

An earlier version of the generator scored anisotropy 1.78 - the strands
swirled instead of combing - because the flow field followed every bump in
the AI diffuse.  These numbers keep that fixed.

    py src/scripts/test_shell_mask.py
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

# the numbers FluffyWorks' own mask measures, on the same wolf
FLUFFWORKS_ANISOTROPY = 5.28
FLUFFWORKS_CROSSINGS = 929

failures = []


def check(ok: bool, what: str):
    print(f"    {'ok  ' if ok else 'FAIL'}  {what}")
    if not ok:
        failures.append(what)


def anisotropy(alpha: np.ndarray, k: int = 9) -> float:
    """How one-directional the strands are: 1 = isotropic, high = combed."""
    gy, gx = np.gradient(alpha.astype(np.float32))

    def blur(a):
        pad = np.pad(a, k // 2, mode="edge")
        c = np.cumsum(pad, axis=0)
        out = c[2 * k // 2:] - c[:-(2 * k // 2)]
        c = np.cumsum(out, axis=1)
        return c[:, 2 * k // 2:] - c[:, :-(2 * k // 2)]

    gx, gy = blur(gx) / (k * k), blur(gy) / (k * k)
    jxx, jyy, jxy = (gx * gx).mean(), (gy * gy).mean(), (gx * gy).mean()
    tmp = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    l1 = (jxx + jyy + tmp) / 2
    l2 = (jxx + jyy - tmp) / 2
    return float(l1 / l2) if l2 > 1e-12 else float("inf")


def crossings(alpha: np.ndarray) -> int:
    """How many strand edges cross one scanline."""
    row = alpha[alpha.shape[0] // 2]
    return int(np.count_nonzero(np.diff(np.sign(np.diff(row))) != 0))


def main() -> int:
    path = (ROOT / "raw_assets" / "HighPolyCreatures" / "wolf" / "incoming" /
            "textures" / "actors" / "wolf" / "wolf_shell.png")
    if not path.is_file():
        print("    the wolf shell texture is not built - run 07_build_all.py first")
        return 1

    with Image.open(path) as im:
        alpha = np.asarray(im.convert("RGBA"), dtype=np.float32)[..., 3] / 255.0

    an = anisotropy(alpha)
    cr = crossings(alpha)
    print(f"=== strand mask: anisotropy {an:.2f}  crossings {cr}")
    print(f"    FluffyWorks:  anisotropy {FLUFFWORKS_ANISOTROPY}  "
          f"crossings {FLUFFWORKS_CROSSINGS}")

    check(an >= FLUFFWORKS_ANISOTROPY * 0.65,
          f"the strands comb (anisotropy {an:.2f}, was 1.78 before the fix)")
    check(abs(cr - FLUFFWORKS_CROSSINGS) < FLUFFWORKS_CROSSINGS * 0.4,
          f"the strands are the right fineness ({cr} against "
          f"{FLUFFWORKS_CROSSINGS})")
    check(alpha.min() >= 0.0 and alpha.max() <= 1.0, "the alpha is a clean 0-1 range")
    check(0.15 < alpha.mean() < 0.75, f"the coverage is sane (mean {alpha.mean():.2f})")

    print("=== RESULT:", "MASK QUALITY OK" if not failures else f"{len(failures)} FAILURES")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
