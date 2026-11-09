# boar_riekling

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC02
- **Category:** monster
- **Vanilla prefixes:** `actors\dlc02\boarriekling`
- **Reference files:** 11 NIFs, 7.6 MB
- **Notes:** Dragonborn. Bristleback mount plus rider.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variantb.nif` | 998.3 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variantg.nif` | 996.7 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling.nif` | 960.3 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variantc.nif` | 960.3 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_varianta.nif` | 923.6 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variantf.nif` | 904.7 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variante.nif` | 883.8 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boarriekling_variantd.nif` | 877.8 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\boar.nif` | 263.1 KB | body - replace |
| `meshes\actors\dlc02\boarriekling\character assets\skeletonboar.nif` | 24.4 KB | skeleton / bind pose |
| `meshes\actors\dlc02\boarriekling\character assets\skeleton.nif` | 24.4 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\boar_riekling\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\boar_riekling\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\dlc02\boarriekling\character assets\skeletonboar.nif`, `meshes\actors\dlc02\boarriekling\character assets\skeleton.nif`
