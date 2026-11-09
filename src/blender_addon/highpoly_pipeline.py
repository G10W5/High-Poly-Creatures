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
    return path.name


def do_fit(context, settings) -> str:
    body = objects_with("vanilla_body")
    model = objects_with("model")
    if not body or not model:
        raise RuntimeError("load the vanilla reference and a model first")
    body, model = body[0], model[0]

    model.rotation_euler = (
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
    apply_transform(model, location=True)

    mlo, mhi = world_bbox(model)
    md = mhi - mlo
    return f"scale {scale:.2f}, dims {md.x:.2f} x {md.y:.2f} x {md.z:.2f}{axes}"


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
    return f"material {mat.name}, textures: {', '.join(saved)}"


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

    work = incoming_dir(root, creature).parent / "work"
    work.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(work / f"{creature.name}.blend"))
    return str(out.relative_to(root))


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
    log.append("validate: " + do_validate(context))
    log.append("export: " + do_export(
        context, creature, root, settings.keep_fur, settings.keep_extra_vanilla))
    return "\n".join(log)


# --------------------------------------------------------------------------- #
# properties
# --------------------------------------------------------------------------- #

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
    rotate_x: bpy.props.FloatProperty(name="Rotate X", default=-90.0)
    rotate_z: bpy.props.FloatProperty(name="Rotate Z", default=0.0)
    scale_multiplier: bpy.props.FloatProperty(name="Scale", default=1.0, min=0.01)
    fit_mode: bpy.props.EnumProperty(
        name="Fit",
        items=[
            ("AXIS", "Match vanilla silhouette",
             "Scale each axis to the vanilla bounding box - fits animations and doorframes"),
            ("UNIFORM", "Keep model proportions",
             "One scale factor on all axes - the model keeps its own shape"),
        ],
        default="AXIS",
    )
    keep_fur: bpy.props.BoolProperty(
        name="Keep vanilla fur shell",
        default=True,
        description="Export the vanilla Fur shell shape alongside the new body",
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
        box.label(text="5. Export", icon="EXPORT")
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
