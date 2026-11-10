"""Add the per-creature fur flag to config/creatures.csv.

Most Skyrim creatures have fur, several are bare (spiders, crabs, wisps,
automata, dragons).  The flag says which get the FluffyWorks-style shell coat.

Also rewrites the file properly: a few notes contain commas, which made the
rows longer than the header.
"""

import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[2] / "config" / "creatures.csv"

# the mammals and birds that get a coat
SHELL = {
    "wolf", "dog", "bear", "sabrecat", "mammoth", "skeever", "deer", "fox",
    "hare", "chicken", "cow", "highlandcow", "horse", "goat", "vale_sabrecat",
    "vale_elk", "armored_husky", "soulcairn_horse", "werewolfbeast", "werebear",
    "troll", "riekling", "boar_riekling",
}

with CSV_PATH.open(encoding="utf-8", newline="") as fh:
    rows = list(csv.reader(fh))

header = rows[0]
out_rows = []
for row in rows[1:]:
    if not row:
        continue
    mod, page, creature, category, prefixes = row[:5]
    notes = ",".join(row[5:]).strip()
    fur = "shell" if creature in SHELL else "none"
    out_rows.append([mod, page, creature, category, prefixes, fur, notes])

with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["mod", "page", "creature", "category", "prefixes", "fur", "notes"])
    writer.writerows(out_rows)

print(f"fur column written: {sum(1 for r in out_rows if r[5] == 'shell')} shell, "
      f"{sum(1 for r in out_rows if r[5] == 'none')} none, {len(out_rows)} rows")
