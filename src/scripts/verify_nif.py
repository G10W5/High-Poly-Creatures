import sys
from pathlib import Path

sys.path.insert(0, r"tools\pynifly\io_scene_nifly")
from pyn.pynifly import NifFile  # noqa: E402

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"build\HighPolyCreatures\meshes\actors\canine\character assets wolf\wolf.nif")

n = NifFile(str(root))
print(f"=== {root} ===")
for s in n.shapes:
    bones = [b for b in s.bone_names] if hasattr(s, "bone_names") else []
    print(f"SHAPE {s.name!r} verts={len(s.verts)} tris={len(s.tris)} bones={len(bones)}")
    try:
        print("   textures:", {k: v for k, v in s.shader.textures.items() if v})
    except Exception as e:
        print("   textures err", e)
    try:
        sf = s.shader.properties
        print("   flags: shaderflags1=0x%X shaderflags2=0x%X" % (sf.shaderflags1, sf.shaderflags2))
    except Exception as e:
        print("   flags err", e)
    if bones:
        print("   bones:", ", ".join(bones))

print("NODES:", [x for x in n.nodes][:8], "... total", len(list(n.nodes)))
n.close()

texdir = Path(r"raw_assets\HighPolyCreatures\wolf\incoming\textures\actors\wolf")
for p in sorted(texdir.glob("*.png")):
    print(f"TEXTURE {p.name} {p.stat().st_size:,} bytes")

# also confirm the image headers
try:
    from PIL import Image
    for p in sorted(texdir.glob("*.png")):
        with Image.open(p) as im:
            print("   ", p.name, im.size, im.mode)
except ImportError:
    print("PIL not available")
