# draugr

- **Mod:** High Poly Enemies
- **FOMOD page:** Undead
- **Category:** undead
- **Vanilla prefixes:** `actors\draugr\character assets`
- **Reference files:** 45 NIFs, 11.7 MB
- **Notes:** Includes skeleton and boneman/wrathman variants. Dismemberment partitions matter.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonwarrior.nif` | 737.1 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\dlc01\skeletonwarrior.nif` | 736.8 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\draugrmale07.nif` | 713.5 KB | body - replace |
| `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnboneman.nif` | 700.4 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale04.nif` | 638.5 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale06.nif` | 628.2 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale05.nif` | 611.8 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale03.nif` | 576.9 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrskeleton.nif` | 502.5 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\skeletonnecroimperialskin.nif` | 499.5 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\skeletonnecrostormcloakskin.nif` | 474.3 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\hevarmorf_2.nif` | 458.5 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale02.nif` | 452.0 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmagicfemale01.nif` | 413.0 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonnecroskin.nif` | 408.0 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\skeletonnecroskin.nif` | 407.8 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\draugrmale01.nif` | 399.1 KB | body - replace |
| `meshes\actors\draugr\character assets\hevarmorf_1.nif` | 358.6 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrmale.nif` | 352.1 KB | body - replace |
| `meshes\actors\draugr\character assets\midarmorf.nif` | 331.2 KB | body - replace |
| `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonnecroskin02.nif` | 297.5 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\lightarmorf.nif` | 293.3 KB | body - replace |
| `meshes\actors\draugr\character assets\draugrfemale.nif` | 251.3 KB | body - replace |
| `meshes\actors\draugr\character assets\hairf01.nif` | 74.7 KB | body - replace |
| `meshes\actors\draugr\character assets\hair02.nif` | 63.2 KB | body - replace |
| `meshes\actors\draugr\character assets\hairf02.nif` | 57.3 KB | body - replace |
| `meshes\actors\draugr\character assets\dlc01\dlcfxkeeperheadeyeswirls_withhorns.nif` | 55.8 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\beard02.nif` | 46.2 KB | body - replace |
| `meshes\actors\draugr\character assets\skeletonf.nif` | 45.7 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\skeleton.nif` | 45.5 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\beard01.nif` | 44.3 KB | body - replace |
| `meshes\actors\draugr\character assets\helmetf02.nif` | 43.8 KB | body - replace |
| `meshes\actors\draugr\character assets\helmet03.nif` | 32.3 KB | body - replace |
| `meshes\actors\draugr\character assets\helmet02.nif` | 30.2 KB | body - replace |
| `meshes\actors\draugr\character assets\skeletons.nif` | 24.1 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\helmet01.nif` | 24.1 KB | body - replace |
| `meshes\actors\draugr\character assets\helmetf01.nif` | 24.1 KB | body - replace |
| `meshes\actors\draugr\character assets\dlc01\dlcfxkeeperheadeyeswirls.nif` | 20.4 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\hair01.nif` | 20.2 KB | body - replace |
| `meshes\actors\draugr\character assets\dlc01\fxdlc1sckeeperparticleattach.nif` | 17.0 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\fxskeletonnecroeyeglow.nif` | 15.4 KB | skeleton / bind pose |
| `meshes\actors\draugr\character assets\dlc01\fxdlcsoulcairnshadeeyes.nif` | 13.4 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\fxdraugrfemaleeyes.nif` | 11.9 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\fxdraugrmaleeyes.nif` | 11.9 KB | FX / LOD / prop - do not replace |
| `meshes\actors\draugr\character assets\fxmagicdraugrdarkening.nif` | 2.8 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\draugr\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\draugr\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\draugr\character assets\skeletonnecroskin.nif`, `meshes\actors\draugr\character assets\skeletonnecrostormcloakskin.nif`, `meshes\actors\draugr\character assets\skeletonf.nif`, `meshes\actors\draugr\character assets\skeletons.nif`, `meshes\actors\draugr\character assets\skeleton.nif`, `meshes\actors\draugr\character assets\fxskeletonnecroeyeglow.nif`, `meshes\actors\draugr\character assets\skeletonnecroimperialskin.nif`, `meshes\actors\draugr\character assets\draugrskeleton.nif`, `meshes\actors\draugr\character assets\dlc01\skeletonwarrior.nif`, `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonnecroskin.nif`, `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonwarrior.nif`, `meshes\actors\draugr\character assets\dlc01\dlc1soulcairnskeletonnecroskin02.nif`
