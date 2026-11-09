# icewraith

- **Mod:** High Poly Enemies
- **FOMOD page:** Monsters
- **Category:** monster
- **Vanilla prefixes:** `actors\icewraith\character assets`
- **Reference files:** 6 NIFs, 947.2 KB

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\icewraith\character assets\icewraithsmokefins.nif` | 403.2 KB | body - replace |
| `meshes\actors\icewraith\character assets\icewraith.nif` | 363.2 KB | body - replace |
| `meshes\actors\icewraith\character assets\magicanomaly.nif` | 102.4 KB | FX / LOD / prop - do not replace |
| `meshes\actors\icewraith\character assets\fxicewraith2ndform.nif` | 54.8 KB | FX / LOD / prop - do not replace |
| `meshes\actors\icewraith\character assets\skeleton.nif` | 11.9 KB | skeleton / bind pose |
| `meshes\actors\icewraith\character assets\fxicewraithmultiparticles.nif` | 11.7 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\icewraith\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\icewraith\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\icewraith\character assets\skeleton.nif`
