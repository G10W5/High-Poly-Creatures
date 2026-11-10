bl_info = {
    "name": "High Poly Creature Pipeline",
    "author": "High Poly Creature Overhaul",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar (N) > High Poly",
    "description": "Turn an AI-generated GLB into a Skyrim SE creature NIF",
    "category": "Object",
}

import bpy
import csv
import functools
import math
import os
import re
from dataclasses import dataclass
import mathutils
from mathutils import Vector
from pathlib import Path

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

DEFAULT_PROJECT = r"C:\Users\Uporabnik\Desktop\Skyrim-HighPoly-Creatures"
MOD_FOLDERS = {"Creatures": "HighPolyCreatures", "Enemies": "HighPolyEnemies"}
MOD_NAMES = {"Creatures": "High Poly Creatures", "Enemies": "High Poly Enemies"}

NON_BODY = (
    "skeleton", "fx", "farskin", "lod", "particles", "projectile", "explosion",
    "blood", "attach", "inhand", "dead", "impact", "crumble", "sack", "eggs",
    "landing", "dust", "stomp", "whip", "magic", "trail", "temp", "gravestone",
)


@dataclass(frozen=True)
class Creature:
    mod: str
    page: str
    name: str
    category: str
    prefixes: str
    notes: str = ""


# --------------------------------------------------------------------------- #
# paths / config
# --------------------------------------------------------------------------- #

def _addon_keys() -> list[str]:
    """Candidate keys for our add-on entry in context.preferences.addons.

    When the file is installed as an add-on, the key is the module name. When it
    is run from the Text Editor, Blender registers it as "__main__" and the
    preferences collection has no such entry at all.
    """
    keys = []
    for k in (__name__, __package__, "highpoly_pipeline"):
        if k and k != "__main__" and k not in keys:
            keys.append(k)
    return keys


def prefs(context):
    """Our add-on preferences, or None when running as a plain script."""
    addons = context.preferences.addons
    for key in _addon_keys():
        if key in addons:
            p = addons[key].preferences
            if p is not None:
                return p
    # last resort: any enabled add-on carrying our preferences class
    try:
        for key in addons.keys():
            p = addons[key].preferences
            if type(p).__name__ == "HPPreferences":
                return p
    except Exception:
        pass
    return None


def project_root(context) -> Path:
    """Resolved project folder: scene override > add-on prefs > built-in default."""
    scene_hp = getattr(context.scene, "hp", None)
    if scene_hp is not None and str(getattr(scene_hp, "project_root", "") or "").strip():
        return Path(bpy.path.abspath(scene_hp.project_root))
    p = prefs(context)
    if p is not None and str(getattr(p, "project_root", "") or "").strip():
        return Path(bpy.path.abspath(p.project_root))
    return Path(DEFAULT_PROJECT)


def load_creatures(root: Path) -> list[Creature]:
    path = root / "config" / "creatures.csv"
    out = []
    if not path.is_file():
        return out
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("mod") or row["mod"].strip().startswith("#"):
                continue
            out.append(
                Creature(
                    row["mod"].strip(), row["page"].strip(), row["creature"].strip(),
                    row["category"].strip(), row["prefixes"].strip(),
                    (row.get("notes") or "").strip(),
                )
            )
    return out


def find_creature(root: Path, mod: str, name: str) -> Creature | None:
    for c in load_creatures(root):
        if c.mod == mod and c.name == name:
            return c
    return None


def ref_dir(root: Path, creature: Creature) -> Path:
    return root / "reference" / MOD_FOLDERS[creature.mod] / creature.name


def incoming_dir(root: Path, creature: Creature) -> Path:
    return root / "raw_assets" / MOD_FOLDERS[creature.mod] / creature.name / "incoming"


def is_body_file(name: str) -> bool:
    return not any(part in name.lower() for part in NON_BODY)


# --------------------------------------------------------------------------- #
# PyNifly (the NIF import/export add-on this pipeline drives)
# --------------------------------------------------------------------------- #

PNIFLY_HINT = (
    "PyNifly is not available. Edit > Preferences > Add-ons > Install from Disk, "
    "pick tools/pynifly/io_scene_nifly/__init__.py (or enable 'Import-Export: niffly' "
    "if it is already listed), then run this again."
)


def pynifly_ready() -> bool:
    """True when the NIF import operator is registered.

    bpy.ops.<module>.<name> attribute access is lazy, so hasattr() lies - only a
    real call tells us the operator exists.
    """
    try:
        bpy.ops.import_scene.pynifly.poll()
        return True
    except Exception:
        return False


def ensure_pynifly() -> bool:
    """Try to switch PyNifly on for this session, then report whether it worked."""
    if pynifly_ready():
        return True
    try:
        import addon_utils
        addon_utils.enable("io_scene_nifly", default_set=True, persistent=True)
    except Exception:
        pass
    return pynifly_ready()


def main_nif(root: Path, creature: Creature) -> Path | None:
    files = [p for p in ref_dir(root, creature).rglob("*.nif") if is_body_file(p.name)]
    if not files:
        return None
    preferred = [p for p in files if p.stem.lower() == creature.name.lower()]
    if preferred:
        return preferred[0]
    return max(files, key=lambda p: p.stat().st_size)


def first_delivery(root: Path, creature: Creature) -> Path | None:
    folder = incoming_dir(root, creature)
    if not folder.is_dir():
        return None
    for ext in (".glb", ".gltf", ".blend", ".fbx", ".obj"):
        hits = sorted(folder.glob(f"*{ext}"))
        if hits:
            return hits[0]
    return None


# --------------------------------------------------------------------------- #
# scene helpers
# --------------------------------------------------------------------------- #

def objects_with(role: str):
    return [o for o in bpy.data.objects if o.get("hp_role") == role]


def tag(objs, role: str):
    for o in objs:
        o["hp_role"] = role


def delete_role(role: str):
    for o in list(objects_with(role)):
        bpy.data.objects.remove(o, do_unlink=True)


def clear_pipeline():
    for role in ("model", "vanilla_fur", "vanilla_body", "vanilla_mesh", "vanilla_armature"):
        delete_role(role)


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o and o.name in bpy.data.objects:
            o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0] if objs else None


def apply_transform(obj, location=False, rotation=False, scale=False):
    select_only([obj])
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)


def set_euler(obj, x: float, y: float, z: float):
    """Assign a rotation that will actually be applied.

    The glTF importer leaves objects in rotation_mode QUATERNION, where
    rotation_euler is only written to a dormant field - transform_apply then
    bakes the (identity) quaternion and the rotation silently does nothing.
    Switching the mode first also converts the current rotation, so nothing is
    lost; the object's transform is identity after a fit anyway.
    """
    if obj.rotation_mode != "XYZ":
        obj.rotation_mode = "XYZ"
    obj.rotation_euler = (x, y, z)


def world_bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def tri_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def mesh_stats(obj) -> str:
    if not obj:
        return "not loaded"
    return f"{len(obj.data.vertices):,} verts / {tri_count(obj):,} tris"


def ensure_uv(obj):
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    obj.data.uv_layers[0].name = "UVMap"


def ensure_vertex_color(obj):
    me = obj.data
    existing = {a.name for a in me.color_attributes}
    if "Col" not in existing:
        attr = me.color_attributes.new(name="Col", type="BYTE_COLOR", domain="POINT")
        for d in attr.data:
            d.color = (1.0, 1.0, 1.0, 1.0)


# --------------------------------------------------------------------------- #
# pipeline steps (shared by operators and one-click)
# --------------------------------------------------------------------------- #

