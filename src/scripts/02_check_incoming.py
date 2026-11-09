"""Report which creatures have delivered models in raw_assets/<Mod>/<creature>/incoming/.

Run:  py src/scripts/02_check_incoming.py
"""
from __future__ import annotations

from common import load_creatures


def main() -> int:
    ready = 0
    partial = 0
    empty = 0

    for creature in load_creatures():
        expected = {
            f.stem.lower()
            for f in creature.ref_dir.rglob("*.nif")
            if not any(part in f.name.lower() for part in
                       ("skeleton", "fx", "farskin", "lod", "particles", "projectile",
                        "explosion", "blood", "attach", "inhand", "dead", "impact",
                        "crumble", "sack", "eggs", "landing", "dust", "stomp", "whip",
                        "magic", "trail", "temp", "gravestone"))
        }
        delivered = {
            p.stem.lower()
            for p in creature.incoming_dir.glob("*")
            if p.is_file() and p.suffix.lower() in {".nif", ".blend", ".fbx", ".obj"}
        }
        missing = sorted(expected - delivered)

        if not delivered:
            empty += 1
            status = "empty"
        elif missing:
            partial += 1
            status = f"{len(delivered)}/{len(expected)} - missing {', '.join(missing[:4])}"
        else:
            ready += 1
            status = f"{len(delivered)}/{len(expected)} ready"

        print(f"[{status:<60}] {creature.mod}/{creature.name}")

    total = ready + partial + empty
    print("")
    print(f"{ready}/{total} complete | {partial} partial | {empty} still waiting")
    return 0 if ready == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
