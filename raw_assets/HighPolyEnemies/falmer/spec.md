# falmer

- **Mod:** High Poly Enemies
- **FOMOD page:** Falmer
- **Category:** monster
- **Vanilla prefixes:** `actors\falmer\character assets`
- **Reference files:** 11 NIFs, 4.1 MB
- **Notes:** Body is armour-driven. Bone and weight transfer are critical here.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\falmer\character assets\falmer06.nif` | 592.0 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer05.nif` | 537.1 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer04.nif` | 498.5 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer02.nif` | 467.3 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer03.nif` | 460.0 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer_female_01.nif` | 430.1 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer01.nif` | 429.9 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer_male.nif` | 360.5 KB | body - replace |
| `meshes\actors\falmer\character assets\falmer_female.nif` | 346.9 KB | body - replace |
| `meshes\actors\falmer\character assets\helmet01.nif` | 43.7 KB | body - replace |
| `meshes\actors\falmer\character assets\skeleton.nif` | 20.0 KB | skeleton / bind pose |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\falmer\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\falmer\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.

Skeleton file(s) to weight against: `meshes\actors\falmer\character assets\skeleton.nif`
