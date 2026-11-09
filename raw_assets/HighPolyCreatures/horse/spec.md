# horse

- **Mod:** High Poly Creatures
- **FOMOD page:** Farm_Ambient
- **Category:** wildlife
- **Vanilla prefixes:** `actors\horse\character assets`
- **Reference files:** 7 NIFs, 1.5 MB

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\horse\character assets\shadowmere.nif` | 431.3 KB | body - replace |
| `meshes\actors\horse\character assets\horse.nif` | 430.0 KB | body - replace |
| `meshes\actors\horse\character assets\imperialsaddle.nif` | 211.5 KB | body - replace |
| `meshes\actors\horse\character assets\saddle.nif` | 203.9 KB | body - replace |
| `meshes\actors\horse\character assets\harness.nif` | 185.9 KB | body - replace |
| `meshes\actors\horse\character assets\horsemane.nif` | 41.8 KB | body - replace |
| `meshes\actors\horse\character assets\skeleton.nif` | 21.9 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyCreatures\horse\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyCreatures\horse\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\horse\character assets\skeleton.nif`
