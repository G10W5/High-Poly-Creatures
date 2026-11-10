# High-Poly Creature & Monster Overhaul

Two Nexus mods, one pipeline:

| Mod | Raw assets | Contents |
| --- | --- | --- |
| **High Poly Creatures** | `raw_assets/HighPolyCreatures` | Wildlife, farm animals, mounts: wolf, bear, sabrecat, mammoth, mudcrab, spider, netch, ... |
| **High Poly Enemies** | `raw_assets/HighPolyEnemies` | Monsters, undead, Dwemer, Falmer, dragons, DLC enemies |

Humanoid playable races are excluded on purpose. That is what keeps this mod 100% FaceGen-safe
and compatible with every NPC overhaul.

## Current state

- **71 creatures**, **431 vanilla NIFs**, **234 body meshes**
- Vanilla reference extracted from `Skyrim - Meshes0.bsa` (DLC included, under `actors\dlc01` / `actors\dlc02`)
- Mesh and bone contract generated for every creature
- PyNifly installed for standalone Python and for Blender 5.1 / 5.2
- **Wolf pilot built end to end**: `build/HighPolyCreatures/` + `dist/HighPolyCreatures-0.1.0.zip`

Vanilla totals: **919,573 vertices / 1,361,309 triangles** across the 234 body meshes.

Collision/ragdoll check: only 13 of the 431 reference NIFs carry `bhk` blocks and they are all
accessories (shield, spider butt, inventory explosions). Every creature's ragdoll lives in its
`skeleton.nif`, which the pipeline never touches — so re-exporting a body NIF cannot lose it.

## What I did

For every creature there is now:

```
raw_assets/<Mod>/<creature>/
├─ incoming/     <- drop the finished AAA model here
└─ spec.md       <- what to replace, what not to touch, and the rules

reference/<Mod>/<creature>/
├─ meshes/...            <- the vanilla NIFs (read-only)
└─ bone_contract.md      <- shape names, vert/tri/partition counts, texture slots, full bone list
```

## Commands

```powershell
py src/scripts/00_extract_vanilla.py   # rebuild reference/ from the vanilla BSA
py src/scripts/01_inventory.py         # probe every NIF and write bone_contract.md + nif_report.csv
py src/scripts/02_check_incoming.py    # per-creature delivery status
py src/scripts/03_build_textures.py    # PNG -> BC7 DDS into build/ (add --preset balanced|small)
py src/scripts/04_build_fomod.py       # zip build/ into dist/ with a FOMOD (add --list, --version)
py src/scripts/test_pipeline.py        # headless regression test of the Blender addon (wolf)
py src/scripts/verify_nif.py           # shapes / bones / partitions / textures of a built NIF
```

## Blender add-on: High Poly

`src/blender_addon/highpoly_pipeline.py` (copied into the Blender 5.1 and 5.2 addons folders)
adds a **View3D > N-panel > High Poly** tab. Pick a creature from `config/creatures.csv` and run
the steps, or hit **Run Full Pipeline**:

| Step | What it does |
| --- | --- |
| 1. Load Vanilla | imports the reference body NIF, tags body / fur / armature |
| 2. Import Model | drops the GLB/FBX/OBJ from `incoming/`, then **Auto Fit** (rotate, scale to vanilla bbox, optional per-axis silhouette match) and **Decimate** (multi-pass collapse to N tris) |
| 3. Transfer Weights | creates the vanilla bone groups, data-transfers weights, drops dead groups, limits to 4 influences |
| 4. Material | reuses the vanilla Skyrim shader nodes, points them at the AI diffuse and a generated normal+gloss map, writes 2K PNGs |
| 5. Fur shells | builds the FluffyWorks-style fur stack (see below) |
| 6. Export | hides the geometry being replaced, exports NIF + textures to `build/<Mod>/` at the vanilla path, saves a work `.blend` |

Settings: target tri budget (x vanilla), rotation, fit mode, texture size (1K/2K/4K),
fur shells (count / spacing / mesh detail), keep the vanilla fur shell, keep other
vanilla meshes.

### The bind pose

