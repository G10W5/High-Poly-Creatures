# dragonpriest

- **Mod:** High Poly Enemies
- **FOMOD page:** Undead
- **Category:** undead
- **Vanilla prefixes:** `actors\dragonpriest\character assets`
- **Reference files:** 19 NIFs, 1.4 MB
- **Notes:** Masks are separate meshes. Do not merge them into the body.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\dragonpriest\character assets\skeletonnecropriest.nif` | 598.3 KB | skeleton / bind pose |
| `meshes\actors\dragonpriest\character assets\dragon_priest.nif` | 418.5 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\fxdragonpriestlargeexplosion.nif` | 91.2 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dragonpriest\character assets\dragon_priestskinfx_mist.nif` | 54.7 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dragonpriest\character assets\fxdragonpriestsmallexplosion.nif` | 25.2 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dragonpriest\character assets\skeleton.nif` | 18.7 KB | skeleton / bind pose |
| `meshes\actors\dragonpriest\character assets\fxdragonpriestparticles01.nif` | 18.6 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dragonpriest\character assets\maskgreenstone.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskmoonstone.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskcorondrum.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskmarble.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskbronze.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskebony.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\masksteel.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskiron.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\maskwood.nif` | 17.6 KB | body - replace |
| `meshes\actors\dragonpriest\character assets\fxfallingsanddragonpriest01.nif` | 17.3 KB | FX / LOD / prop - do not replace |
| `meshes\actors\dragonpriest\character assets\fxskeletonnecropriesteyeglow.nif` | 15.4 KB | skeleton / bind pose |
| `meshes\actors\dragonpriest\character assets\fxdragonpreisteyeglow.nif` | 11.9 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\dragonpriest\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\dragonpriest\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\dragonpriest\character assets\skeletonnecropriest.nif`, `meshes\actors\dragonpriest\character assets\skeleton.nif`, `meshes\actors\dragonpriest\character assets\fxskeletonnecropriesteyeglow.nif`
