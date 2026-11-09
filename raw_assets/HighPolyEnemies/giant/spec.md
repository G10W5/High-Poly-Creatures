# giant

- **Mod:** High Poly Enemies
- **FOMOD page:** Monsters
- **Category:** monster
- **Vanilla prefixes:** `actors\giant\character assets`
- **Reference files:** 4 NIFs, 1.8 MB
- **Notes:** Uses a club as a separate mesh.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\giant\character assets\giant02.nif` | 753.5 KB | body - replace |
| `meshes\actors\giant\character assets\giant01.nif` | 656.1 KB | body - replace |
| `meshes\actors\giant\character assets\giant.nif` | 445.4 KB | body - replace |
| `meshes\actors\giant\character assets\skeleton.nif` | 19.6 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\giant\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\giant\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\giant\character assets\skeleton.nif`