A replacement mesh has to be delivered in the vanilla mesh's **bind pose** - the
stance Skyrim's animation clips are authored against.  An AI model comes in
whatever stance the generator used (Skyrim's bear rears up on its hind legs,
an AI bear stands on all fours), and the per-axis fit then stretches it to
match a box that belongs to another pose.

**Auto Orient** (on by default) tries all 24 axis-aligned rotations and keeps
the one that puts the model's surface closest to the vanilla body, so a model
that arrives turned around or upside down still inherits the right bones.  The
status shows how well it lined up: `auto-oriented (0/-0/180, fit 1.7 units)`.

Every creature also has a reference render of its bind pose:

```
reference\HighPolyCreatures\bear\pose_side.png
```

Feed it to the image generator and ask for the same stance - then the fit
factors come out near 1 and nothing is distorted.  See `docs/POSE_WORKFLOW.md`.

### Fur shells (FluffyWorks style)

The fur is a stack of alpha-tested copies of the body, the same trick FluffyWorks
uses:

* every layer is the body pushed out along the vertex normals (`Shell spacing`,
  0.2 units = 2 mm per layer);
* every layer gets **its own alpha threshold** (15, 30, 45 …), so the inner
  layers keep the whole coat and the outer ones only the brightest strands -
  that taper is what makes it read as fur;
* the strand mask lives in the alpha channel of `<creature>_hp_shell.dds`, the
  coat colour in RGB, with no fur on the dark parts (eyes, nose).

The threshold is written by the exporter from the material's Skyrim shader node
group (`Alpha Property` ▸ `Alpha Threshold`) - the material's custom properties
are ignored, which is why every layer needs its own material. The
`DOUBLE_SIDED` flag has no Blender equivalent and is patched into the NIF
after the export.

## Tools installed

- `tools/pynifly/io_scene_nifly` — PyNifly 30.3.0. Usable from plain Python
  (`sys.path.insert(0, 'tools/pynifly/io_scene_nifly')`) and copied into the Blender 5.1 / 5.2
  addons folders.
- `bethesda-structs` — reads the vanilla BSA archives.
- `tools/texconv/texconv.exe` — Microsoft DirectXTex BC7/BC3 encoder (PNG -> DDS).

Blender workflow: `File > Import > Nif File (.nif)` now works, so the vanilla meshes in
`reference/` can be opened directly and modelled over.

## The three rules that matter

1. **Do not re-export the whole creature NIF.** Creature NIFs carry collision, ragdoll
   bodies, attach nodes and FX nodes. The new geometry gets transplanted into the vanilla
   NIF; everything else is preserved.
2. **Bone names and partition order are law.** Dismemberment, ragdoll and animations all
   break if the bone list or `NiSkinPartition` order changes.
3. **A `.nif` is not ready until it is weighted.** A bare high-poly mesh with no skin
   weights is unusable. `.blend` / `.fbx` / `.obj` is the preferred delivery; weights are
   transferred from the vanilla mesh.

## Folder map

```
config/creatures.csv   master list: mod, FOMOD page, creature, category, vanilla prefixes
reference/             extracted vanilla NIFs + contracts (generated, git-ignored)
raw_assets/            model deliveries + generated spec.md per creature
src/scripts/           pipeline scripts
src/fomod_template/    FOMOD scaffolding (built later)
tools/                 PyNifly (git-ignored)
build/                 assembled mod folders (generated)
dist/                  release archives (generated)
```

## Status

- [x] Project structure
- [x] Vanilla reference extracted for all 71 creatures
- [x] Per-creature specs, mesh stats and bone contracts
- [x] PyNifly toolchain working in Python and Blender
- [x] Blender N-panel add-on (`highpoly_pipeline.py`), tested headless on the wolf
- [x] Wolf pilot: GLB -> fit -> decimate -> weights -> material -> NIF -> DDS
- [x] Texture build (PNG -> BC7 DDS, full mips) and FOMOD packaging
- [x] FluffyWorks-style fur shells (alpha-tested layer stack, per-layer threshold)
- [x] Bind-pose reference renders for all 71 creatures (`docs/POSE_WORKFLOW.md`)
- [ ] In-game test of the wolf (install `build/HighPolyCreatures` into Data, spawn a wolf)
- [ ] Second colour variant / `wolf1..4` handling
- [ ] Remaining 70 creatures
