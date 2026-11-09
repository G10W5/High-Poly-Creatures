# alduin

- **Mod:** High Poly Enemies
- **FOMOD page:** Dragons
- **Category:** dragon
- **Vanilla prefixes:** `actors\alduin`
- **Reference files:** 2 NIFs, 1.1 MB
- **Notes:** Alduin is a separate mesh. Highest rig risk in the project.

## Files

| Vanilla file | Size | Role |
| --- | --- | --- |
| `meshes\actors\alduin\alduin.nif` | 954.6 KB | body - replace |
| `meshes\actors\alduin\farskin_alduin.nif` | 178.0 KB | FX / LOD / prop - do not replace |

## Contract (non-negotiable)

Full mesh stats and the exact bone list: `reference\HighPolyEnemies\alduin\bone_contract.md`

1. Keep the exact vanilla bone names. No added bones, no removed bones.
2. Maximum 4 bone influences per vertex.
3. Maximum ~65,500 vertices per skin partition (16-bit indices).
4. Keep the vanilla `NiSkinPartition` order - dismemberment depends on it.
5. Do not re-export the whole NIF. The finished geometry is transplanted into the
   vanilla NIF so collision, ragdoll bodies, attach nodes and FX nodes survive.
6. Bounding sphere / box must be recomputed after the transplant.

## Deliverable

Drop the finished model in `C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\raw_assets\HighPolyEnemies\alduin\incoming`.

Use the same base name as the mesh it replaces (e.g. `wolf.nif`, `bear.nif`).
A `.blend`, `.fbx` or `.obj` is fine - the geometry is retargeted to the vanilla
skeleton during the build. If you deliver a finished `.nif`, it must already be
weighted to the correct vanilla skeleton.
