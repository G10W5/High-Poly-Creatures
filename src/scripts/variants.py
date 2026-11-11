"""Colour variants shared by 08_build_variants.py and 04_build_fomod.py.

Vanilla gives some animals several NIFs over one skeleton that differ only in
coat colour (wolfblack/wolfred, frostbitespidercold).  We deliver one texture
per animal, so every other coat is derived from ours by an HSV shift held in
config/variants.csv (hue in degrees, sat/val as multipliers).  The fur shell
gets the same shift so the coat follows, and the variant NIF is copied from
the built main NIF with its Diffuse slot repointed.

Only our own generated textures are ever tinted - nothing here ships a pixel
that did not come from this project's models (see README, asset provenance).
"""
from __future__ import annotations

import csv
import fnmatch
import sys
from dataclasses import dataclass
from pathlib import Path

from common import NON_BODY_NAME_PARTS, ROOT, Creature

VARIANTS_CSV = ROOT / "config" / "variants.csv"
PYNIFLY_PATH = ROOT / "tools" / "pynifly" / "io_scene_nifly"


@dataclass(frozen=True)
class Variant:
    mod: str
    creature: str
    variant: str
    hue: float      # degrees to rotate hue by
    sat: float      # saturation multiplier
    val: float      # value (brightness) multiplier
    notes: str = ""


def load_variants() -> dict[tuple[str, str], Variant]:
    """{(creature_lower, variant_lower): row} from config/variants.csv."""
    out: dict[tuple[str, str], Variant] = {}
    if not VARIANTS_CSV.is_file():
        return out
    with VARIANTS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("creature") or (row.get("mod") or "").strip().startswith("#"):
                continue
            v = Variant(
                mod=row["mod"].strip(),
                creature=row["creature"].strip(),
                variant=row["variant"].strip(),
                hue=float(row.get("hue") or 0),
                sat=float(row.get("sat") or 1.0),
                val=float(row.get("val") or 1.0),
                notes=(row.get("notes") or "").strip(),
            )
            out[(v.creature.lower(), v.variant.lower())] = v
    return out


def matches(bare: str, prefixes) -> bool:
    """A vanilla-relative path against a creature's prefixes (wildcards allowed)."""
    for pfx in prefixes:
        pfx = pfx.replace("\\", "/").lower()
        bare = bare.replace("\\", "/").lower()
        if any(ch in pfx for ch in "*?["):
            if fnmatch.fnmatch(bare, pfx):
                return True
        elif bare.startswith(pfx):
            return True
    return False


def textures_dir(creature: Creature) -> Path:
    return creature.incoming_dir / "textures" / "actors" / creature.name


def _tint_png(src: Path, dst: Path, hue: float, sat: float, val: float) -> Path:
    """HSV-shift one PNG, keeping the alpha channel byte-for-byte.

    The shell's alpha IS the strand mask, so only the colour may move.
    """
    from PIL import Image

    with Image.open(src) as img:
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        h, s, v = img.convert("RGB").convert("HSV").split()
        shift = int(round(hue * 255.0 / 360.0))
        if shift:
            h = h.point(lambda x: (x + shift) % 256)
        if sat != 1.0:
            s = s.point(lambda x: min(255, int(round(x * sat))))
        if val != 1.0:
            v = v.point(lambda x: min(255, int(round(x * val))))
        out = Image.merge("HSV", (h, s, v)).convert("RGB")
        if alpha is not None:
            out.putalpha(alpha)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    return dst


def tint_textures(v: Variant, creature: Creature, with_shell: bool) -> list[Path]:
    """<variant>_d.png (+ <variant>_shell.png): hue/sat/value shifted copies."""
    made = []
    names = [f"{creature.name}_d.png"]
    if with_shell:
        names.append(f"{creature.name}_shell.png")
    for src_name in names:
        src = textures_dir(creature) / src_name
        if not src.is_file():
            continue
        dst = textures_dir(creature) / src_name.replace(
            f"{creature.name}_", f"{v.variant}_", 1)
        made.append(_tint_png(src, dst, v.hue, v.sat, v.val))
    return made


def retarget_nif(nif_path: Path, creature_name: str, variant_name: str) -> int:
    """Point the variant NIF's Diffuse slots at the variant textures.

    The normal and the _sk lighting maps stay shared - vanilla does the same
    (wolfblack uses Wolf_n.dds and Wolf_sk.dds).  Returns the slots changed.
    """
    if str(PYNIFLY_PATH) not in sys.path:
        sys.path.insert(0, str(PYNIFLY_PATH))
    from pyn.pynifly import NifFile

    changed = 0
    nif = NifFile(str(nif_path))
    try:
        for shape in nif.shapes:
            diffuse = shape.shader.textures.get("Diffuse") or ""
            head, sep, fname = diffuse.replace("/", "\\").rpartition("\\")
            if not sep:
                continue  # no directory to keep - leave it alone
            low = fname.lower()
            new = None
            if low == f"{creature_name.lower()}_d.dds":
                new = f"{variant_name}_d.dds"
            elif low == f"{creature_name.lower()}_shell.dds":
                new = f"{variant_name}_shell.dds"
            if new:
                shape.set_texture("Diffuse", f"{head}\\{new}")
                changed += 1
        nif.save()
    finally:
        nif.close()
    return changed
