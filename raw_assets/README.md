# Delivering models

Each creature has its own folder:

```
raw_assets/<Mod>/<creature>/
├─ incoming/     <- put the finished mesh here
└─ spec.md       <- what to replace, what not to touch, and the rules
```

The vanilla files are in `reference/<Mod>/<creature>/meshes/...`. They are read-only:
they are the size, bone and partition reference, not something to edit.

## The short version

1. Open the creature's vanilla body NIF in Blender (PyNifly is already installed).
2. Model the high-poly replacement over it, same silhouette and world scale.
3. Drop the mesh into that creature's `incoming/` folder.
4. Run `py src/scripts/02_check_incoming.py` to see what is still missing.

## What to deliver

| Item | Rule |
| --- | --- |
| Format | `.blend` preferred. `.fbx` or `.obj` accepted. |
| Scale | Same world scale and origin as the vanilla mesh. Do not rescale. |
| Orientation | Same as the vanilla import in Blender. |
| Shape name | Match the vanilla shape name from `bone_contract.md` (e.g. `WolfREDUCED`, `BearNew`). |
| UVs | Required, non-overlapping. |
| Rig | Not needed. Weights are transferred from the vanilla mesh. |
| Separate parts | Keep them separate. Do not merge eyes, masks, armor, hair or FX into the body. |
| Textures | 2K, in `incoming/textures/`. PNG or DDS. We convert and pack. |

## What not to deliver

- The vanilla skeleton or any `.hkx` file.
- Collision or ragdoll geometry. The vanilla NIF keeps its own.
- Added bones. The bone list in `bone_contract.md` is the complete allowed set.
- Engine props (projectiles, explosions, blood meshes, LODs, farskins).

## Why the shape name matters

The build retargets your mesh onto the vanilla shape. If the name does not match, the
script cannot tell which vanilla part you are replacing, and the build stops instead of
guessing.

## Checking the delivery

```powershell
py src/scripts/02_check_incoming.py
```

It prints one line per creature:

- `empty` - nothing delivered yet
- `2/4 - missing wolfblack, wolfred` - partial delivery
- `4/4 ready` - complete

## Priority order

The full scope is 71 creatures and 234 body meshes. Ship the iconic ones first:
wolf, bear, sabrecat, mammoth, troll, giant, dragon, draugr, falmer. That is what a
screenshot sells, and it lets the texture and packaging pipeline be proven before
scaling to every variant.
