# soulcairn_horse

- **Mod:** High Poly Creatures
- **FOMOD page:** DLC01
- **Category:** wildlife
- **Vanilla prefixes:** `actors\dlc01\horse`
- **Reference files:** 3 NIFs, 594.1 KB
- **Notes:** Dawnguard. Soul Cairn horse / Arvak (horsebone).

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc01\horse\character assets\soulcairnhorsebone.nif` | 309.8 KB | body - replace |
| `meshes\actors\dlc01\horse\character assets\horsebone.nif` | 275.5 KB | body - replace |
| `meshes\actors\dlc01\horse\character assets\jamshadowmerefx.nif` | 8.8 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyCreatures\soulcairn_horse\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyCreatures\soulcairn_horse\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.