def do_load_vanilla(context, creature: Creature, root: Path) -> str:
    if not ensure_pynifly():
        raise RuntimeError(PNIFLY_HINT)
    clear_pipeline()
    nif = main_nif(root, creature)
    if not nif:
        raise RuntimeError(f"no body NIF found for {creature.name}")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.pynifly(filepath=str(nif))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    arms = [o for o in new if o.type == "ARMATURE"]
    if not meshes:
        raise RuntimeError("vanilla import produced no meshes")
    tag(new, "vanilla_mesh")
    tag(arms, "vanilla_armature")
    tag(meshes, "vanilla_mesh")
    fur = [o for o in meshes if o.name.lower().startswith("fur")]
    tag(fur, "vanilla_fur")
    body_pool = [o for o in meshes if o not in fur] or meshes
    body = max(body_pool, key=lambda o: len(o.data.vertices))
    tag([body], "vanilla_body")
    context.scene["hp_vanilla_nif"] = str(nif)
    return nif.name


def do_import_model(context, creature: Creature, root: Path, filepath: Path | None = None) -> str:
    delete_role("model")
    path = Path(filepath) if filepath else first_delivery(root, creature)
    if not path or not path.is_file():
        raise RuntimeError("no model found in incoming/")
    before = set(bpy.data.objects)
    ext = path.suffix.lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif ext == ".blend":
        with bpy.data.libraries.load(str(path)) as (src, dst):
            dst.objects = [n for n in src.objects if n]
        for obj in dst.objects:
            if obj:
                bpy.context.scene.collection.objects.link(obj)
    else:
        raise RuntimeError(f"unsupported model format: {ext}")
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("model import produced no meshes")
    model = max(meshes, key=lambda o: len(o.data.vertices))
    tag([model], "model")
    model.name = "HP_Model"
    for extra in meshes:
        if extra is not model:
            extra.hide_set(True)
            extra.hide_render = True

    # Take it straight to vanilla size/orientation: a raw GLB is ~1/140th of the
    # wolf and lies on the wrong axis, which looks alarming when it first lands.
    try:
        note = " | " + do_fit(context, context.scene.hp)
    except Exception as exc:
        note = f" | no fit yet: {exc}"
    return path.name + note


def _bake_world_transform(model) -> None:
    """Bake the object's world transform into the mesh and reset the object.

    The orientation search measures the model in world space, so the rotation
    has to be applied in world space as well.  A GLB often brings its own root
    transform (a rotated root node), and without this the search would find
    one orientation and the model would end up in another.
    """
    from mathutils import Matrix

    matrix = model.matrix_world.copy()
    if matrix == Matrix.Identity(4):
        return
    mesh = model.data
    for v in mesh.vertices:
        v.co = matrix @ v.co
    mesh.update()
    model.matrix_world = Matrix.Identity(4)


def _clear_previous_fit(model) -> bool:
    """Undo the transform a previous Auto Fit baked into the vertices.

    Fit is destructive - rotation, scale and offset are applied straight to the
    mesh - so without this every press would stack a new transform on the old
    one and changing Rotate X could never undo the -90 the first fit applied.
    Reversing the recorded transform (exact inverse: un-offset, un-scale,
    un-rotate) makes fit idempotent while keeping decimation and skin weights.
    """
    rot = model.get("hp_fit_rot")
    if not rot:
        return False
    scale = tuple(model.get("hp_fit_scale") or (1.0, 1.0, 1.0))
    off = tuple(model.get("hp_fit_offset") or (0.0, 0.0, 0.0))

    select_only([model])
    model.location = (-off[0], -off[1], -off[2])
    apply_transform(model, location=True)

    model.scale = tuple((1.0 / s) if abs(s) > 1e-9 else 1.0 for s in scale)
    apply_transform(model, scale=True)

    euler = mathutils.Euler(
        (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), "XYZ")
    inv = euler.to_matrix().inverted().to_euler("XYZ")
    set_euler(model, inv.x, inv.y, inv.z)
    apply_transform(model, rotation=True)

    for key in ("hp_fit_rot", "hp_fit_scale", "hp_fit_offset"):
        if key in model:
            del model[key]
    return True


def do_fit(context, settings) -> str:
    body = objects_with("vanilla_body")
    model = objects_with("model")
    if not body or not model:
        raise RuntimeError("load the vanilla reference and a model first")
    body, model = body[0], model[0]

    had_weights = any(
        g.weight > 0.0 for v in model.data.vertices for g in v.groups) if model.vertex_groups else False
    _clear_previous_fit(model)
    _bake_world_transform(model)

    orient_note = ""
    applied_rot = (float(settings.rotate_x), 0.0, float(settings.rotate_z))
    if settings.auto_orient:
        # Try every axis-aligned orientation and keep the one whose bone
        # weights would match the vanilla's best.  This is what stops a model
        # with its head down (or facing the other way) from inheriting the
        # wrong bones and deforming into a mess in game.
        matrix, median, l1, spread = find_best_orientation(model, body)
        model.rotation_mode = "XYZ"
        model.rotation_euler = matrix.to_euler("XYZ")
        applied_rot = tuple(math.degrees(v) for v in model.rotation_euler)
        apply_transform(model, rotation=True)
        orient_note = (
            f", auto-oriented ({applied_rot[0]:.0f}/{applied_rot[1]:.0f}/"
            f"{applied_rot[2]:.0f}, fit {median:.1f} units)"
        )
    else:
        set_euler(
            model,
            math.radians(settings.rotate_x),
            0.0,
            math.radians(settings.rotate_z),
        )
        apply_transform(model, rotation=True)

    vlo, vhi = world_bbox(body)
    mlo, mhi = world_bbox(model)
    vdim = vhi - vlo
    mdim = mhi - mlo
    if max(mdim) <= 0:
        raise RuntimeError("model has zero size")
    scale = (max(vdim) / max(mdim)) * settings.scale_multiplier
    model.scale = (scale, scale, scale)
    apply_transform(model, scale=True)

    axes = ""
    fx = fy = fz = 1.0
    if settings.fit_mode == "AXIS":
        # Match the vanilla silhouette per axis so the body still fits animations,
        # doorframes and hitboxes. Uniform keeps the AI model's own proportions.
        vlo, vhi = world_bbox(body)
        mlo, mhi = world_bbox(model)
        md = mhi - mlo
        fx = (vdim.x / md.x) if md.x > 0 else 1.0
        fy = (vdim.y / md.y) if md.y > 0 else 1.0
        fz = (vdim.z / md.z) if md.z > 0 else 1.0
        model.scale = (fx, fy, fz)
        apply_transform(model, scale=True)
        axes = f", axis-fit {fx:.3f}/{fy:.3f}/{fz:.3f}"

    vlo, vhi = world_bbox(body)
    mlo, mhi = world_bbox(model)
    vc = (vlo + vhi) / 2
    mc = (mlo + mhi) / 2
    model.location.x += vc.x - mc.x
    model.location.y += vc.y - mc.y
    model.location.z += vlo.z - mlo.z
    off = tuple(float(v) for v in model.location)
    apply_transform(model, location=True)

    # Record exactly what was baked in, so the next Auto Fit can reverse it.
    model["hp_fit_rot"] = applied_rot
    model["hp_fit_scale"] = (float(scale * fx), float(scale * fy), float(scale * fz))
    model["hp_fit_offset"] = off

    mlo, mhi = world_bbox(model)
    md = mhi - mlo
    note = " | already weighted: re-run Transfer Weights" if had_weights else ""

    # How far the model's proportions are from the vanilla's.  A model that is
    # already in the vanilla's stance fits with nearly the same scale on every
    # axis; a model in a different stance (Skyrim's bear rears up, an AI bear
    # stands on all fours) has to be squashed to fit the box, and its
    # animation will be wrong no matter how well it is scaled.
    spread = max(fx, fy, fz) / max(min(fx, fy, fz), 1e-6)
    if spread > 1.25:
        note += (
            f" | WARNING: the model's proportions differ from the vanilla's "
            f"({spread:.2f}x) - it is probably in a different pose than the "
            f"bind pose Skyrim animates. Use the 'Keep model proportions' fit "
            f"and regenerate the model from reference/<mod>/<creature>/pose_side.png"
        )
    return (
        f"scale {scale:.2f}, dims {md.x:.2f} x {md.y:.2f} x {md.z:.2f}"
        f"{axes}{orient_note}{note}"
    )


