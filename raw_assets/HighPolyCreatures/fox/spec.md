# fox

- **Mod:** High Poly Creatures
- **FOMOD page:** Farm_Ambient
- **Category:** wildlife
- **Vanilla prefixes:** `actors\wolf\fox*.nif`, `actors\wolf\character assets\skeleton.nif`
- **Reference files:** 3 NIFs, 213.2 KB
- **Notes:** Fox reuses the wolf rig. Only the fox meshes and its skeleton belong here.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\wolf\foxarctic.nif` | 91.4 KB | body - replace |
| `meshes\actors\wolf\fox.nif` | 91.4 KB | body - replace |
| `meshes\actors\wolf\character assets\skeleton.nif` | 30.4 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyCreatures\fox\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyCreatures\fox\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\wolf\character assets\skeleton.nif`
