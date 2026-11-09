# dragon_dlc01

- **Mod:** High Poly Enemies
- **FOMOD page:** DLC01
- **Category:** dragon
- **Vanilla prefixes:** `actors\dlc01\dragon`
- **Reference files:** 12 NIFs, 3.2 MB
- **Notes:** Dawnguard. Purple and ice-lake variants.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dlc01\dragon\dragon_icelake.nif` | 901.9 KB | body - replace |
| `meshes\actors\dlc01\dragon\dragon_purple.nif` | 853.7 KB | body - replace |
| `meshes\actors\dlc01\dragon\dragonpurplebloodhead.nif` | 345.6 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_icelakebloodhead.nif` | 314.0 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_icelakebloodtail.nif` | 177.9 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragonpurplebloodwingtail.nif` | 130.3 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragonpurplebloodwingl.nif` | 107.9 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragonpurplebloodwingr.nif` | 105.0 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_icelakebloodwingl.nif` | 92.9 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_icelakebloodwingr.nif` | 92.6 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_icelakelod.nif` | 88.1 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dlc01\dragon\dragon_purplelod.nif` | 75.2 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\dragon_dlc01\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\dragon_dlc01\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.