# --------------------------------------------------------------------------- #
# pose / orientation
# --------------------------------------------------------------------------- #

def _cube_rotations():
    """The 24 axis-aligned rotations - every way a model can be turned.

    An AI model can come in any of them (Y-up, Z-up, nose to +Y, nose to -Y),
    and only one of them lines the model up with the vanilla body.
    """
    import itertools
    from mathutils import Matrix

    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            # start from zeros: an identity would keep its 1s in the other
            # positions and turn these into something that is not a rotation
            m = Matrix(((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
            for row, col in enumerate(perm):
                m[row][col] = float(signs[row])
            if m.determinant() > 0:
                out.append(m)
    return out


def _bone_share_table(obj):
    """(names, per-vertex bone weight matrix) for a mesh."""
    import numpy as np

    names: list[str] = []
    index: dict[str, int] = {}
    rows = []
    for v in obj.data.vertices:
        row: dict[int, float] = {}
        for g in v.groups:
            if g.weight <= 0.0:
                continue
            name = obj.vertex_groups[g.group].name
            if name.startswith("SBP_"):
                continue
            if name not in index:
                index[name] = len(names)
                names.append(name)
            row[index[name]] = row.get(index[name], 0.0) + g.weight
        rows.append(row)
    matrix = np.zeros((len(rows), len(names)), dtype=np.float32)
    for i, row in enumerate(rows):
        for b, w in row.items():
            matrix[i, b] = w
    return names, index, matrix


def _fit_transform(verts, body_lo, body_hi, uniform: bool = False):
    """The fit the pipeline applies: match the vanilla's box.

    With uniform=True only the largest axis is matched and the model keeps its
    own proportions - that is what the orientation search scores with, because
    a wrong orientation could otherwise "win" by being squashed flat until it
    fits.
    """
    import numpy as np

    lo = verts.min(axis=0)
    hi = verts.max(axis=0)
    dim = hi - lo
    target = body_hi - body_lo
    if uniform:
        big = max(dim.max(), 1e-6)
        factor = target.max() / big
        scale = np.array([factor, factor, factor])
    else:
        scale = np.where(dim > 1e-6, target / np.maximum(dim, 1e-6), 1.0)
    out = verts * scale
    out = out - out.min(axis=0) + body_lo
    return out, scale


def find_best_orientation(model, body, samples: int = 4000):
    """Pick the rotation that lines the model up with the vanilla body.

    Scored by how closely the model then sits on the vanilla body (the median
    distance from the model's surface to the vanilla's), with the bone weight
    distribution as the tie breaker.

    This matters more than it looks: an AI model is often delivered turned
    around or upside down.  The bounding box fit cannot tell - a wolf on its
    back has the same box as a wolf on its feet - so the model ends up
    inheriting the wrong bones and the game deforms it into a mess.
    """
    import numpy as np
    from mathutils import kdtree

    body_matrix = body.matrix_world
    body_verts = np.array([(body_matrix @ v.co)[:] for v in body.data.vertices],
                          dtype=np.float64)
    body_lo = body_verts.min(axis=0)
    body_hi = body_verts.max(axis=0)

    _names, _index, weights = _bone_share_table(body)
    totals = weights.sum(axis=0)
    vanilla_shares = totals / (totals.sum() or 1.0)

    kd = kdtree.KDTree(len(body_verts))
    for i, co in enumerate(body_verts):
        kd.insert((float(co[0]), float(co[1]), float(co[2])), i)
    kd.balance()

    model_matrix = model.matrix_world
    verts = np.array([(model_matrix @ v.co)[:] for v in model.data.vertices],
                     dtype=np.float64)
    step = max(1, len(verts) // samples)
    probe = verts[::step]

    target = body_hi - body_lo
    best = None
    for matrix in _cube_rotations():
        rotation = np.array(matrix.transposed())
        rotated = verts @ rotation
        lo = rotated.min(axis=0)
        hi = rotated.max(axis=0)
        dim = hi - lo
        scale = np.where(dim > 1e-6, target / np.maximum(dim, 1e-6), 1.0)
        offset = body_lo - (rotated * scale).min(axis=0)

        fitted = (probe @ rotation) * scale + offset
        indices = []
        dists = []
        for p in fitted:
            _, idx, d = kd.find((float(p[0]), float(p[1]), float(p[2])))
            indices.append(idx)
            dists.append(d)
        shared = weights[indices].sum(axis=0)
        shares = shared / (shared.sum() or 1.0)
        l1 = float(np.abs(shares - vanilla_shares).sum())
        median = float(np.median(dists))
        spread = float(scale.max() / max(scale.min(), 1e-6))
        # a correct orientation needs almost no squashing; a wrong one can
        # only "fit" by being flattened, so the spread counts against it
        key = (round(median * (1.0 + max(0.0, spread - 1.25)), 3), round(l1, 3))
        if best is None or key < best[0]:
            best = (key, matrix, (median, l1, spread))
    key, matrix, info = best
    median, l1, spread = info
    return matrix, median, l1, spread


# --------------------------------------------------------------------------- #
# pose
# --------------------------------------------------------------------------- #

def _bone_weight_tables(obj):
    """(bone names, per vertex list of (bone index, weight)).

    The SBP_* groups are NiSkinPartition markers, not bones, so they are
    skipped.
    """
    names: list[str] = []
    index: dict[str, int] = {}
    per_vertex: list[list[tuple[int, float]]] = []
    for v in obj.data.vertices:
        entries: list[tuple[int, float]] = []
        for g in v.groups:
            if g.weight <= 0.0:
                continue
            name = obj.vertex_groups[g.group].name
            if name.startswith("SBP_"):
                continue
            if name not in index:
                index[name] = len(names)
                names.append(name)
            entries.append((index[name], float(g.weight)))
        per_vertex.append(entries)
    return names, index, per_vertex


def _principal_axis(points, weights):
    """Weighted principal direction of a point cloud (None if degenerate)."""
    import numpy as np

    if len(points) < 3:
        return None
    p = np.asarray(points, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    total = w.sum()
    if total <= 0.0:
        return None
    mean = (p * w[:, None]).sum(axis=0) / total
    d = p - mean
    cov = (d * w[:, None]).T @ d / total
    try:
        values, vectors = np.linalg.eigh(cov)
    except np.linalg.LinAlgError:
        return None
    axis = vectors[:, int(np.argmax(values))]
    norm = float(np.linalg.norm(axis))
    if norm < 1e-9:
        return None
    return mean, axis / norm


def _model_edges(mesh) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for poly in mesh.polygons:
        vs = list(poly.vertices)
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            if a < b:
                edges.append((a, b))
            else:
                edges.append((b, a))
    return edges


def do_decimate(context, settings) -> str:
    body = objects_with("vanilla_body")
    model = objects_with("model")
    if not body or not model:
        raise RuntimeError("load the vanilla reference and a model first")
    body, model = body[0], model[0]
    vanilla_tris = tri_count(body)
    target = settings.target_tris or vanilla_tris * settings.target_multiplier
    current = tri_count(model)
    if target >= current:
        return f"already {current:,} tris (target {target:,}) - skipped"
    # Collapse in passes: one huge ratio change leaves visible artefacts on a
    # 500k-tri AI mesh, while repeated halving keeps the silhouette.
    passes = 0
    select_only([model])
    while tri_count(model) > target:
        now = tri_count(model)
        frac = target / now
        # Halve until close, then land on the target: one huge collapse in a single
        # pass leaves visible artefacts on a 500k-tri AI mesh.
        ratio = 0.5 if frac < 0.3 else frac
        if ratio >= 1.0:
            break
        mod = model.modifiers.new("HP_Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        select_only([model])
        bpy.ops.object.modifier_apply(modifier=mod.name)
        passes += 1
        if tri_count(model) >= now:  # no progress, give up
            break
    return (
        f"{current:,} -> {tri_count(model):,} tris "
        f"(target {target:,}, {passes} pass{'es' if passes != 1 else ''})"
    )


def do_transfer_weights(context) -> str:
    arms = objects_with("vanilla_armature")
    body = objects_with("vanilla_body")
    model = objects_with("model")
    if not arms or not body or not model:
        raise RuntimeError("need vanilla armature, vanilla body and a model")
    arm, body, model = arms[0], body[0], model[0]

    for mod in list(model.modifiers):
        if mod.type == "ARMATURE":
            model.modifiers.remove(mod)
    ensure_uv(model)
    ensure_vertex_color(model)

    # Data transfer only fills groups the target already has -- create them first
    # with the vanilla body's bone names, then let the transfer write the weights.
    existing = {g.name for g in model.vertex_groups}
    created = 0
    for g in body.vertex_groups:
        if g.name not in existing:
            model.vertex_groups.new(name=g.name)
            created += 1

    transfer = model.modifiers.new("HP_Weights", "DATA_TRANSFER")
    transfer.object = body
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    select_only([model])
    bpy.ops.object.modifier_apply(modifier=transfer.name)

    # Drop groups the transfer never touched so they don't become stray bones.
    totals: dict[int, float] = {}
    for v in model.data.vertices:
        for g in v.groups:
            totals[g.group] = totals.get(g.group, 0.0) + g.weight
    dead = [g.name for g in model.vertex_groups if totals.get(g.index, 0.0) <= 0.0]
    for name in dead:
        g = model.vertex_groups.get(name)
        if g:
            model.vertex_groups.remove(g)

    model.parent = arm
    model.matrix_parent_inverse = arm.matrix_world.inverted()
    arm_mod = model.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = arm

    # SBP_* is a NiSkinPartition marker, not a bone, but limit_total counts it.
    # Zero it for the limit pass so the model keeps all four bone influences, then
    # put weight 1.0 back so every triangle lands in the body partition.
    sbp_groups = [g for g in model.vertex_groups if g.name.startswith("SBP_")]
    all_idx = list(range(len(model.data.vertices)))
    for g in sbp_groups:
        g.add(all_idx, 0.0, "REPLACE")

    select_only([model])
    try:
        bpy.ops.object.vertex_group_limit_total(limit=4)
    except Exception:
        pass
    try:
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    except Exception:
        pass

    for g in sbp_groups:
        g.add(all_idx, 1.0, "REPLACE")

    weighted = sum(1 for v in model.data.vertices if any(g.weight > 0.0 for g in v.groups))
    idx_name = {g.index: g.name for g in model.vertex_groups}
    max_inf = max((
        len([
            g for g in v.groups
            if g.weight > 0.0 and not idx_name.get(g.group, "").startswith("SBP_")
        ])
        for v in model.data.vertices), default=0)
    if weighted == 0:
        raise RuntimeError("weight transfer wrote nothing - check that the model sits inside the vanilla body")
    return (
        f"{len(model.vertex_groups)} groups (+{created} created), "
        f"max {max_inf} inf, {weighted}/{len(model.data.vertices)} verts weighted"
    )


def _find_images(model):
    diffuse = normal = orm = None
    for mat in model.data.materials:
        if not mat or not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            base = node.inputs.get("Base Color")
            if base and base.links:
                src = base.links[0].from_node
                if src.type == "TEX_IMAGE":
                    diffuse = src.image
            nrm = node.inputs.get("Normal")
            if nrm and nrm.links:
                src = nrm.links[0].from_node
                if src.type == "NORMAL_MAP" and src.inputs.get("Color").links:
                    nimg = src.inputs["Color"].links[0].from_node
                    if nimg.type == "TEX_IMAGE":
                        normal = nimg.image
            rough = node.inputs.get("Roughness")
            if rough and rough.links:
                src = rough.links[0].from_node
                if src.type == "SEPARATE_COLOR" and src.inputs.get("Color").links:
                    oimg = src.inputs["Color"].links[0].from_node
                    if oimg.type == "TEX_IMAGE":
                        orm = oimg.image
    return diffuse, normal, orm


def _make_spec_normal(normal_img, orm_img, name, size=2048):
    if np is None or normal_img is None:
        return normal_img
    normal_img.scale(size, size)
    w, h = normal_img.size
    npx = np.empty(w * h * 4, dtype=np.float32)
    normal_img.pixels.foreach_get(npx)
    npx = npx.reshape(-1, 4)
    if orm_img is not None:
        orm_img.scale(size, size)
        opx = np.empty(w * h * 4, dtype=np.float32)
        orm_img.pixels.foreach_get(opx)
        opx = opx.reshape(-1, 4)
        # Glossiness with a floor: raw 1-roughness averages ~0.14 on fur, which
        # would leave the body almost matte once multiplied with the vanilla _sk.
        npx[:, 3] = 0.45 + 0.55 * (1.0 - opx[:, 1])
    else:
        npx[:, 3] = 1.0
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    # Colorspace must be set before the pixels: assigning it re-reads the buffer
    # and a fresh generated image has no file to re-read, so it comes back black.
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(npx.ravel())
    img.pack()
    return img


def do_setup_material(context, creature: Creature, root: Path) -> str:
    body = objects_with("vanilla_body")
    model = objects_with("model")
    if not body or not model:
        raise RuntimeError("load the vanilla reference and a model first")
    body, model = body[0], model[0]

    diffuse, normal, orm = _find_images(model)
    if diffuse is None:
        raise RuntimeError("could not find a base colour texture on the model")

    size = 2048
    try:
        size = int(context.scene.hp.texture_size)
    except Exception:
        pass
    diffuse.scale(size, size)
    spec_normal = _make_spec_normal(normal, orm, f"{creature.name}_n", size)

    vanilla_mat = next((m for m in body.data.materials if m), None)
    if vanilla_mat is None:
        raise RuntimeError("vanilla body has no material")
    mat = vanilla_mat.copy()
    mat.name = f"{creature.name}_HP"

    nodes = mat.node_tree.nodes
    if "Diffuse_Texture" in nodes:
        nodes["Diffuse_Texture"].image = diffuse
    if "Normal_Texture" in nodes and spec_normal:
        nodes["Normal_Texture"].image = spec_normal
    # Subsurface (soft/rim lighting) keeps the vanilla _sk.dds on purpose: Skyrim
    # reads that map as a lighting mask, not as a second albedo.

    model.data.materials.clear()
    model.data.materials.append(mat)

    # Path must contain a "textures" folder: PyNifly exports everything from that
    # part onward, lowercased, with a .dds suffix.
    tex_dir = incoming_dir(root, creature) / "textures" / "actors" / creature.name
    tex_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for img, suffix in ((diffuse, "d"), (spec_normal, "n")):
        if img is None:
            continue
        png = tex_dir / f"{creature.name}_{suffix}.png"
        img.filepath_raw = str(png)
        img.file_format = "PNG"
        img.save()
        img.filepath_raw = str(png)
        saved.append(png.name)

    # The shell texture: same coat colour, strand mask in the alpha channel.
    # It is only needed when shells are on, but writing it always keeps the
    # texture folder in sync with the panel settings.
    try:
        shells = int(context.scene.hp.shell_count)
    except Exception:
        shells = 0
    if shells > 0:
        shell_img = _make_shell_image(diffuse, creature.name)
        png = tex_dir / f"{creature.name}_hp_shell.png"
        shell_img.filepath_raw = str(png)
        shell_img.file_format = "PNG"
        shell_img.save()
        shell_img.filepath_raw = str(png)
        saved.append(png.name)

    return f"material {mat.name}, textures: {', '.join(saved)}"


# --------------------------------------------------------------------------- #
# fur shells (FluffyWorks style)
# --------------------------------------------------------------------------- #

# FluffyWorks builds its fur as a stack of alpha-blended copies of the body,
# each pushed further out along the vertex normals.  Every layer gets a higher
# alpha threshold, so the outer layers only keep the brightest strands - that
# taper is what makes it read as fur instead of a stack of skins.
SHELL_PREFIX = "HP_Shell"
SHELL_ALPHA_FLAGS = 4844        # PyNifly's default: alpha blend + alpha test
SHELL_THRESHOLD_STEP = 15       # FluffyWorks uses 15, 30, 45 ... 240


def _value_noise(height: int, width: int, cells_y: int, cells_x: int, rng):
    """Bilinear value noise, stretched along V so it reads as strands."""
    import numpy as np

    grid = rng.random((cells_y + 1, cells_x + 1)).astype(np.float32)
    ys = np.linspace(0, cells_y, height, endpoint=False)
    xs = np.linspace(0, cells_x, width, endpoint=False)
    y0 = ys.astype(np.int32)
    x0 = xs.astype(np.int32)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    g00 = grid[np.ix_(y0, x0)]
    g01 = grid[np.ix_(y0, x0 + 1)]
    g10 = grid[np.ix_(y0 + 1, x0)]
    g11 = grid[np.ix_(y0 + 1, x0 + 1)]
    top = g00 * (1 - fx) + g01 * fx
    bottom = g10 * (1 - fx) + g11 * fx
    return top * (1 - fy) + bottom * fy


def _strand_mask(height: int, width: int, seed: int = 7):
    """Fur strand mask with a broad value spread.

    The spread matters: the shells fade because each layer has a higher alpha
    threshold, so the mask has to cover the whole range - dense inner layers
    keep nearly everything, the outer ones only the brightest strands.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    mask = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    total = 0.0
    cells = 48
    for _ in range(4):
        # fine across U, coarse along V -> long thin strands
        mask += _value_noise(height, width, max(2, cells // 8), cells, rng) * amplitude
        total += amplitude
        amplitude *= 0.5
        cells *= 2
    mask /= total
    return np.clip((mask - 0.5) * 1.7 + 0.55, 0.0, 1.0)


def _make_shell_image(diffuse_img, name: str, seed: int = 7):
    """Build the shell texture: fur colour in RGB, strand mask in alpha.

    The RGB is a copy of the diffuse so the fur keeps the coat colour.  The
    alpha is scaled by a blurred version of the diffuse, so dark features (eyes,
    nose, mouth) end up with almost no fur on them.
    """
    import numpy as np

    width, height = diffuse_img.size
    pixels = np.array(diffuse_img.pixels[:], dtype=np.float32).reshape(height, width, 4)
    rgb = pixels[:, :, :3].copy()
    luma = rgb[:, :, 0] * 0.3 + rgb[:, :, 1] * 0.6 + rgb[:, :, 2] * 0.1

    # blur the luma so isolated dark specks do not punch holes in the fur
    blurred = bpy.data.images.new("hp_luma_tmp", width, height)
    buf = np.zeros((height, width, 4), dtype=np.float32)
    buf[:, :, 0] = buf[:, :, 1] = buf[:, :, 2] = luma
    buf[:, :, 3] = 1.0
    blurred.pixels = buf.ravel().tolist()
    blurred.scale(max(8, width // 16), max(8, height // 16))
    blurred.scale(width, height)
    soft = np.array(blurred.pixels[:], dtype=np.float32).reshape(height, width, 4)[:, :, 0]
    bpy.data.images.remove(blurred)

    coverage = np.clip((soft - 0.12) / 0.28, 0.0, 1.0)
    mask = _strand_mask(height, width, seed=seed)
    alpha = np.clip(mask * 0.8 + 0.2, 0.0, 1.0) * coverage

    out = np.zeros((height, width, 4), dtype=np.float32)
    out[:, :, :3] = rgb
    out[:, :, 3] = alpha
    img = bpy.data.images.new(f"{name}_shell", width, height, alpha=True)
    img.pixels = out.ravel().tolist()
    return img


def _make_shell_base(context, model, target_tris: int):
    """A decimated, smoothed copy of the model to build the shell stack from."""
    base = model.copy()
    base.data = model.data.copy()
    base.name = "HP_ShellBase"
    for mod in list(base.modifiers):
        if mod.type == "ARMATURE":
            base.modifiers.remove(mod)
    context.collection.objects.link(base)

    current = tri_count(base)
    target = max(200, min(int(target_tris), current))
    select_only([base])
    while tri_count(base) > target:
        now = tri_count(base)
        ratio = target / now
        ratio = 0.5 if ratio < 0.3 else ratio
        mod = base.modifiers.new("HP_ShellDecimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        select_only([base])
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if tri_count(base) >= now:
            break

    # smooth away the spikes a collapse leaves behind, otherwise the shells
    # poke through the body in places
    smooth = base.modifiers.new("HP_ShellSmooth", "SMOOTH")
    smooth.factor = 0.5
    smooth.iterations = 3
    select_only([base])
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    return base


def _set_alpha_threshold(mat, threshold: int) -> bool:
    """Set the alpha test cutoff in the Skyrim shader node group.

    PyNifly's exporter writes the NiAlphaProperty from the material's shader
    node group - the node linked to the group's "Alpha Property" input - and
    not from the material's custom properties.  Every material copied from the
    vanilla body inherits its threshold (62), which would give all the shells
    the same cutoff and no taper.
    """
    tree = getattr(mat, "node_tree", None)
    if tree is None:
        return False
    for node in tree.nodes:
        for inp in node.inputs:
            if inp.name != "Alpha Property" or not inp.is_linked:
                continue
            source = inp.links[0].from_node
            for socket in source.inputs:
                if socket.name == "Alpha Threshold":
                    socket.default_value = float(threshold)
                elif socket.name == "Alpha Test":
                    socket.default_value = True
            return True
    return False


def _shell_material(model, shell_png: Path, layer: int):
    """One material per shell layer.

    Each layer gets its own alpha threshold (15, 30, 45 ...): the outer
    layers must only keep the brightest strands of the strand mask, and that
    taper is what makes the stack read as fur instead of a stack of skins.
    """
    src = next((m for m in model.data.materials if m), None)
    if src is None:
        raise RuntimeError("the model has no material - run Setup Material first")
    mat = src.copy()
    mat.name = f"{SHELL_PREFIX}_L{layer:02d}"
    threshold = SHELL_THRESHOLD_STEP * layer
    _set_alpha_threshold(mat, threshold)
    mat["NiAlphaProperty_flags"] = SHELL_ALPHA_FLAGS
    mat["NiAlphaProperty_threshold"] = threshold
    img = bpy.data.images.load(str(shell_png))
    img.name = shell_png.stem
    nodes = mat.node_tree.nodes
    if "Diffuse_Texture" in nodes:
        nodes["Diffuse_Texture"].image = img
    return mat


def do_make_shells(context, creature: Creature, root: Path, settings) -> str:
    """Build the FluffyWorks-style shell stack (see the section comment above)."""
    model = objects_with("model")
    if not model:
        raise RuntimeError("no model loaded")
    model = model[0]

    count = int(settings.shell_count)
    delete_role("shell")
    if count <= 0:
        return "shells: off"

    tex_dir = incoming_dir(root, creature) / "textures" / "actors" / creature.name
    # "_hp_shell" and not "_shell": FluffyWorks already ships <creature>_shell.dds
    # for its own fur, and the two must not fight over the same file name.
    shell_png = tex_dir / f"{creature.name}_hp_shell.png"
    if not shell_png.is_file():
        raise RuntimeError(
            f"shell texture {shell_png.name} is missing - run Setup Material first")

    base = _make_shell_base(context, model, int(settings.shell_tris))
    spacing = float(settings.shell_spacing)

    made = []
    for layer in range(1, count + 1):
        mat = _shell_material(model, shell_png, layer)
        shell = base.copy()
        shell.data = base.data.copy()
        # no dots in the name: Blender treats ".001" as its own duplicate suffix
        shell.name = f"{SHELL_PREFIX}_L{layer:02d}"
        shell.data.materials.clear()
        shell.data.materials.append(mat)
        mesh = shell.data
        for v in mesh.vertices:
            v.co += v.normal * (layer * spacing)
        mesh.update()
        context.collection.objects.link(shell)
        tag([shell], "shell")
        shell["hp_shell_layer"] = layer
        made.append(shell)
    bpy.data.objects.remove(base, do_unlink=True)

    tris = tri_count(made[0]) if made else 0
    return (
        f"{len(made)} shells x {tris:,} tris, spacing {spacing:.2f} "
        f"(fur length {count * spacing:.2f} units)"
    )


def do_validate(context) -> str:
    model = objects_with("model")
    arms = objects_with("vanilla_armature")
    if not model:
        raise RuntimeError("no model loaded")
    model = model[0]
    me = model.data

    idx_name = {g.index: g.name for g in model.vertex_groups}
    max_inf = 0
    zero = 0
    for v in me.vertices:
        n = len([
            g for g in v.groups
            if g.weight > 0.0 and not idx_name.get(g.group, "").startswith("SBP_")
        ])
        max_inf = max(max_inf, n)
        if n == 0:
            zero += 1

    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()

    arm_bones = {b.name for b in arms[0].data.bones} if arms else set()
    group_names = {g.name for g in model.vertex_groups}
    # SBP_* groups are NiSkinPartition markers PyNifly writes back out, not bones.
    stray = sorted(n for n in group_names - arm_bones if not n.startswith("SBP_"))
    has_partition = any(n.startswith("SBP_") for n in group_names)

    problems = []
    if max_inf > 4:
        problems.append(f"{max_inf} influences")
    if zero:
        problems.append(f"{zero} unweighted verts")
    if not me.uv_layers:
        problems.append("no UVs")
    if stray:
        problems.append(f"{len(stray)} stray groups ({stray[0]})")
    if not has_partition:
        problems.append("no SBP partition marker")
    if not any(m for m in me.materials):
        problems.append("no material")
    status = "OK" if not problems else "CHECK: " + ", ".join(problems)
    return (
        f"{status} | {len(me.vertices):,} verts, {tri_count(model):,} tris, "
        f"max {max_inf} inf, {zero} unweighted, {nonman:,} non-manifold edges"
    )


def postprocess_nif(path: Path) -> str:
    """Give the shell layers FluffyWorks' shader setup.

    The alpha blend and the per-layer threshold are written by the exporter
    (they come from the material), but the DOUBLE_SIDED flag has no Blender
    equivalent, so it is patched into the exported NIF.  Rim and soft lighting
    are dropped as well: the vanilla _sk.dds lighting map belongs to the old
    body and only muddies up the thin fur layers.
    """
    try:
        from pyn.pynifly import NifFile
        from pyn.nifconstants import ShaderFlags2
    except Exception as exc:
        return f"shell patch skipped: {exc}"

    try:
        nif = NifFile(str(path))
        patched = []
        for shape in nif.shapes:
            if not shape.name.startswith(SHELL_PREFIX):
                continue
            shader = shape.shader
            props = shader.properties
            props.shaderflags2_set(ShaderFlags2.DOUBLE_SIDED)
            props.shaderflags2_clear(ShaderFlags2.RIM_LIGHTING)
            props.shaderflags2_clear(ShaderFlags2.SOFT_LIGHTING)
            shader.properties = props
            patched.append(shape.name)
        nif.save()
        nif.close()
    except Exception as exc:
        return f"shell patch failed: {exc}"
    return f"{len(patched)} shells patched"


def do_export(context, creature: Creature, root: Path, keep_fur=True, keep_extra=False) -> str:
    model = objects_with("model")
    arms = objects_with("vanilla_armature")
    if not model or not arms:
        raise RuntimeError("nothing to export")
    model = model[0]
    arm = arms[0]

    nif = main_nif(root, creature)
    if not nif:
        raise RuntimeError("cannot determine vanilla output path")
    relative = Path(nif).relative_to(ref_dir(root, creature))
    out = root / "build" / MOD_FOLDERS[creature.mod] / relative
    out.parent.mkdir(parents=True, exist_ok=True)

    selection = [model, arm]
    shells = objects_with("shell")
    if shells:
        selection += shells
    if keep_fur:
        selection += objects_with("vanilla_fur")
    keep_ids = {o.name for o in selection}

    # The exporter pulls in everything under the NIF root, so the geometry this
    # model replaces has to be hidden while it runs.
    replaced = []
    for o in objects_with("vanilla_mesh"):
        if o.name in keep_ids:
            continue
        if o.get("hp_role") == "vanilla_fur":
            if keep_fur:  # already in the selection, belt and braces
                continue
        elif keep_extra:
            continue  # parts the model does not cover (horns, eyes, armour)
        replaced.append(o)
    for o in replaced:
        o.hide_set(True)
        o.hide_render = True

    if not ensure_pynifly():
        raise RuntimeError(PNIFLY_HINT)
    try:
        select_only(selection)
        bpy.ops.export_scene.pynifly(filepath=str(out), target_game="SKYRIMSE")
    finally:
        for o in replaced:
            o.hide_set(False)
            o.hide_render = False

    patched = ""
    if shells:
        patched = " | " + postprocess_nif(out)

    work = incoming_dir(root, creature).parent / "work"
    work.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(work / f"{creature.name}.blend"))
    return str(out.relative_to(root)) + patched


def run_full(context, settings):
    root = project_root(context)
    creature = find_creature(root, settings.mod, settings.creature)
    if not creature:
        raise RuntimeError("creature not found in config/creatures.csv")
    log = []
    log.append("load: " + do_load_vanilla(context, creature, root))
    log.append("import: " + do_import_model(context, creature, root))
    log.append("fit: " + do_fit(context, settings))
    log.append("decimate: " + do_decimate(context, settings))
    log.append("rig: " + do_transfer_weights(context))
    log.append("material: " + do_setup_material(context, creature, root))
    log.append("shells: " + do_make_shells(context, creature, root, settings))
    log.append("validate: " + do_validate(context))
    log.append("export: " + do_export(
        context, creature, root, settings.keep_fur, settings.keep_extra_vanilla))
    return "\n".join(log)


# --------------------------------------------------------------------------- #
# properties
# --------------------------------------------------------------------------- #

def _refit_update(self, context):
    """Rotate X / Rotate Z / Scale / Fit are live: re-fit the moment they change.

    Fitting only re-applies a reversible transform (~10 ms even on a 273k-tri
    model), so dragging a slider can move the model instead of silently doing
    nothing until a button is pressed.
    """
    try:
        if not objects_with("model") or not objects_with("vanilla_body"):
            return  # nothing to fit yet - import runs the fit itself
        self.status = do_fit(context, self)
    except Exception as exc:
        self.status = f"fit: {exc}"


def creature_items(self, context):
    try:
        root = project_root(context)
        creatures = [c for c in load_creatures(root) if c.mod == self.mod]
    except Exception:
        creatures = []
    if not creatures:
        return [("NONE", "(no creatures)", "Check project root")]
    return [(c.name, c.name, f"{c.page}") for c in creatures]


class HPPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    project_root: bpy.props.StringProperty(
        name="Project Root",
        subtype="DIR_PATH",
        default=DEFAULT_PROJECT,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "project_root")
        root = Path(bpy.path.abspath(self.project_root))
        layout.label(text=f"config found: {str((root / 'config' / 'creatures.csv').is_file())}")


class HPSettings(bpy.types.PropertyGroup):
    project_root: bpy.props.StringProperty(
        name="Project root",
        subtype="DIR_PATH",
        default="",
        description="Folder containing config/creatures.csv. "
                    "Leave empty to use the add-on preference (or the built-in default)",
    )
    mod: bpy.props.EnumProperty(
        name="Mod",
        items=[("Creatures", "Creatures", ""), ("Enemies", "Enemies", "")],
        default="Creatures",
    )
    creature: bpy.props.EnumProperty(name="Creature", items=creature_items)
    model_file: bpy.props.StringProperty(name="Model", subtype="FILE_PATH")
    target_multiplier: bpy.props.IntProperty(
        name="Target x Vanilla", default=6, min=1, max=64,
        description="Tri budget as a multiple of vanilla",
    )
    target_tris: bpy.props.IntProperty(
        name="Target Tris", default=0, min=0,
        description="0 = use the multiplier",
    )
    rotate_x: bpy.props.FloatProperty(
        name="Rotate X", default=-90.0,
        description="Turns the imported model onto its feet - takes effect "
                    "immediately. Ignored when Auto Orient is on",
        update=_refit_update,
    )
    rotate_z: bpy.props.FloatProperty(
        name="Rotate Z", default=0.0,
        description="Turns the model left/right - takes effect immediately. "
                    "Ignored when Auto Orient is on",
        update=_refit_update,
    )
    auto_orient: bpy.props.BoolProperty(
        name="Auto Orient", default=True,
        description="Try all 24 axis-aligned orientations and keep the one "
                    "whose bones line up with the vanilla body. A model with "
                    "its head down, or facing the other way, otherwise "
                    "inherits the wrong bones and deforms in game",
        update=_refit_update,
    )
    scale_multiplier: bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.01,
        description="Extra multiplier on top of the automatic size match - takes effect immediately",
        update=_refit_update,
    )
    fit_mode: bpy.props.EnumProperty(
        name="Fit",
        items=[
            ("AXIS", "Match vanilla silhouette",
             "Scale each axis to the vanilla bounding box - fits animations and doorframes"),
            ("UNIFORM", "Keep model proportions",
             "One scale factor on all axes - the model keeps its own shape"),
        ],
        default="AXIS",
        update=_refit_update,
    )
    keep_fur: bpy.props.BoolProperty(
        name="Keep vanilla fur shell",
        default=False,
        description="Export the vanilla Fur shell shape alongside the new body. "
                    "Off by default: that shell was modelled for the vanilla body "
                    "and does not line up with a new mesh",
    )
    shell_count: bpy.props.IntProperty(
        name="Fur shells", default=8, min=0, max=16,
        description="Number of alpha-blended fur layers (FluffyWorks style). "
                    "0 = no fur",
    )
    shell_spacing: bpy.props.FloatProperty(
        name="Shell spacing", default=0.2, min=0.01, max=2.0,
        description="Distance between fur layers in Skyrim units (0.2 = 2 mm). "
                    "Total fur length = layers x spacing",
    )
    shell_tris: bpy.props.IntProperty(
        name="Shell tris", default=3000, min=500, max=20000,
        description="Triangle budget for the mesh each fur layer is built from",
    )
    texture_size: bpy.props.EnumProperty(
        name="Texture size",
        items=[("1024", "1K", ""), ("2048", "2K", ""), ("4096", "4K", "")],
        default="2048",
        description="Resolution the diffuse and normal maps are baked at",
    )
    keep_extra_vanilla: bpy.props.BoolProperty(
        name="Keep other vanilla meshes",
        default=False,
        description="Export vanilla shapes the model does not replace (horns, eyes, armour)",
    )
    status: bpy.props.StringProperty(name="Status", default="Ready")


# --------------------------------------------------------------------------- #
# operators
# --------------------------------------------------------------------------- #

def _guard(fn):
    """Report a failed step as a clean operator message instead of a traceback.

    Blender shows uncaught exceptions as a red Python traceback dialog, which is
    unhelpful here - the cause is always something the panel can explain.
    """

    @functools.wraps(fn)
    def wrapper(self, context):
        try:
            return fn(self, context)
        except Exception as exc:
            msg = str(exc) or exc.__class__.__name__
            try:
                self.settings.status = f"FAILED: {msg}"
            except Exception:
                pass
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

    return wrapper


class _Base:
    bl_options = {"REGISTER", "UNDO"}

    def _creature(self):
        root = project_root(bpy.context)
        if not (root / "config" / "creatures.csv").is_file():
            raise RuntimeError(
                f"no config/creatures.csv under {root} - "
                "set Project root in the High Poly panel"
            )
        c = find_creature(root, self.settings.mod, self.settings.creature)
        if not c:
            raise RuntimeError(
                f"creature {self.settings.creature!r} not found for mod "
                f"{self.settings.mod!r} in config/creatures.csv"
            )
        return root, c


class HP_OT_enable_pynifly(bpy.types.Operator):
    bl_idname = "hp.enable_pynifly"
    bl_label = "Enable PyNifly"
    bl_description = "Switch on the PyNifly add-on (NIF import/export) this pipeline needs"
    bl_options = {"REGISTER"}

    @_guard
    def execute(self, context):
        if ensure_pynifly():
            self.report({"INFO"}, "PyNifly enabled - NIF import/export available")
            return {"FINISHED"}
        self.report({"ERROR"}, PNIFLY_HINT)
        return {"CANCELLED"}


class HP_OT_load_vanilla(_Base, bpy.types.Operator):
    bl_idname = "hp.load_vanilla"
    bl_label = "Load Vanilla Reference"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        root, c = self._creature()
        name = do_load_vanilla(context, c, root)
        self.settings.status = f"vanilla: {name}"
        return {"FINISHED"}


class HP_OT_import_model(_Base, bpy.types.Operator):
    bl_idname = "hp.import_model"
    bl_label = "Import Model"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.glb;*.gltf;*.blend;*.fbx;*.obj", options={"HIDDEN"})

    @property
    def settings(self):
        return bpy.context.scene.hp

    def invoke(self, context, event):
        root, c = self._creature()
        start = incoming_dir(root, c)
        if start.is_dir():
            self.filepath = str(start)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    @_guard
    def execute(self, context):
        root, c = self._creature()
        name = do_import_model(context, c, root, Path(self.filepath) if self.filepath else None)
        self.settings.status = f"model: {name}"
        return {"FINISHED"}


class HP_OT_fit(_Base, bpy.types.Operator):
    bl_idname = "hp.fit"
    bl_label = "Auto Fit"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        self.settings.status = do_fit(context, self.settings)
        return {"FINISHED"}


class HP_OT_decimate(_Base, bpy.types.Operator):
    bl_idname = "hp.decimate"
    bl_label = "Decimate"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        self.settings.status = do_decimate(context, self.settings)
        return {"FINISHED"}


class HP_OT_transfer_weights(_Base, bpy.types.Operator):
    bl_idname = "hp.transfer_weights"
    bl_label = "Transfer Weights"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        self.settings.status = do_transfer_weights(context)
        return {"FINISHED"}


class HP_OT_make_shells(_Base, bpy.types.Operator):
    bl_idname = "hp.make_shells"
    bl_label = "Build Fur Shells"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        root, c = self._creature()
        self.settings.status = do_make_shells(context, c, root, self.settings)
        return {"FINISHED"}


class HP_OT_setup_material(_Base, bpy.types.Operator):
    bl_idname = "hp.setup_material"
    bl_label = "Setup Skyrim Material"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        root, c = self._creature()
        self.settings.status = do_setup_material(context, c, root)
        return {"FINISHED"}


class HP_OT_validate(_Base, bpy.types.Operator):
    bl_idname = "hp.validate"
    bl_label = "Validate"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        self.settings.status = do_validate(context)
        return {"FINISHED"}


class HP_OT_export(_Base, bpy.types.Operator):
    bl_idname = "hp.export_nif"
    bl_label = "Export NIF"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        root, c = self._creature()
        self.settings.status = "exported: " + do_export(
            context, c, root, self.settings.keep_fur, self.settings.keep_extra_vanilla)
        return {"FINISHED"}


class HP_OT_run_all(_Base, bpy.types.Operator):
    bl_idname = "hp.run_all"
    bl_label = "Run Full Pipeline"
    bl_description = "Load vanilla, import the model, fit, decimate, rig, material, validate, export"

    @property
    def settings(self):
        return bpy.context.scene.hp

    @_guard
    def execute(self, context):
        try:
            report = run_full(context, self.settings)
        except Exception as exc:
            self.settings.status = f"FAILED: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.settings.status = report.splitlines()[-1]
        self.report({"INFO"}, "Pipeline finished")
        print("=== HP PIPELINE ===")
        print(report)
        return {"FINISHED"}


# --------------------------------------------------------------------------- #
# panel
# --------------------------------------------------------------------------- #

class HP_PT_panel(bpy.types.Panel):
    bl_label = "High Poly Creature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "High Poly"

    def draw(self, context):
        layout = self.layout
        s = context.scene.hp

        # Project root first: everything below depends on it, and it is the one
        # thing that breaks when the file is run from the Text Editor instead of
        # being installed as an add-on (no preferences entry for "__main__").
        root = None
        err = ""
        try:
            root = project_root(context)
            root_ok = (root / "config" / "creatures.csv").is_file()
        except Exception as exc:
            root_ok = False
            err = str(exc)

        box = layout.box()
        box.prop(s, "project_root", text="Project root (blank = default)")
        if root is None:
            box.label(text=f"Error: {err[:60]}", icon="ERROR")
        elif root_ok:
            box.label(text=f"using {root}", icon="CHECKMARK")
        else:
            box.label(text="no config/creatures.csv here:", icon="ERROR")
            box.label(text=str(root))

        if not pynifly_ready():
            warn = layout.box()
            warn.label(text="PyNifly not enabled - NIF import/export off", icon="ERROR")
            warn.operator("hp.enable_pynifly")

        col = layout.column(align=True)
        col.prop(s, "mod")
        col.prop(s, "creature")
        if root_ok and not any(c.mod == s.mod for c in load_creatures(root)):
            col.label(text="No creatures for this mod - check Project root", icon="ERROR")

        box = layout.box()
        box.label(text="1. Vanilla", icon="MESH_DATA")
        box.operator("hp.load_vanilla", icon="IMPORT")
        body = objects_with("vanilla_body")
        if body:
            box.label(text=mesh_stats(body[0]))
            arms = objects_with("vanilla_armature")
            if arms:
                box.label(text=f"{len(arms[0].data.bones)} bones")

        box = layout.box()
        box.label(text="2. Model", icon="MESH_MONKEY")
        box.operator("hp.import_model", icon="FILE_NEW")
        model = objects_with("model")
        if model:
            box.label(text=mesh_stats(model[0]))
        box.prop(s, "target_multiplier")
        box.prop(s, "target_tris")
        box.prop(s, "auto_orient")
        box.prop(s, "rotate_x")
        box.prop(s, "rotate_z")
        box.prop(s, "fit_mode")
        box.prop(s, "scale_multiplier")
        row = box.row(align=True)
        row.operator("hp.fit", icon="SNAP_ON")
        row.operator("hp.decimate", icon="MOD_DECIM")


        box = layout.box()
        box.label(text="3. Rig", icon="ARMATURE_DATA")
        box.operator("hp.transfer_weights", icon="GROUP_VERTEX")

        box = layout.box()
        box.label(text="4. Material", icon="MATERIAL")
        box.prop(s, "texture_size")
        box.operator("hp.setup_material", icon="TEXTURE")

        box = layout.box()
        box.label(text="5. Fur shells", icon="MOD_PARTICLES")
        box.prop(s, "shell_count")
        box.prop(s, "shell_spacing")
        box.prop(s, "shell_tris")
        box.operator("hp.make_shells", icon="MOD_EXPLODE")
        shells = objects_with("shell")
        if shells:
            box.label(text=f"{len(shells)} layers, "
                           f"fur length {len(shells) * s.shell_spacing:.2f}")

        box = layout.box()
        box.label(text="6. Export", icon="EXPORT")
        box.prop(s, "keep_fur")
        box.prop(s, "keep_extra_vanilla")
        row = box.row(align=True)
        row.operator("hp.validate", icon="CHECKMARK")
        row.operator("hp.export_nif", icon="FILE_TICK")
        box.operator("hp.run_all", icon="PLAY", emboss=True)

        layout.separator()
        layout.label(text="Status:", icon="INFO")
        for line in (s.status or "Ready").splitlines()[-3:]:
            layout.label(text=line)


# --------------------------------------------------------------------------- #
# registration
# --------------------------------------------------------------------------- #

CLASSES = (
    HPPreferences,
    HPSettings,
    HP_OT_enable_pynifly,
    HP_OT_load_vanilla,
    HP_OT_import_model,
    HP_OT_fit,
    HP_OT_decimate,
    HP_OT_transfer_weights,
    HP_OT_make_shells,
    HP_OT_setup_material,
    HP_OT_validate,
    HP_OT_export,
    HP_OT_run_all,
    HP_PT_panel,
)


def _classes():
    """AddonPreferences only resolves when this file is an installed add-on.

    Run from the Text Editor, __name__ is "__main__" and Blender would key the
    preferences to an add-on that does not exist - which is exactly the KeyError
    that used to break the panel. Everything else works either way.
    """
    if __name__ == "__main__":
        return tuple(c for c in CLASSES if c is not HPPreferences)
    return CLASSES


def register():
    for cls in _classes():
        bpy.utils.register_class(cls)
    bpy.types.Scene.hp = bpy.props.PointerProperty(type=HPSettings)


def unregister():
    if hasattr(bpy.types.Scene, "hp"):
        del bpy.types.Scene.hp
    for cls in reversed(_classes()):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
