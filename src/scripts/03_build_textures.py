"""Bake the addon's PNG textures into Skyrim SE DDS files (BC7, full mip chain).

    py src/scripts/03_build_textures.py            # everything
    py src/scripts/03_build_textures.py Creatures   # one mod

Source : raw_assets/<ModFolder>/<creature>/incoming/textures/**/*.png
Target : build/<ModFolder>/textures/**/*.dds   (same relative path as the NIFs)

Format policy
    *_d / anything else  BC7_UNORM_SRGB   colour, 8 bit per channel
    *_n                  BC7_UNORM        normal + gloss in alpha (linear)

BC7 is what Skyrim SE itself ships; it keeps the alpha channel the normal map
needs for specular, which BC5 would throw away.
"""

from __future__ import annotations

import argparse
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXCONV = ROOT / "tools" / "texconv" / "texconv.exe"


def dds_info(path: Path) -> tuple[str, int, int, int]:
    """(format, width, height, mip levels) straight out of the DDS header."""
    data = path.read_bytes()
    if data[:4] != b"DDS ":
        return ("not dds", 0, 0, 0)
    height, width = struct.unpack_from("<II", data, 12)
    mips = struct.unpack_from("<I", data, 28)[0]
    fourcc = data[84:88]
    if fourcc == b"DX10":
        dxgi = struct.unpack_from("<I", data, 128)[0]
        fmt = {
            71: "BC1", 72: "BC1_SRGB", 74: "BC2", 75: "BC2_SRGB",
            76: "BC3", 77: "BC3_SRGB", 78: "BC4", 80: "BC5",
            98: "BC7_UNORM", 99: "BC7_UNORM_SRGB",
        }.get(dxgi, f"dxgi {dxgi}")
    else:
        fmt = {b"DXT1": "BC1", b"DXT3": "BC2", b"DXT5": "BC3"}.get(fourcc, repr(fourcc))
    return (fmt, width, height, mips)


def convert(png: Path, out: Path, fmt: str, force: bool = False) -> str:
    if out.exists() and not force and out.stat().st_mtime >= png.stat().st_mtime:
        return "up to date"
    if not TEXCONV.is_file():
        raise SystemExit(f"texconv not found: {TEXCONV}")
    out.parent.mkdir(parents=True, exist_ok=True)
    # texconv converts an sRGB source to linear and back again for an sRGB
    # target, so the stored bytes match the PNG.  "-l --ignore-srgb" is only
    # right for *linear* targets (normal maps), where it keeps the raw values;
    # using it on a colour map made the diffuse washed out in game.
    flags = [] if fmt.endswith("_SRGB") else ["-l", "--ignore-srgb"]
    cmd = [
        str(TEXCONV), "-nologo", "-y", *flags,
        "-f", fmt, "-o", str(out.parent), str(png),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        raise RuntimeError(f"texconv failed for {png.name}: {proc.stdout}{proc.stderr}")
    got_fmt, w, h, mips = dds_info(out)
    return f"{got_fmt} {w}x{h} {mips} mips {out.stat().st_size / 1024 / 1024:.2f} MB"


def pick_format(png: Path, preset: str) -> str:
    """best     BC7 colour + BC7 normal (gloss kept in alpha)   5.3 + 5.3 MB @2K
       balanced BC7 colour + BC3 normal                        5.3 + 2.7 MB
       small    BC1 colour + BC3 normal                        2.7 + 2.7 MB"""
    stem = png.stem.lower()
    normal = stem.endswith("_n") or stem.endswith("_normal")
    if not normal:
        return {"small": "BC1_UNORM_SRGB"}.get(preset, "BC7_UNORM_SRGB")
    if preset == "small":
        return "BC3_UNORM"
    if preset == "balanced":
        return "BC3_UNORM"
    return "BC7_UNORM"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mod", nargs="?", help="Creatures or Enemies (default: all)")
    ap.add_argument("--force", action="store_true", help="reconvert even if up to date")
    ap.add_argument("--preset", choices=("best", "balanced", "small"), default="best",
                    help="quality/size tradeoff (default: best)")
    args = ap.parse_args()

    raw = ROOT / "raw_assets"
    if not raw.is_dir():
        raise SystemExit(f"no raw_assets under {ROOT}")

    folders = sorted(p for p in raw.iterdir() if p.is_dir())
    if args.mod:
        want = args.mod.lower()
        folders = [p for p in folders if want in p.name.lower()]

    total_new, total_skip, total_bytes = 0, 0, 0
    started = time.time()
    for folder in folders:
        for texroot in sorted(folder.glob("*/incoming/textures")):
            for png in sorted(texroot.rglob("*.png")):
                # the fur mask is a working file (painted in Blender), not a
                # texture the game ever loads
                if png.stem.lower().endswith("_furmask"):
                    continue
                rel = png.relative_to(texroot)
                out = ROOT / "build" / folder.name / "textures" / rel.with_suffix(".dds")
                try:
                    status = convert(png, out, pick_format(png, args.preset), args.force)
                except RuntimeError as exc:
                    print(f"FAIL {rel}: {exc}")
                    return 1
                if status == "up to date":
                    total_skip += 1
                    continue
                total_new += 1
                total_bytes += out.stat().st_size
                print(f"  {folder.name}/textures/{rel} -> {status}")

    print(
        f"done: {total_new} converted, {total_skip} up to date, "
        f"{total_bytes / 1024 / 1024:.1f} MB in {time.time() - started:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
