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
| Wolf frozen in a T-pose or sliding without legs moving | weights/skinning broken |
| Body invisible, only the fur shell shows | mesh or NIF corrupt |
| Game crashes on spawn | NIF rejected — tell me and I will check the block layout |
| Fur pokes through the body in places | the shell base mesh is too coarse — raise `Shell tris` |
| Vanilla fluff shell floating off the body | `Keep vanilla fur shell` is on — turn it off (it is off by default; that shell was modelled for the vanilla body) |

## How the fur works

The fur is a stack of **8 alpha-tested shell layers** (`HP_Shell_L01` …
`HP_Shell_L08`), built the way FluffyWorks does it:

* each layer is a copy of the body, pushed out along the vertex normals
  (`Shell spacing`, 0.2 units = 2 mm per layer, so 1.6 units of fur in total),
* each layer has its **own alpha threshold** — 15, 30, 45 … 120 — so the inner
  layers keep almost the whole coat while the outer ones only keep the
  brightest strands. That taper is what makes it read as fur;
* the strand mask lives in the **alpha channel** of `wolf_hp_shell.dds`, with
  the coat colour in RGB, and dark parts of the coat (eyes, nose) get no fur.

Tuning in the add-on (N-panel ▸ *Fur shells*):

| Setting | Effect |
| --- | --- |
| `Fur shells` | number of layers (0 = no fur, max 16) |
| `Shell spacing` | distance between layers = fur length |
| `Shell tris` | how fine the shell base mesh is (higher = smoother, bigger file) |

## Rollback

Delete those seven files. The vanilla ones come back from the BSA on their own.
