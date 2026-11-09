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
```

Your game is at:
`C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data`

Nothing else is touched — no skeleton, no animation, no plugin, no ESP/ESL.

## Option B — the archive

`dist\HighPolyCreatures-0.1.0.zip` (14.3 MB) has the same files plus a FOMOD.
Install it with your mod manager if you have one; the FOMOD asks page by page
(Beasts, Farm_Ambient, DLC01, DLC02) so Dawnguard/Dragonborn content is opt-in.

## Before you test

Other wolf replacers will fight this one. Loose files beat the vanilla BSA, but if
another mod ships *loose* wolf meshes, whichever is higher in your load order wins.
For a clean test, temporarily disable anything else that touches wolves
(`actors\canine\...` or `textures\actors\wolf\...`).

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
| Purple or black body | texture path wrong |
| Wolf frozen in a T-pose or sliding without legs moving | weights/skinning broken |
| Body invisible, only the fluff shell shows | mesh or NIF corrupt |
| Game crashes on spawn | NIF rejected — tell me and I will check the block layout |
| Fur shell pokes through the body in places | the vanilla shell does not match the new silhouette — expected, we decide then whether to keep it |

## Rollback

Delete those six files. The vanilla ones come back from the BSA on their own.
