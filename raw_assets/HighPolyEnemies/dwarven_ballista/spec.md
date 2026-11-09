# dwarven_ballista

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC02
- **Category:** automaton
- **Vanilla prefixes:** `actors\dlc02\dwarvenballistacenturion`
- **Reference files:** 3 NIFs, 655.1 KB
- **Notes:** Dragonborn.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc02\dwarvenballistacenturion\character assets\dwarvenballista.nif` | 434.4 KB | body - replace |
| `meshes\actors\dlc02\dwarvenballistacenturion\character assets\skeleton.nif` | 163.9 KB | skeleton / bind pose |
| `meshes\actors\dlc02\dwarvenballistacenturion\character assets\ballistacenturionparticles.nif` | 56.9 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\dwarven_ballista\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\dwarven_ballista\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\dlc02\dwarvenballistacenturion\character assets\skeleton.nif`
