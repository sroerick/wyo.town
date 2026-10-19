# _common.py — shared build+render machinery for wyo.town brand models
#
# The brand treatment every model gets (see brand/BRAND.md):
#   palette-only colors, two flat tones per mesh split per-face by world
#   normal (no lights, no gradients), orthographic product-shot camera
#   auto-framed on the geometry, fixed-size Workbench FLAT render.
#
# A model script is only its geometry builder:
#
#   import _common as C
#   C.new_scene(seed=7)
#   green = C.material("pad", "#4E8C4A")
#   ... build meshes, C.two_tone(ob, lit, dark) ...
#   C.finish("model.blend", "model.png", frame=my_objects)

import math
import os
import random

import bpy
from mathutils import Vector

# ---------------------------------------------------------------- palette

# the 16 brand inks, by number and name (BRAND.md, "Ink")
INKS = {
    "INK": "#101418", "SNOW": "#F6F5F0", "STOCK": "#EAD2A0", "CHROME": "#BFBFBF",
    "RUST": "#AA3311", "AMBER": "#FFB300", "SUNSET": "#FF7A45", "PINK": "#FF3EA5",
    "MAGENTA": "#AA00AA", "PLUM": "#7A1FA2", "AZURE": "#1E6BFF", "SKY": "#88CCEE",
    "AQUA": "#00C2C7", "LIME": "#C8F24E", "TEAL": "#0B5D6B", "TERRITORIAL": "#002F6C",
}

FIELD = INKS["STOCK"]  # default render field

# one fixed light direction; faces turn toward it (lit) or away (shade)
LIGHT = Vector((0.35, -0.65, 0.67)).normalized()


def rgba(hex_color):
    """sRGB hex -> scene-linear RGBA, so flat colors hit the exact ink."""

    def s2l(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return tuple(s2l(int(hex_color[i:i + 2], 16)) for i in (1, 3, 5)) + (1.0,)


def material(name, hex_color):
    """A flat color material; hex may be a brand ink name or literal '#rrggbb'."""
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba(INKS.get(hex_color, hex_color))
    return m


# ---------------------------------------------------------------- geometry

def new_scene(seed=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if seed is not None:
        random.seed(seed)


def ico(subdiv=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0)
    return bpy.context.active_object


def two_tone(ob, lit, dark, thresh=0.12):
    """Assign lit/dark material per face from the world-space normal."""
    me = ob.data
    me.materials.append(lit)
    me.materials.append(dark)
    nm = ob.matrix_world.to_3x3().inverted().transposed()
    for p in me.polygons:
        n = (nm @ p.normal).normalized()
        p.material_index = 0 if n.dot(LIGHT) > thresh else 1


# ---------------------------------------------------------------- render

def finish(blend_path, png_path, frame, field=FIELD, res=512,
           cam_offset=(2.0, -10.0, 0.8), transparent=True):
    """Camera + Workbench setup, auto-framed on `frame` objects; save + render."""
    bpy.context.view_layer.update()

    xs, zs = [], []
    for ob in frame:
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            xs.append(w.x)
            zs.append(w.z)
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)

    target = Vector(((x0 + x1) / 2, 0.0, (z0 + z1) / 2))
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(x1 - x0, z1 - z0) * 1.14
    cam_ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(cam_ob)
    cam_ob.location = target + Vector(cam_offset)  # slight 3/4
    cam_ob.rotation_euler = (target - cam_ob.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam_ob

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"            # no lighting, no gradient
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.background_type = "VIEWPORT"
    # viewport background is display-space: use raw sRGB, not the linear rgba(),
    # or the display transform double-converts the field ink to gray
    sc.display.shading.background_color = tuple(int(field[i:i + 2], 16) / 255 for i in (1, 3, 5))
    sc.render.film_transparent = transparent
    try:
        sc.display.render_aa = "OFF"             # keep edges crisp
    except TypeError:
        pass
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.render.filepath = png_path

    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.render.render(write_still=True)

    print(f"WROTE {blend_path}")
    print(f"WROTE {png_path}")
