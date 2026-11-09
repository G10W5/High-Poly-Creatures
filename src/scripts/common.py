"""Shared constants and helpers for the High-Poly Creature overhaul pipeline."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIG = ROOT / "config" / "creatures.csv"
REFERENCE = ROOT / "reference"
RAW_ASSETS = ROOT / "raw_assets"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition")
DATA_DIR = GAME_DIR / "Data"
VANILLA_MESHES_BSA = DATA_DIR / "Skyrim - Meshes0.bsa"

# Logical mod name -> folder name on disk.
MOD_FOLDERS = {
    "Creatures": "HighPolyCreatures",
    "Enemies": "HighPolyEnemies",
}
MOD_NAMES = {
    "Creatures": "High Poly Creatures",
    "Enemies": "High Poly Enemies",
}

# NIFs that are not the actor body: test poses, static display copies, markers, baked trailer poses.
SKIP_NAME_PARTS = ("test", "static", "marker", "trailertemp")

# Files that are not the replaceable body mesh.
NON_BODY_NAME_PARTS = (
    "skeleton", "fx", "farskin", "lod", "particles", "projectile",
    "explosion", "blood", "attach", "inhand", "dead", "impact",
    "crumble", "sack", "eggs", "landing", "dust", "stomp", "whip",
    "magic", "trail", "temp", "gravestone",
)


@dataclass(frozen=True)
class Creature:
    mod: str
    page: str
    name: str
    category: str
    prefixes: tuple[str, ...]
    notes: str = ""

    @property
    def mod_folder(self) -> str:
        return MOD_FOLDERS[self.mod]

    @property
    def mod_name(self) -> str:
        return MOD_NAMES[self.mod]

    @property
    def ref_dir(self) -> Path:
        return REFERENCE / self.mod_folder / self.name

    @property
    def incoming_dir(self) -> Path:
        return RAW_ASSETS / self.mod_folder / self.name / "incoming"

    @property
    def spec_path(self) -> Path:
        return RAW_ASSETS / self.mod_folder / self.name / "spec.md"


def load_creatures() -> list[Creature]:
    creatures: list[Creature] = []
    with CONFIG.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("mod") or row["mod"].strip().startswith("#"):
                continue
            creatures.append(
                Creature(
                    mod=row["mod"].strip(),
                    page=row["page"].strip(),
                    name=row["creature"].strip(),
                    category=row["category"].strip(),
                    prefixes=tuple(
                        p.strip() for p in row["prefixes"].split(";") if p.strip()
                    ),
                    notes=(row.get("notes") or "").strip(),
                )
            )
    return creatures


def is_body_file(name: str) -> bool:
    lowered = name.lower()
    return not any(part in lowered for part in NON_BODY_NAME_PARTS)


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"
