# werewolfbeast

- **Mod:** High Poly Enemies
- **FOMOD page:** Monsters
- **Category:** monster
- **Vanilla prefixes:** `actors\werewolfbeast\character assets`, `actors\werewolf\character assets\skeleton.nif`
- **Reference files:** 6 NIFs, 973.1 KB
- **Notes:** Player werewolf. Body and head are separate meshes; skeleton lives in actors\werewolf.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\werewolfbeast\character assets\malebodywerewolf_1.nif` | 676.5 KB | body - replace |
| `meshes\actors\werewolfbeast\character assets\maleheadwerewolff.nif` | 157.6 KB | body - replace |
| `meshes\actors\werewolfbeast\character assets\mouth\mouthmalebeastwerewolf.nif` | 71.7 KB | body - replace |
| `meshes\actors\werewolf\character assets\skeleton.nif` | 30.4 KB | skeleton / bind pose |
| `meshes\actors\werewolfbeast\character assets\skeleton.nif` | 29.0 KB | skeleton / bind pose |
| `meshes\actors\werewolfbeast\character assets\eyesmalewerewolfbeast.nif` | 7.9 KB | body - replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\werewolfbeast\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\werewolfbeast\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\werewolfbeast\character assets\skeleton.nif`, `meshes\actors\werewolf\character assets\skeleton.nif`
