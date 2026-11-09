"""Extract the vanilla creature NIFs from Skyrim - Meshes0.bsa.

Creates, per creature:
  reference/<Mod>/<creature>/meshes/...   read-only vanilla reference
  raw_assets/<Mod>/<creature>/incoming/   where the finished model goes
  raw_assets/<Mod>/<creature>/spec.md     the modelling contract

Run:  py src/scripts/00_extract_vanilla.py
"""
from __future__ import annotations

import csv
import fnmatch
import sys
from pathlib import PureWindowsPath

from bethesda_structs.archive.bsa import BSAArchive

from common import (
    BUILD,
    DIST,
    RAW_ASSETS,
    REFERENCE,
    ROOT,
    SKIP_NAME_PARTS,
    VANILLA_MESHES_BSA,
    Creature,
    human_size,
    is_body_file,
    load_creatures,
)


def as_windows(path: PureWindowsPath) -> str:
    return str(path).replace("/", "\\")


def matches_prefix(path: str, prefix: str) -> bool:
    if "*" in prefix or "?" in prefix:
        return fnmatch.fnmatchcase(path, prefix)
    return path == prefix or path.startswith(prefix + "\\")


def build_spec(creature: Creature, files: list[tuple[str, int]]) -> str:
    total = sum(size for _, size in files)
    body = sorted(
        ((p, s) for p, s in files if is_body_file(PureWindowsPath(p).name)),
        key=lambda item: item[1],
        reverse=True,
    )
    skeletons = [p for p, _ in files if "skeleton" in PureWindowsPath(p).name.lower()]

    lines: list[str] = []
    lines.append(f"# {creature.name}")
    lines.append("")
    lines.append(f"- **Mod:** {creature.mod_name}")
    lines.append(f"- **FOMOD page:** {creature.page}")
    lines.append(f"- **Category:** {creature.category}")
    lines.append(f"- **Vanilla prefixes:** " + ", ".join(f"`{p}`" for p in creature.prefixes))
    lines.append(f"- **Reference files:** {len(files)} NIFs, {human_size(total)}")
    if creature.notes:
        lines.append(f"- **Notes:** {creature.notes}")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("| Vanilla file | Size | Role |")
    lines.append("| --- | --- | --- |")
    for path, size in sorted(files, key=lambda item: item[1], reverse=True):
        name = PureWindowsPath(path).name.lower()
        if "skeleton" in name:
            role = "skeleton / bind pose"
        elif is_body_file(name):
            role = "body - replace"
        else:
            role = "FX / LOD / prop - do not replace"
        lines.append(f"| `{path}` | {human_size(size)} | {role} |")
    lines.append("")
    lines.append("## Contract (non-negotiable)")
    lines.append("")
    lines.append(f"Full mesh stats and the exact bone list: `{creature.ref_dir.relative_to(ROOT) / 'bone_contract.md'}`")
    lines.append("")
    lines.append("1. Keep the exact vanilla bone names. No added bones, no removed bones.")
    lines.append("2. Maximum 4 bone influences per vertex.")
    lines.append("3. Maximum ~65,500 vertices per skin partition (16-bit indices).")
    lines.append("4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.")
    lines.append("5. Do not re-export the whole NIF. The finished geometry is transplanted into the")
    lines.append("   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.")
    lines.append("6. Bounding sphere / box must be recomputed after the transplant.")
    lines.append("")
    lines.append("## Deliverable")
    lines.append("")
    lines.append(f"Drop the finished model in `{creature.incoming_dir}`.")
    lines.append("")
    lines.append("Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).")
    lines.append("A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla")
    lines.append("skeleton during the build. If you deliver a finished `.nif`, it must already be")
    lines.append("weighted to the correct vanilla skeleton.")
    lines.append("")
    if skeletons:
        lines.append("Skeleton file(s) to weight against: " + ", ".join(f"`{s}`" for s in skeletons))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    for folder in (REFERENCE, RAW_ASSETS, BUILD, DIST):
        folder.mkdir(parents=True, exist_ok=True)

    creatures = load_creatures()
    print(f"config: {len(creatures)} creatures")

    if not VANILLA_MESHES_BSA.is_file():
        print(f"ERROR: vanilla archive not found: {VANILLA_MESHES_BSA}")
        return 1

    print(f"reading {VANILLA_MESHES_BSA.name} (this takes a moment)...")
    archive = BSAArchive.parse_file(str(VANILLA_MESHES_BSA))
    entries = [(PureWindowsPath(f.filepath), f.data) for f in archive.iter_files()]
    print(f"archive: {len(entries)} files")

    manifest_rows: list[dict[str, str | int]] = []
    seen: set[str] = set()
    matched_total = 0

    for creature in creatures:
        prefixes = ["meshes\\" + p.lower().replace("/", "\\") for p in creature.prefixes]
        matched: list[tuple[PureWindowsPath, bytes]] = []

        for path, data in entries:
            if not path.name.lower().endswith(".nif"):
                continue
            win = as_windows(path).lower()
            if not any(matches_prefix(win, prefix) for prefix in prefixes):
                continue
            name = path.name.lower()
            if any(part in name for part in SKIP_NAME_PARTS):
                continue
            if win in seen:
                print(f"  WARNING: {win} matched twice; keeping the first occurrence")
                continue
            matched.append((path, data))
            seen.add(win)

        if not matched:
            print(f"  MISSING: {creature.mod}/{creature.name} (no NIFs matched)")
            continue

        files: list[tuple[str, int]] = []
        for path, data in matched:
            relative = PureWindowsPath(*path.parts)
            target = creature.ref_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append((as_windows(relative), len(data)))
            manifest_rows.append(
                {
                    "mod": creature.mod,
                    "page": creature.page,
                    "creature": creature.name,
                    "file": as_windows(relative),
                    "bytes": len(data),
                }
            )

        creature.incoming_dir.mkdir(parents=True, exist_ok=True)
        creature.spec_path.write_text(build_spec(creature, files), encoding="utf-8")
        matched_total += 1
        print(f"  {creature.mod}/{creature.name}: {len(files)} files, {human_size(sum(s for _, s in files))}")

    manifest_path = REFERENCE / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["mod", "page", "creature", "file", "bytes"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print("")
    print(f"done: {matched_total}/{len(creatures)} creatures, {len(manifest_rows)} NIFs extracted")
    print(f"manifest: {manifest_path}")
    if matched_total != len(creatures):
        print("some creatures had no matching NIFs - see the MISSING lines above")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
