"""Probe every vanilla body NIF and write the mesh/bone contract per creature.

Uses PyNifly's standalone layer (no Blender needed).

Outputs:
  reference/nif_report.csv                        one row per shape
  reference/<Mod>/<creature>/bone_contract.md     per-creature mesh + bone contract

Run:  py src/scripts/01_inventory.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from common import ROOT, human_size, is_body_file, load_creatures

NIFLIB = ROOT / "tools" / "pynifly" / "io_scene_nifly"
if str(NIFLIB) not in sys.path:
    sys.path.insert(0, str(NIFLIB))

try:
    from pyn.pynifly import NifFile
except Exception as exc:  # pragma: no cover - only when PyNifly is missing
    NifFile = None
    IMPORT_ERROR = exc


def probe(path: Path) -> list[dict]:
    """Return one dict per shape in the NIF."""
    nif = NifFile(str(path))
    shapes = []
    for shape in nif.shapes:
        shapes.append(
            {
                "name": shape.name,
                "verts": len(shape.verts),
                "tris": len(shape.tris),
                "partitions": len(shape.partitions),
                "bones": list(dict.fromkeys(shape.bone_names)),
                "textures": {k: v for k, v in (shape.textures or {}).items() if v},
            }
        )
    return shapes


def contract_markdown(creature, probed: list[tuple[Path, list[dict]]]) -> str:
    lines = [f"# {creature.name} - mesh contract", ""]
    all_bones: list[str] = []
    for path, shapes in probed:
        for shape in shapes:
            for bone in shape["bones"]:
                if bone not in all_bones:
                    all_bones.append(bone)
    lines.append(f"Union of bones across all body meshes: **{len(all_bones)}**")
    lines.append("")
    lines.append("A finished model may only use bones from this list.")
    lines.append("")
    for path, shapes in probed:
        rel = path.relative_to(creature.ref_dir)
        lines.append(f"## `{rel}`")
        lines.append("")
        lines.append("| Shape | Verts | Tris | Partitions | Bones |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for shape in shapes:
            lines.append(
                f"| `{shape['name']}` | {shape['verts']:,} | {shape['tris']:,} | "
                f"{shape['partitions']} | {len(shape['bones'])} |"
            )
        lines.append("")
        textures = {}
        for shape in shapes:
            for slot, value in shape["textures"].items():
                textures.setdefault(slot, set()).add(value)
        if textures:
            lines.append("Textures:")
            lines.append("")
            for slot, values in textures.items():
                for value in sorted(values):
                    lines.append(f"- **{slot}:** `{value}`")
            lines.append("")
    if all_bones:
        lines.append("## Bone list")
        lines.append("")
        lines.append(", ".join(f"`{b}`" for b in all_bones))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    if NifFile is None:
        print(f"ERROR: PyNifly not available ({IMPORT_ERROR})")
        return 1

    creatures = load_creatures()
    report_rows: list[dict] = []
    print(
        f"{'MOD':<10} {'CREATURE':<22} {'NIFS':>4} {'SHAPES':>6} "
        f"{'VERTS':>9} {'TRIS':>9} {'BONES':>5} {'SIZE':>9}"
    )
    print("-" * 92)

    totals = {"verts": 0, "tris": 0, "nifs": 0, "shapes": 0}
    problems = 0

    for creature in creatures:
        files = sorted(creature.ref_dir.rglob("*.nif"))
        body_files = [f for f in files if is_body_file(f.name)]
        size = sum(f.stat().st_size for f in files)
        probed: list[tuple[Path, list[dict]]] = []
        verts = tris = shapes = bones = 0

        for path in body_files:
            try:
                parsed = probe(path)
            except Exception as exc:
                print(f"  WARNING: {creature.name}: {path.name}: {exc}")
                problems += 1
                continue
            probed.append((path, parsed))
            shapes += len(parsed)
            verts += sum(s["verts"] for s in parsed)
            tris += sum(s["tris"] for s in parsed)
            for shape in parsed:
                bones = max(bones, len(shape["bones"]))
                for slot, value in shape["textures"].items():
                    report_rows.append(
                        {
                            "mod": creature.mod,
                            "creature": creature.name,
                            "nif": str(path.relative_to(creature.ref_dir)),
                            "shape": shape["name"],
                            "verts": shape["verts"],
                            "tris": shape["tris"],
                            "partitions": shape["partitions"],
                            "bones": len(shape["bones"]),
                            "texture_slot": slot,
                            "texture": value,
                        }
                    )

        (creature.ref_dir / "bone_contract.md").write_text(
            contract_markdown(creature, probed), encoding="utf-8"
        )
        totals["verts"] += verts
        totals["tris"] += tris
        totals["nifs"] += len(body_files)
        totals["shapes"] += shapes
        print(
            f"{creature.mod:<10} {creature.name:<22} {len(body_files):>4} {shapes:>6} "
            f"{verts:>9,} {tris:>9,} {bones:>5} {human_size(size):>9}"
        )

    report_path = ROOT / "reference" / "nif_report.csv"
    with report_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "mod", "creature", "nif", "shape", "verts", "tris",
                "partitions", "bones", "texture_slot", "texture",
            ],
        )
        writer.writeheader()
        writer.writerows(report_rows)

    print("-" * 92)
    print(
        f"{len(creatures)} creatures | {totals['nifs']} body NIFs | "
        f"{totals['shapes']} shapes | {totals['verts']:,} verts | {totals['tris']:,} tris"
    )
    print(f"report: {report_path}")
    return 0 if problems == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
