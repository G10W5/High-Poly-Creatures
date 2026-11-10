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
| 2. Import Model | drops the GLB/FBX/OBJ from `incoming/`, then **Auto Orient** (picks the rotation that lines the model up with the vanilla body) and **Decimate** (multi-pass collapse to N tris) |
| 3. Transfer Weights | creates the vanilla bone groups, data-transfers weights, drops dead groups, limits to 4 influences |
| 4. Surface | relaxes the decimated mesh and shades it smooth - **no extra triangles** |
| 5. Material | reuses the vanilla Skyrim shader nodes, points them at the AI diffuse and a generated normal+gloss map, writes 2K PNGs |
| 6. Fur shells | builds the FluffyWorks-style fur stack (see below) |
| 7. Export | hides the geometry being replaced, exports NIF + textures to `build/<Mod>/` at the vanilla path, saves a work `.blend` |

Settings: target tri budget (x vanilla), rotation, fit mode, texture size (1K/2K/4K),
surface smoothing, fur shells (count / spacing / mesh detail), keep the vanilla fur
shell, keep other vanilla meshes.

### Smoother without more polygons

Decimating a 500k-triangle AI model down to the Skyrim budget leaves hard
facets - and the AI sculpts model their fur as thousands of thin shards that
survive the decimation and show up as plates.  Three things fix that:

* **Target x Vanilla** (default 4) - a *lower* budget collapses the shards
  away.  More triangles means more shards, not more detail;
* **Smooth** (a light Laplacian pass) relaxes what is left;
* **Shade smooth** averages the normals across the faces, so the body shades
  as one continuous surface instead of a mosaic of flat triangles.  The NIF
  stores the normals, so this is free.

None of them costs a triangle.  **Remesh** (voxel) cleans the geometry up
completely, but the UVs then have to be copied over by nearest point, which
smears the texture - so it is off by default.

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

### Fur

**Baked shell layers (default)** - a stack of alpha-tested copies of the body,
each pushed a bit further out, with a **strand mask** in the alpha channel of
`<creature>_shell.dds`.  The mask is fine and dense (tiny strands, combed
along the model's own coat), and every layer gets its **own alpha threshold**
so the inner layers keep the whole coat while the outer ones only keep the
brightest strands.  That taper is what makes it read as a soft coat instead of
a painted-on texture.  No add-ons needed - same as FluffyWorks.

| Setting | Effect |
| --- | --- |
| `Fur shells` | number of layers (5 by default, max 16) |
| `Shell spacing` | distance between layers = fur length (0.4 = 4 mm) |
| `Shell gap` | how far the first layer sits above the body |
| `Shell tris` | how dense the layers are (0 = as dense as the body) |

The layers **have to be as dense as the body** to hug it: a layer that is
coarser cuts across the body and shows up as flat plates.  Five layers of a
20k triangle wolf is 14 MB of NIF - so `Fur shells = 0` (body only, 2.4 MB)
stays a choice, and a lower `Target x Vanilla` makes everything cheaper.

The thresholds are spread over the layers rather than fixed, so fewer layers
still taper the same way (three layers get 40/80/120, five get 24/48/72/96/120).

**`_shell.dds` for Open Shaders / Bottled Shaders (optional)** - the same
texture is what their *Fur Shells* feature looks for, and that shader draws
the layers itself:

> *"Draws layered fur ... from the `_shell.dds` textures ... No fur meshes
> needed ... Length, density and droop can be changed ... Mod authors can add
> fur to anything by putting a `_shell.dds` next to its texture."*

With Open Shaders installed: set `Fur shells = 0` and keep only the body and
the texture - the shader generates the fur, with **inertia, wind, wet fur in
the rain** and in-game sliders, at ~2.4 MB instead of 14 MB.  The mod ships
the texture either way, so both routes are covered.

**Hair cards (off by default)** - real strand geometry: small tapered quads
standing off the skin, weighted to the body's bones and double sided so they
are visible from every angle.  Cheaper than the layers, but reads as *spiky
bristles* rather than a soft coat.  Set the CSV `fur` column to `cards` for a
creature that should get these.

## Tools installed

- `tools/pynifly/io_scene_nifly` — PyNifly 30.3.0. Usable from plain Python
  (`sys.path.insert(0, 'tools/pynifly/io_scene_nifly')`) and copied into the Blender 5.1 / 5.2
  addons folders.
- `bethesda-structs` — reads the vanilla BSA archives.
- `tools/texconv/texconv.exe` — Microsoft DirectXTex BC7/BC3 encoder (PNG -> DDS).

Blender workflow: `File > Import > Nif File (.nif)` now works, so the vanilla meshes in
`reference/` can be opened directly and modelled over.

## Asset provenance (Nexus rules)

Every texture this project ships is **generated from the AI models delivered
in `raw_assets/`**:

- `wolf_d.dds`, `wolf_n.dds` — converted from the model's own diffuse and
  normal (texconv, PNG → BC7);
- `<creature>_shell.dds` — **generated** by `_make_shell_image()`: the coat
  colour copied from the model's diffuse, plus a procedural strand mask whose
  flow comes from that same diffuse.

Nothing is taken from another mod. Shell texturing is a *technique*, not an
asset, and using the technique (or the `_shell.dds` naming convention, which
Fur Shader Armors and the Shaders plugins also use) is fine; shipping
FluffyWorks' or anyone else's DDS files is not, and we do not.

Two things to keep watching:

1. **Do not use another mod's screenshots as the AI model's reference image.**
   A model generated from a photo of someone else's fur can be a derivative
   work. The `reference/<mod>/<creature>/pose_side.png` renders come from the
   vanilla game files, which is the normal, allowed basis for a replacer.
2. The vanilla `_sk.dds` lighting map is deliberately *not* replaced - we keep
   the game's own file untouched rather than shipping a copy.

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
