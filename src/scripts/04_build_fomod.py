"""Turn build/<ModFolder> into a Nexus-ready archive with a FOMOD.

    py src/scripts/04_build_fomod.py                 # both mods, everything built
    py src/scripts/04_build_fomod.py Creatures --version 1.0.0

Archive layout (what Nexus gets):

    dist/HighPolyCreatures-1.0.0.zip
        fomod/ModuleConfig.xml      one install step per FOMOD page in creatures.csv
        fomod/Info.xml
        files/meshes/...            every built NIF, at its vanilla path
        files/textures/...          every built DDS, at its vanilla path

Steps are the pages from config/creatures.csv (Beasts, Monsters, ... DLC01, DLC02),
so Dawnguard and Dragonborn content are opt-in pages inside one download. Inside a
step, groups are the creature categories and each plugin is one creature.
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.dom import minidom

ROOT = Path(__file__).resolve().parents[2]
MOD_FOLDERS = {"Creatures": "HighPolyCreatures", "Enemies": "HighPolyEnemies"}
MOD_NAMES = {"Creatures": "High Poly Creatures", "Enemies": "High Poly Enemies"}
DLC_PAGES = ("DLC01", "DLC02")

# Non-body NIFs (skeletons, FX, LOD) never belong to a creature plugin.
NON_BODY = (
    "skeleton", "fx", "farskin", "lod", "particles", "projectile", "explosion",
    "blood", "attach", "inhand", "dead", "impact", "crumble", "sack", "eggs",
    "landing", "dust", "stomp", "whip", "magic", "trail", "temp", "gravestone",
)


@dataclass
class Creature:
    mod: str
    page: str
    name: str
    category: str
    prefixes: list[str]
    notes: str
    files: list[Path] = field(default_factory=list)


def load_creatures() -> list[Creature]:
    out = []
    with (ROOT / "config" / "creatures.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("mod") or row["mod"].strip().startswith("#"):
                continue
            prefixes = [p.strip().lower().replace("/", "\\")
                        for p in row["prefixes"].split(";") if p.strip()]
            out.append(Creature(
                row["mod"].strip(), row["page"].strip(), row["creature"].strip(),
                row["category"].strip(), prefixes, (row.get("notes") or "").strip(),
            ))
    return out


def collect(mod_folder: str, creatures: list[Creature]) -> list[Path]:
    """Every built file, attached to the creature whose prefix matches its path."""
    build = ROOT / "build" / mod_folder
    orphans: list[Path] = []
    for path in sorted(build.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".nif", ".dds"):
            continue
        rel = path.relative_to(build).as_posix().lower()
        if path.suffix.lower() == ".nif" and any(p in Path(rel).name for p in NON_BODY):
            orphans.append(path)
            continue
        # creature prefixes are written without the meshes/ root
        bare = rel[len("meshes/"):] if rel.startswith("meshes/") else rel
        hit = None
        for c in creatures:
            if any(bare.startswith(pfx.replace("\\", "/")) for pfx in c.prefixes):
                hit = c
                break
        if hit is None and path.suffix.lower() == ".dds":
            # textures/actors/<creature>/<creature>_d.dds
            parts = rel.split("/")
            if len(parts) >= 3 and parts[0] == "textures":
                hit = next((c for c in creatures if c.name.lower() == parts[2]), None)
        if hit:
            hit.files.append(path)
        else:
            orphans.append(path)
    return orphans


def expand_variants(mod: str, creatures: list[Creature]) -> int:
    """Copy each creature's built body NIF over its vanilla variant paths.

    wolf.nif, wolfblack.nif, wolfred.nif and wolffire.nif are the same mesh with
    different textures; the AI model replaces all of them, so every wolf in game
    changes instead of only one in four. Variant NIFs are found in reference/
    under the same prefixes the creature owns.
    """
    ref_root = ROOT / "reference" / MOD_FOLDERS[mod]
    added = 0
    for c in creatures:
        built_nifs = [f for f in c.files if f.suffix.lower() == ".nif"]
        if not built_nifs:
            continue
        main = next((f for f in built_nifs if f.stem.lower() == c.name.lower()),
                    max(built_nifs, key=lambda p: p.stat().st_size))
        ref_dir = ref_root / c.name
        if not ref_dir.is_dir():
            continue
        variants = []
        for ref in ref_dir.rglob("*.nif"):
            if any(p in ref.name.lower() for p in NON_BODY):
                continue
            rel = ref.relative_to(ref_dir).as_posix().lower()
            # prefixes are written without the meshes/ root
            bare = rel[len("meshes/"):] if rel.startswith("meshes/") else rel
            if not any(bare.startswith(pfx.replace("\\", "/")) for pfx in c.prefixes):
                continue
            out = ROOT / "build" / MOD_FOLDERS[mod] / ref.relative_to(ref_dir)
            if out.exists() or out == main:
                continue
            variants.append((ref, out))
        for ref, out in variants:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(main.read_bytes())
            c.files.append(out)
            added += 1
    return added


def build_xml(mod: str, creatures: list[Creature]) -> ET.ElementTree:
    pages: dict[str, list[Creature]] = {}
    for c in creatures:
        if c.files:
            pages.setdefault(c.page, []).append(c)

    ordered = sorted(pages, key=lambda p: (p in DLC_PAGES, list(pages).index(p)))

    config = ET.Element("config", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
    })
    ET.SubElement(config, "moduleName").text = MOD_NAMES[mod]

    steps = ET.SubElement(config, "installSteps", {"order": "Explicit"})
    for page in ordered:
        step = ET.SubElement(steps, "installStep", {"name": page})
        groups_el = ET.SubElement(step, "optionalFileGroups", {"order": "Explicit"})

        by_cat: dict[str, list[Creature]] = {}
        for c in pages[page]:
            by_cat.setdefault(c.category, []).append(c)

        for cat in sorted(by_cat):
            group = ET.SubElement(groups_el, "group", {
                "name": cat.capitalize(), "type": "SelectAny",
            })
            plugins = ET.SubElement(group, "plugins", {"order": "Explicit"})
            for c in sorted(by_cat[cat], key=lambda x: x.name):
                plugin = ET.SubElement(plugins, "plugin", {"name": c.name})
                desc = c.notes or f"High poly {c.name}"
                ET.SubElement(plugin, "description").text = desc
                files_el = ET.SubElement(plugin, "files")
                for f in sorted(c.files):
                    rel = f.relative_to(ROOT / "build" / MOD_FOLDERS[mod]).as_posix()
                    ET.SubElement(files_el, "file", {
                        "source": f"files/{rel}",
                        "destination": rel,
                    })
                ET.SubElement(plugin, "conditionFlags")
        ET.SubElement(step, "conditions")

    ET.SubElement(config, "requiredInstallFile")
    ET.SubElement(config, "type").text = "Basic"
    return ET.ElementTree(config)


def write_info(mod: str, version: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<fomod>\n"
        f"  <Name>{MOD_NAMES[mod]}</Name>\n"
        f"  <Version>{version}</Version>\n"
        "  <Description>High poly creature replacers for Skyrim SE.</Description>\n"
        "</fomod>\n"
    )


def pretty(tree: ET.ElementTree) -> str:
    raw = ET.tostring(tree.getroot(), encoding="unicode")
    xml = minidom.parseString(raw).toprettyxml(indent="  ")
    return "\n".join(line for line in xml.splitlines() if line.strip()) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mod", nargs="?", help="Creatures or Enemies (default: both)")
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--list", action="store_true", help="show coverage, write nothing")
    args = ap.parse_args()

    wanted = [args.mod] if args.mod else ["Creatures", "Enemies"]
    all_creatures = load_creatures()
    rc = 0

    for mod in wanted:
        folder = MOD_FOLDERS[mod]
        creatures = [c for c in all_creatures if c.mod == mod]
        orphans = collect(folder, creatures)
        variants = expand_variants(mod, creatures)
        built = [c for c in creatures if c.files]
        missing = [c for c in creatures if not c.files]

        print(f"=== {MOD_NAMES[mod]} ===")
        print(f"  {len(built)}/{len(creatures)} creatures built, "
              f"{sum(len(c.files) for c in built)} files"
              + (f" ({variants} variant copies)" if variants else ""))
        if missing:
            print(f"  not built yet: {', '.join(c.name for c in missing)}")
        if orphans:
            print(f"  unmatched files: "
                  f"{', '.join(str(p.relative_to(ROOT / 'build' / folder)) for p in orphans)}")
        if not built:
            print("  nothing to package")
            rc = 1
            continue
        if args.list:
            continue

        dist = ROOT / "dist"
        dist.mkdir(exist_ok=True)
        out_zip = dist / f"{folder}-{args.version}.zip"
        tree = build_xml(mod, creatures)
        xml_text = pretty(tree)

        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.writestr("fomod/ModuleConfig.xml", xml_text)
            zf.writestr("fomod/Info.xml", write_info(mod, args.version))
            for c in built:
                for f in c.files:
                    rel = f.relative_to(ROOT / "build" / folder).as_posix()
                    zf.write(f, f"files/{rel}")

        size = out_zip.stat().st_size
        print(f"  -> {out_zip.relative_to(ROOT)} ({size / 1024 / 1024:.1f} MB)")

    return rc


if __name__ == "__main__":
    sys.exit(main())
