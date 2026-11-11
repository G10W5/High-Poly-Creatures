"""Build the colour variants of a creature (config/variants.csv).

Vanilla gives some animals several NIFs over one skeleton that differ only in
coat colour (wolfblack/wolfred, frostbitespidercold).  We deliver one texture
per animal, so the other coats are derived from ours: the diffuse (and the fur
shell) are hue/sat/value shifted, and a copy of the body NIF is repointed at
them.

    py src/scripts/08_build_variants.py            # everything in the config
    py src/scripts/08_build_variants.py wolf       # one creature

Run after 07_build_all.py (it needs the built body) and before
04_build_fomod.py (which packages the variant NIFs).  03_build_textures.py
turns the tinted PNGs into DDS afterwards.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from common import BUILD, MOD_FOLDERS, ROOT, load_creatures
from variants import (
    load_variants, matches, retarget_nif, tint_textures, textures_dir,
)

sys.path.insert(0, str(ROOT / "tools" / "pynifly" / "io_scene_nifly"))


def build_root(creature) -> Path:
    return BUILD / MOD_FOLDERS[creature.mod]


def ref_root(creature) -> Path:
    return ROOT / "reference" / MOD_FOLDERS[creature.mod] / creature.name


def main_nif(creature) -> Path | None:
    """The built body NIF (the one that matches the creature's own name)."""
    build = build_root(creature)
    if not build.is_dir():
        return None
    hits = []
    for path in build.rglob("*.nif"):
        rel = path.relative_to(build).as_posix().lower()
        bare = rel[len("meshes/"):] if rel.startswith("meshes/") else rel
        if not matches(bare, creature.prefixes):
            continue
        if path.stem.lower() == creature.name.lower():
            hits.append(path)
    if not hits:
        return None
    # the rigged "character assets" copy is the one we can use
    rigged = [p for p in hits if "character assets" in str(p).lower()]
    return sorted(rigged or hits, key=str)[0]


def variant_nif_path(creature, variant: str) -> Path | None:
    """Where the variant NIF has to live: the vanilla path, under build/."""
    ref = ref_root(creature)
    if not ref.is_dir():
        return None
    for path in ref.rglob("*.nif"):
        if path.stem.lower() == variant.lower():
            return build_root(creature) / path.relative_to(ref)
    return None


def main() -> int:
    only = [a.lower() for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []
    creatures = {c.name.lower(): c for c in load_creatures()}
    rows = load_variants()

    if not rows:
        print("config/variants.csv has no rows")
        return 1

    done = 0
    for (creature_name, variant_name), row in sorted(rows.items()):
        if only and creature_name not in only:
            continue
        creature = creatures.get(creature_name)
        if creature is None:
            print(f"{variant_name}: no creature '{creature_name}' in creatures.csv")
            continue

        body = main_nif(creature)
        if body is None:
            print(f"{variant_name}: {creature_name} is not built yet (run 07_build_all.py)")
            continue

        out = variant_nif_path(creature, row.variant)
        if out is None:
            print(f"{variant_name}: no vanilla NIF with that name")
            continue

        # 1. the body copy
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(body, out)

        # 2. tinted textures: the diffuse, and the fur shell when it has one
        tex_dir = textures_dir(creature)
        has_shell = (tex_dir / f"{creature.name}_shell.png").is_file()
        made = tint_textures(row, creature, has_shell)

        # 3. point the copy at them
        changed = retarget_nif(out, creature.name, row.variant)

        done += 1
        print(f"{creature.name} -> {row.variant}: {out.relative_to(ROOT)} "
              f"({changed} texture slots, "
              f"{', '.join(p.name for p in made) or 'no textures'})")

    print(f"done: {done} variant(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
