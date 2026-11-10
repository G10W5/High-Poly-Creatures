# Wolf pilot — manual install & in-game test

Everything you need is already built. Two ways to install, pick one.

## Option A — loose files (simplest for a test)

Copy the **contents** of this folder:

```
C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures\build\HighPolyCreatures\
```

into your Skyrim data folder, so you end up with:

```
<Data>\meshes\actors\canine\character assets wolf\wolf.nif
<Data>\meshes\actors\canine\character assets wolf\wolfblack.nif
<Data>\meshes\actors\canine\character assets wolf\wolffire.nif
<Data>\meshes\actors\canine\character assets wolf\wolfred.nif
<Data>\textures\actors\wolf\wolf_d.dds
<Data>\textures\actors\wolf\wolf_n.dds
<Data>\textures\actors\wolf\wolf_hp_shell.dds
```

Your game is at:
`C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data`

> **All three textures are required.** Without `wolf_d.dds` the engine has no
> diffuse to load and falls back to a flat default material — that is what makes
> an untextured wolf look purple/lavender. If the wolf is a flat colour, the
> textures are missing, not broken.

Nothing else is touched — no skeleton, no animation, no plugin, no ESP/ESL.

## Option B — the archive

`dist\HighPolyCreatures-1.0.0.zip` (32.8 MB) has the same files plus a FOMOD.
Install it with your mod manager if you have one; the FOMOD asks page by page
(Beasts, Farm_Ambient, DLC01, DLC02) so Dawnguard/Dragonborn content is opt-in.

> If your mod manager is Vortex: it will want to own those files, and it will
> overwrite hand-copied ones on the next deploy. Use the archive for a test
> that has to survive.

## Before you test

Other wolf replacers will fight this one. Loose files beat the vanilla BSA, but if
another mod ships *loose* wolf meshes, whichever is higher in your load order wins.
For a clean test, temporarily disable anything else that touches wolves
(`actors\canine\...` or `textures\actors\wolf\...`).

**FluffyWorks** in particular replaces the wolf NIFs *and* ships
`textures\actors\wolf\wolf_shell.dds`. Our fur texture is called
`wolf_hp_shell.dds` so the two never fight over the same file, but FluffyWorks'
own wolf NIFs will still replace ours — disable FluffyWorks for the test.

## In game

1. Load a save, open the console with `~`.
2. `help "wolf" 4` — look for the base id of a **WOLF** entry (8 hex digits).
3. `player.placeatme <that id>` — spawn one, or just walk into the wilderness
   around Whiterun at night where wolves spawn.
4. Also check the black/red/fire variants if you can: they all use the same
   high-poly mesh now (they lost their colour differences — tinting is a to-do).

## What to look for

| Symptom | Meaning |
| --- | --- |
| Wolf looks high poly, fur detail crisp, walks/runs/attacks normally | success |
| Purple or black body | the diffuse texture is missing from `<Data>\textures\actors\wolf\` |
| Fur looks like a fuzzy halo around a smooth body | the shell layers are there but the strand mask is too sparse — lower `Shell spacing` or raise `Fur shells` |
| Flat shards poking out of the body | the shell layers do not hug the body — they are wrapped on now, so this means an old build |
| Wolf frozen in a T-pose or sliding without legs moving | weights/skinning broken |
| Body invisible, only the fur shell shows | mesh or NIF corrupt |
| Game crashes on spawn | NIF rejected — tell me and I will check the block layout |
| Surface looks faceted / spiky | lower `Target x Vanilla` (the fur shards go away) and raise `Smooth` a little |
| Flat plates on the body | the AI model's own fur geometry - lower `Target x Vanilla`; `Remesh` fixes it but smears the texture |
| Vanilla fluff shell floating off the body | `Keep vanilla fur shell` is on — turn it off (it is off by default; that shell was modelled for the vanilla body) |

## Smoother without more triangles

The *Surface* section has three knobs that cost no triangles:

| Setting | Effect |
| --- | --- |
| `Target x Vanilla` | the tri budget - a **lower** one collapses the AI model's fur shards away, more triangles keeps them |
| `Smooth` | relaxes the decimated mesh; too much and the shards collapse into holes |
| `Shade smooth` | averages the normals across the faces so the body shades as one surface instead of flat triangles |

`Remesh` rebuilds the mesh as a clean voxel surface (which fixes the shards
completely) but the UVs have to be copied over by nearest point afterwards,
which smears the texture - so it is off by default.

## How the fur works

There are two ways to put fur on the wolf, and the default is the first one.

**Hair cards** (default, 12000 strands) - every strand is a small tapered quad
standing off the skin, rooted on a vertex of the body and weighted to the same
bones, so it follows the animation.  This is what makes the fur read as fur:
the strands are *in the silhouette*, not painted on it.  The fur shape is made
double sided after the export - without that the flat cards would only be
visible from one side.

| Setting | Effect |
| --- | --- |
| `Fur strands` | how many cards (two triangles each) |
| `Fur length` | how far they stand off the skin (1.8 = 1.8 cm) |
| `Fur width` | the width of a strand at its root |
| `Fur lay` | 0 = straight out, 1 = lying back along the body |

**Fur shells** (FluffyWorks' technique, off by default) - a stack of
alpha-tested copies of the body, each pushed further out, with a strand mask in
the alpha channel of `wolf_hp_shell.dds`.  It gives a soft coat, but on a high
poly body it is expensive: a layer has to be as dense as the body to hug it,
so five layers of a 20k triangle wolf cost 12 MB of NIF.  Hair cards give the
same read for about a megabyte.

If the shells are on:

| Setting | Effect |
| --- | --- |
| `Fur shells` | number of layers (0 = off, max 16) |
| `Shell spacing` | distance between layers = fur length |
| `Shell tris` | 0 = same density as the body, which is what the layers need to hug it |

Each layer gets its **own alpha threshold** — 15, 30, 45 … — so the inner
layers keep the whole coat while the outer ones only keep the brightest
strands.  That taper is what makes it read as fur.

## Smoother without more triangles

The *Surface* section has two knobs that cost no triangles:

| Setting | Effect |
| --- | --- |
| `Smooth` | relaxes the decimated mesh (Laplacian), the surface goes soft and the normal map brings the detail back |
| `Shade smooth` | averages the normals across the faces so the body shades as one surface instead of flat triangles |

If it still looks too soft, raise *Target x Vanilla* — that is the only knob
that really buys geometry.

## Rollback

Delete those seven files. The vanilla ones come back from the BSA on their own.
