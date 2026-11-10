# The bind pose — why a model has to match the vanilla's stance

## The rule

**A creature's replacement mesh has to be delivered in the vanilla mesh's bind
pose.** Not "close to it" — the same pose.

Skyrim's animation clips are authored against the bind pose of the mesh that
ships with the game. The engine applies bone transforms relative to that pose,
so a mesh in a different stance gets deformed by an animation that expects the
vanilla stance: the legs land in the wrong place, the back bends the wrong way,
and the creature ends up stretched or rubbery.

The pose references show this clearly:

| creature | vanilla bind pose |
| --- | --- |
| wolf | standing, side profile, tail level |
| bear | **rearing up on its hind legs**, front paws raised, claws out |
| mammoth | standing, trunk down |

## Why the bear looked stretched

The pipeline fits a model to the vanilla body by matching the bounding box per
axis. That only works if both are in the same pose. For the bear:

```
fit: scale 173.90, axis-fit 0.839 / 1.781 / 1.745
```

The AI bear had to be stretched **1.78× lengthwise and 1.75× vertically** to
fill a box that belongs to a *rearing* bear. That is the "stretched" you saw -
the fit was trying to reconcile two different stances, and it loses.

The add-on now warns about exactly this: when the per-axis fit factors differ
by more than about 25 %, the status says the model's proportions differ from
the vanilla's and its pose is probably wrong.

## What to do about it

### 1. Generate the model in the right pose

Every creature has a reference render:

```
reference\HighPolyCreatures\bear\pose_side.png
reference\HighPolyCreatures\wolf\pose_side.png
reference\HighPolyEnemies\<creature>\pose_side.png
```

These are the vanilla bind poses, side on, on a plain background. Feed the
image to your generator and ask for the same stance, e.g.:

> *a high-poly Skyrim bear, standing on its hind legs, front paws raised,
> side view, matching the reference image*

Then the model needs no pose fixing at all, and the fit factors come out even
(the wolf: 0.875 / 1.000 / 0.930 - close to 1, so almost no distortion).

Regenerate them with:

```
blender --background --python src\scripts\05_render_pose_reference.py
```

### 2. Use the "Keep model proportions" fit

If you want to use a model whose pose does not match anyway, switch **Fit** to
*Keep model proportions* (uniform scale). The creature will keep its own
proportions and will not be squashed - it will simply animate a bit off, which
looks far better than a stretched one.

### 3. What does *not* work

An automatic pose warp was implemented and thrown away again: a quadrupedal
model cannot be morphed into a rearing one without tearing the mesh (the front
legs have to become arms), and even for a matching pose the surface
registration tore the fur. Re-posing is a job for the model, not for the
pipeline - hence the reference renders.
