# FOMOD template

Two installers are generated from the same manifest:

- `High Poly Creatures` — Beasts, Farm & Ambient, Dawnguard, Dragonborn, Extras
- `High Poly Enemies` — Monsters, Undead, Dwemer, Falmer, Dragons, Dawnguard, Dragonborn, Extras

Every page:

1. Core (required)
2. Texture resolution (2K default, 4K optional later)
3. One page per pack
4. Extras (parallax, compatibility patches)
5. Load order note for any ESL-flagged pack

Rules:

- A page never ships a plugin without the assets it points at.
- Group A creatures (race-skin driven) ship as loose files at vanilla paths, no plugin.
- Group B creatures (Draugr, Falmer, Dragon Priest) get the minimal ESL because their
  body is armour-driven.
