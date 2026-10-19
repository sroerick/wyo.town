# tuna.py — build + render the wyo.town low-poly can of tuna
#
# Usage:
#   blender -b --python brand/models/tuna.py
#   blender -b --python brand/models/tuna.py -- 160     one still, rotated
#   blender -b --python brand/models/tuna.py -- spin 24  24 turntable frames -> .spin/
#
# Writes:
#   brand/models/tuna.blend       (source file, re-editable)
#   brand/assets/model-tuna.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the can.
#
# The joke is the object: a squat steel can, a pink paper label, an amber
# ring pull. The medium is 1984, so the can has sixteen sides and hard edges.

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# the can is metal + the fruit inks; the pull is the brand's own accent
METAL_L = "CHROME"     # steel, lit faces
METAL_D = "TEAL"       # steel, shaded faces — INK read as holes in the rim
LABEL_L = "PINK"       # the paper wrapper, lit
LABEL_D = "MAGENTA"    # the paper wrapper, shaded
PULL_L = "AMBER"       # the ring pull, lit
PULL_D = "RUST"        # the ring pull, shaded
WORD_L = "STOCK"       # the printed word, lit — ink on the pink paper
WORD_D = "MAGENTA"     # the printed word, shaded

SEED = 7

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "tuna.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-tuna.png")

# a tuna can is squat, but only about two to one across to tall
R = 1.00        # body radius
H = 0.90        # body height
SIDES = 16      # the period's polygon budget
LID_R = 0.94    # recessed lid, so the rim reads as a rolled edge
LID_T = 0.045

C.new_scene(seed=SEED)

m_metal_l = C.material("metal-lit", METAL_L)
m_metal_d = C.material("metal-shade", METAL_D)
m_label_l = C.material("label-lit", LABEL_L)
m_label_d = C.material("label-shade", LABEL_D)
m_pull_l = C.material("pull-lit", PULL_L)
m_pull_d = C.material("pull-shade", PULL_D)
m_word_l = C.material("word-lit", WORD_L)
m_word_d = C.material("word-shade", WORD_D)


def cylinder(radius, depth, name, verts=SIDES, cap="NOTHING"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, end_fill_type=cap)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def torus(major, minor, name, major_seg=SIDES, minor_seg=6):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=major_seg, minor_segments=minor_seg)
    ob = bpy.context.active_object
    ob.name = name
    return ob


meshes = []

# the wall: open cylinder, capped by the rims and lids
wall = cylinder(R, H, "wall")
meshes.append(wall)

# the paper label: a band just proud of the wall, most of the visible face
label = cylinder(R + 0.02, H * 0.72, "label")
meshes.append(label)

# the rolled rims top and bottom
for z, nm in ((H / 2, "rim-top"), (-H / 2, "rim-bot")):
    rim = torus(R - 0.02, 0.065, nm)
    rim.location = (0.0, 0.0, z)
    meshes.append(rim)

# the recessed lids, sitting just inside the rims
for z, nm in ((H / 2 - LID_T / 2, "lid-top"), (-H / 2 + LID_T / 2, "lid-bot")):
    lid = cylinder(LID_R, LID_T, nm, cap="NGON")
    lid.location = (0.0, 0.0, z)
    meshes.append(lid)

# the ring pull: elongated, riveted at the front, back edge lifted off the lid
pull = torus(0.17, 0.035, "pull", major_seg=12, minor_seg=6)
pull.scale = (1.5, 0.85, 1.0)
pull.location = (0.46, 0.0, H / 2 + 0.05)
pull.rotation_euler = (0.0, 0.22, 0.0)
meshes.append(pull)

# the rivet tab pinning the ring's front end to the lid
bpy.ops.mesh.primitive_cube_add(size=1.0)
tab = bpy.context.active_object
tab.name = "tab"
tab.scale = (0.18, 0.09, 0.02)
tab.location = (0.20, 0.0, H / 2 + 0.015)
meshes.append(tab)

# the printed word: PLACARD (Chicago Kare) bent onto the paper label
FONT = os.path.join(ROOT, "brand", "fonts", "chicago-kare.woff2")
word_font = bpy.data.fonts.load(FONT)
word_curve = bpy.data.curves.new("word", "FONT")
word_curve.body = "TUNA"
word_curve.font = word_font
word_curve.align_x = "CENTER"
word_curve.align_y = "CENTER"
word_curve.size = 0.36
word_curve.extrude = 0.012
word = bpy.data.objects.new("word", word_curve)
bpy.context.scene.collection.objects.link(word)
bpy.context.view_layer.objects.active = word
word.select_set(True)
bpy.ops.object.convert(target="MESH")
bpy.context.view_layer.update()

# wrap the flat mesh around the label: local x sweeps the arc, local z is relief
R_WORD = R + 0.035
for v in word.data.vertices:
    x, y, z = v.co
    phi = x / R_WORD
    r = R_WORD + z
    v.co = (r * math.sin(phi), -r * math.cos(phi), y)
word.data.update()
meshes.append(word)

bpy.context.view_layer.update()

# two tones, per face, against the fixed light — no lamps
def tone():
    for ob in meshes:
        if ob is label:
            C.two_tone(ob, m_label_l, m_label_d)
        elif ob is word:
            C.two_tone(ob, m_word_l, m_word_d)
        elif ob is pull or ob is tab:
            C.two_tone(ob, m_pull_l, m_pull_d)
        else:
            C.two_tone(ob, m_metal_l, m_metal_d)

tone()

# optional spin / turn
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TURN, SPIN = 0.0, 0
if args and args[0] == "spin":
    SPIN = int(args[1]) if len(args) > 1 else 24
elif args:
    TURN = float(args[0])

from mathutils import Matrix

base = {o: o.matrix_world.copy() for o in meshes}


def pose(angle):
    """Rotate the whole can to `angle` deg around Z; light stays world-fixed."""
    Rz = Matrix.Rotation(math.radians(angle), 4, "Z")
    for o in meshes:
        o.matrix_world = Rz @ base[o]
    bpy.context.view_layer.update()
    tone()


pose(TURN)
if TURN:
    stem, dot = os.path.splitext(PNG_OUT)
    PNG_OUT = f"{stem}-{int(TURN)}{dot}"

# a high three-quarter angle, so the lid and the ring pull actually read
C.finish(BLEND_OUT, PNG_OUT, frame=meshes, cam_offset=(2.0, -10.0, 2.6))

if SPIN:
    spin_dir = os.path.join(HERE, ".spin")
    os.makedirs(spin_dir, exist_ok=True)
    for k in range(SPIN):
        pose(360.0 * k / SPIN)
        bpy.context.scene.render.filepath = os.path.join(spin_dir, f"frame-{k:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"WROTE {SPIN} frames to {spin_dir}")
