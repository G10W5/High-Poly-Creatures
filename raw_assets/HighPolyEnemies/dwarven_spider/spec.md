# dwarven_spider

- **Mod:** High Poly Enemies
- **FOMOD page:** Dwemer
- **Category:** automaton
- **Vanilla prefixes:** `actors\dwarvenspider\character assets`
- **Reference files:** 6 NIFs, 807.8 KB

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dwarvenspider\character assets\dwarvenspidernoeye.nif` | 269.0 KB | body - replace |
| `meshes\actors\dwarvenspider\character assets\dwarvenspidercenturion.nif` | 236.7 KB | body - replace |
| `meshes\actors\dwarvenspider\character assets\dwarvenspidernofx.nif` | 236.7 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dwarvenspider\character assets\dwarvenspidercenturionskinedsteam.nif` | 39.1 KB | body - replace |
| `meshes\actors\dwarvenspider\character assets\skeleton.nif` | 19.5 KB | skeleton / bind pose |
| `meshes\actors\dwarvenspider\character assets\dwarvenspidercenturionfx.nif` | 6.8 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\dwarven_spider\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\dwarven_spider\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\dwarvenspider\character assets\skeleton.nif`
