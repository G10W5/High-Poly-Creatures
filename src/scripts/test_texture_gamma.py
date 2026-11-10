"""Find the texconv flags that reproduce the source PNG byte for byte.

The built diffuse came out washed out (much brighter than the PNG), so the
gamma pipeline in 03_build_textures.py is wrong.  This converts the wolf
diffuse with several flag combinations and compares the stored bytes against
the source PNG's bytes (read as raw data, no colour management).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXCONV = ROOT / "tools" / "texconv" / "texconv.exe"
SRC = ROOT / "raw_assets" / "HighPolyCreatures" / "wolf" / "incoming" / "textures" / "actors" / "wolf" / "wolf_d.png"
TMP = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "opencode" / "gammatest"

COMBOS = {
    "current": ["-l", "--ignore-srgb"],
    "plain": [],
    "srgb": ["-srgb"],
    "linear": ["-l"],
    "srgb_only": ["-srgb", "--ignore-srgb"],
}

FORMATS = {
    "BC7_UNORM_SRGB": "BC7_UNORM_SRGB",
    "BC1_UNORM_SRGB": "BC1_UNORM_SRGB",
    "BC3_UNORM": "BC3_UNORM",
}


def convert(flags: list[str], fmt: str, outdir: Path) -> Path:
    # texconv names the output after the SOURCE file, so every combination needs
    # its own directory or they overwrite each other.
    outdir = outdir / f"{'_'.join(flags) or 'plain'}_{fmt}"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{SRC.stem}.dds"
    if out.exists():
        out.unlink()
    cmd = [str(TEXCONV), "-nologo", "-y", "-f", fmt, *flags, "-o", str(outdir), str(SRC)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        print(f"    texconv failed: {flags} {fmt}: {proc.stdout}{proc.stderr}")
    return out


def read_raw(path: Path) -> tuple[list, tuple]:
    """Return (samples, size) of the file's raw pixel bytes, no colour management."""
    import bpy  # only available inside Blender

    img = bpy.data.images.load(str(path))
    img.colorspace_settings.name = "Non-Color"
    px = list(img.pixels)
    size = tuple(img.size)
    bpy.data.images.remove(img)
    return px, size


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    # Convert first: loading the PNG into Blender while texconv reads it makes
    # texconv see a different (linear) source.
    outputs = []
    for name, flags in COMBOS.items():
        for fmt in FORMATS:
            out = convert(flags, fmt, TMP)
            if out.exists():
                outputs.append((name, fmt, out))
            else:
                print(f"    texconv failed: {name} {fmt}")

    src_px, src_size = read_raw(SRC)
    print(f"source {SRC.name} {src_size[0]}x{src_size[1]}")
    n = len(src_px) // 4
    probes = [n // 4, n // 3, n // 2, (2 * n) // 3, (3 * n) // 4]
    print("source samples:", [round(src_px[i * 4], 4) for i in probes])

    for name, fmt, out in outputs:
        px, size = read_raw(out)
        vals = [round(px[i * 4], 4) for i in probes]
        err = sum(abs(px[i * 4] - src_px[i * 4]) for i in probes) / len(probes)
        print(f"  {name:<10} {fmt:<16} R samples {vals}  mean |err| {err:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
