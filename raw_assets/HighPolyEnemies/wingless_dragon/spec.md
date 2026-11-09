# wingless_dragon

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC02
- **Category:** dragon
- **Vanilla prefixes:** `actors\dlc02\winglessdragon`
- **Reference files:** 2 NIFs, 783.8 KB
- **Notes:** Dragonborn.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc02\winglessdragon\characterassets\winglessdragon.nif` | 759.9 KB | body - replace |
| `meshes\actors\dlc02\winglessdragon\characterassets\skeleton.nif` | 23.9 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\wingless_dragon\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\wingless_dragon\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\dlc02\winglessdragon\characterassets\skeleton.nif`
