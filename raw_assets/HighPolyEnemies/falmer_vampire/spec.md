# falmer_vampire

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC01
- **Category:** monster
- **Vanilla prefixes:** `actors\dlc01\falmervampire`
- **Reference files:** 4 NIFs, 1.4 MB
- **Notes:** Dawnguard. Winged variants included.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc01\falmervampire\falmervampireferalwings.nif` | 475.6 KB | body - replace |
| `meshes\actors\dlc01\falmervampire\falmervampireferal.nif` | 449.6 KB | body - replace |
| `meshes\actors\dlc01\falmervampire\falmervampirewings.nif` | 285.8 KB | body - replace |
| `meshes\actors\dlc01\falmervampire\falmervampire.nif` | 259.8 KB | body - replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\falmer_vampire\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\falmer_vampire\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.
