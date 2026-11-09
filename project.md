# GOAL.md - High-Poly Creature & Monster Overhaul AIO (Non-NPC)

## Objective
Develop a high-poly visual overhaul strictly for Skyrim SE/AE Creatures, Wild Animals, Monsters, and Falmer. Human/Mer playable race NPCs are intentionally excluded to maintain 100% facegen and NPC overhaul compatibility.

---

## Target Asset Scope
- **Wild Beasts:** Wolves, Bears, Sabre Cats, Mammoths, Mudcrabs, Spiders, etc.
- **Monsters & Daedra:** Trolls, Giants, Spriggans, Hagravens, Atronachs, Dragons.
- **Undead & Automata:** Draugr, Skeletons, Dragon Priests, Dwarven Machinery.
- **Falmer:** All Falmer variants (treated as creature actor rigs).
- **EXCLUDED:** Human/Elf/Orc/Beast-race playable NPCs, guards, bandits, and human armor sets.

---

## Workflow Division of Labor

### Human Author (Your Responsibilities)
- Model high-poly 3D geometry matching vanilla creature bounding scales.
- Transfer vanilla bone weights via Blender (`Transfer Data` modifier) or Outfit Studio.
- Export clean `.nif` creature meshes and generate 2K/4K PBR texture sets (`_n.dds`, `_msn.dds`, `_p.dds`).

### AI Agent (Automation Responsibilities)
- Process incoming high-poly `.nif` files in `/raw_assets` and update internal block strings/texture paths.
- Generate light-master (`.esl`) or ESL-flagged (`.esp`) plugins using Spriggit CLI.
- Map updated high-poly meshes to vanilla creature `ArmorAddon` and `Race` visual records without modifying base gameplay stats.
- Construct directory structures and compile a modular FOMOD installer (`ModuleConfig.xml`).

---

## Project Structure

```text
/skyrim-creatures-highpoly
│── /raw_assets
│   ├── /beasts         # Wolves, Bears, Mammoths, etc.
│   ├── /monsters       # Trolls, Giants, Falmer, Spiders, Dragons
│   └── /undead_dwemer  # Draugr, Skeletons, Dwarven Automatons
│── /build
│   ├── /Pack1_Beasts   # Production asset structure for Beasts
│   ├── /Pack2_Monsters # Production asset structure for Monsters & Falmer
│   └── /Pack3_AIO      # Combined directory for AIO release
│── /src
│   ├── /yaml_records   # Decompiled plugin records for Spriggit compilation
│   └── /fomod_template # FOMOD structure and XML templates
└── GOAL.md