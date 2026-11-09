# dragon_dlc02

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC02
- **Category:** dragon
- **Vanilla prefixes:** `actors\dlc02\dragon`
- **Reference files:** 6 NIFs, 2.8 MB
- **Notes:** Dragonborn. Black variant.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc02\dragon\dragon_blackvariant.nif` | 958.1 KB | body - replace |
| `meshes\actors\dlc02\dragon\dragon_blackvarianttailbloodmesh.nif` | 550.4 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc02\dragon\dragon_blackvariantwingrbloodmesh.nif` | 480.6 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc02\dragon\dragon_blackvariantwinglbloodmesh.nif` | 480.3 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc02\dragon\dragon_blackvariantheadbloodmesh.nif` | 309.2 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc02\dragon\dragon_blackvariantlod.nif` | 71.5 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\dragon_dlc02\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\dragon_dlc02\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.
