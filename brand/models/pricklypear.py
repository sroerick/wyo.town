# pricklypear.py — build + render the wyo.town low-poly prickly pear
#
# Usage:
#   blender -b --python brand/models/pricklypear.py
#
# Writes:
#   brand/models/pricklypear.blend       (source file, re-editable)
#   brand/assets/model-pricklypear.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the cactus.

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# tile-specific colors (from tile-pricklypear.svg); inks come from C.INKS
GREEN = "#4E8C4A"    # pad, lit faces
GREEN_D = "#2C4A28"  # pad, shaded faces
DOT = "#E8F2D0"     # areole dots

SEED = 7

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "pricklypear.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-pricklypear.png")

# one unit ellipsoid = one pad; x width, y thickness, z height
PAD_R = (0.95, 0.30, 1.10)
TAPER = 0.28                  # egg shape: base of each pad narrows by this much

# Composition is a growth tree: each pad sprouts from a bearing on its
# parent's edge (phi), deflects to its own axis (delta), shrinks per
# generation, and buries a set depth into the joint (seat). Weight stays
# centered but nothing mirrors.
#
# Seven pads, one gesture: a spine climbing up-left, a strong right arm for
# counterweight, one low trailing pad to kill any symmetry. 1 hero + 3 medium
# + 3 small; size contrast does the composition work.
#        parent  phi  delta  scale  leanX  seat
NODES = [
    (    -1,    0,   -5,  0.95,   3, 1.00),   # 0 base, the hero pad
    (     0,    0,  -12,  0.75,   2, 0.86),   # 1 spine, welded to the base
    (     1,  -12,   -8,  0.55,  -3, 0.90),   # 2 crown, continues it, fruit
    (     0,  +45,  +12,  0.62,   5, 0.90),   # 3 right arm, the counterweight
    (     3,  +10,  -18,  0.45,   4, 0.96),   # 4 right tip, fruit
    (     0, -100,   -5,  0.50,  -4, 0.90),   # 5 tail, low and horizontal left
    (     1,  +70,  +10,  0.45,   3, 0.90),   # 6 side pad low on the spine's shaft
]
FRUIT_NODES = (2, 4)          # crown tip + right tip: diagonal, never mirrored

C.new_scene(seed=SEED)

m_green = C.material("pad-lit", GREEN)
m_green_d = C.material("pad-shade", GREEN_D)
m_dot = C.material("areole", DOT)
m_amber = C.material("fruit-lit", "AMBER")
m_rust = C.material("fruit-shade", "RUST")

pads, fans, pivots, members = [], [], {}, {}
for i, row in enumerate(NODES):
    parent, phi, delta, s, lean = row[:5]
    pad = C.ico(2)
    pad.name = f"pad-{i}"
    # taper the base so it reads as a pad, not a pebble
    for v in pad.data.vertices:
        if v.co.z < 0:
            w = 1.0 + TAPER * v.co.z
            v.co.x *= w
            v.co.y *= w
    rx, ry, rz = (PAD_R[j] * s for j in range(3))
    members[i] = [pad]
    if parent < 0:
        pad.location = (0.0, 0.0, 1.0)
        pivots[i] = Vector((0.0, 0.0, 0.0))
        fan = math.radians(delta)
    else:
        p = pads[parent]
        ps = NODES[parent][3]
        rxp, rzp = PAD_R[0] * ps, PAD_R[2] * ps
        a = math.radians(phi)
        t = 1.0 / math.hypot(math.sin(a) / rxp, math.cos(a) / rzp)
        seat = Vector((math.sin(a) * t, 0.0, math.cos(a) * t))
        ax = math.radians(phi + delta)
        axis = Vector((math.sin(ax), 0.0, math.cos(ax)))
        pivots[i] = p.matrix_world @ seat  # joint point, for sway animation
        c = p.matrix_world @ (seat + axis * (rz * row[5]))
        pad.location = (c.x, c.y + random.uniform(-0.08, 0.08), c.z)
        fan = fans[parent] + ax
    pad.scale = (rx, ry, rz)
    pad.rotation_euler = (math.radians(lean + random.uniform(-3, 3)), fan, 0.0)
    fans.append(fan)
    pads.append(pad)
    bpy.context.view_layer.update()  # refresh matrix_world for children
for pad in pads:
    C.two_tone(pad, m_green, m_green_d)

# areole dots: seeded per pad, so no two pads carry the same scatter
for i, pad in enumerate(pads):
    spin = random.uniform(0, math.pi)
    sn, cs = math.sin(spin), math.cos(spin)
    for fx, fz in ((0.40, 0.32), (-0.32, 0.02), (0.10, 0.60))[:3 if NODES[i][3] > 0.5 else 2]:
        fx, fz = fx * cs + fz * sn, fz * cs - fx * sn  # rotate scatter per pad
        # unit-sphere local coords; matrix_world applies the pad's own scale
        y = -math.sqrt(max(0.0, 1 - fx * fx - fz * fz)) - 0.06
        d = C.ico(1)
        d.name = f"areole-{i}"
        d.scale = (0.05, 0.05, 0.05)
        d.location = pad.matrix_world @ Vector((fx, y, fz))
        d.data.materials.append(m_dot)
        members[i].append(d)

# fruit (tunas) at pad tips
fruits = []
for i in FRUIT_NODES:
    tip = pads[i].matrix_world @ Vector((0.0, 0.0, 1.02))
    f = C.ico(2)
    f.name = f"fruit-{i}"
    f.scale = (0.17, 0.15, 0.22)
    f.location = tip + Vector((0.0, 0.0, 0.06))
    C.two_tone(f, m_amber, m_rust)
    fruits.append(f)
    members[i].append(f)

# optional spin:
#   blender -b --python pricklypear.py -- 160      one still, rotated
#   blender -b --python pricklypear.py -- spin 24  24 turntable frames -> .spin/
#   blender -b --python pricklypear.py -- sway 16  16 idle-sway frames -> .sway/
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TURN, SPIN, SWAY = 0.0, 0, 0
if args and args[0] == "spin":
    SPIN = int(args[1]) if len(args) > 1 else 24
elif args and args[0] == "sway":
    SWAY = int(args[1]) if len(args) > 1 else 16
elif args:
    TURN = float(args[0])

from mathutils import Matrix

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.context.view_layer.update()        # matrices fresh before snapshot
base = {o: o.matrix_world.copy() for o in meshes}


def pose(angle):
    """Rotate the whole plant to `angle` deg around Z; light stays world-fixed."""
    R = Matrix.Rotation(math.radians(angle), 4, "Z")
    for o in meshes:
        o.matrix_world = R @ base[o]
    bpy.context.view_layer.update()
    for pad in pads:
        C.two_tone(pad, m_green, m_green_d)
    for f in fruits:
        C.two_tone(f, m_amber, m_rust)


pose(TURN)
if TURN:
    stem, dot = os.path.splitext(PNG_OUT)
    PNG_OUT = f"{stem}-{int(TURN)}{dot}"

C.finish(BLEND_OUT, PNG_OUT, frame=meshes)

if SWAY:
    # each pad pivots a couple degrees around its own joint; sine over the
    # frame count closes the loop. Root barely moves; outer pads move most.
    rng = random.Random(SEED + 1000)
    sway = {}
    for i in range(len(pads)):
        depth = 0
        j = i
        while NODES[j][0] >= 0:
            depth += 1
            j = NODES[j][0]
        amp = math.radians(rng.uniform(0.8, 2.2)) * (0.25 + 0.35 * depth)
        ax = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0)).normalized()
        sway[i] = (rng.uniform(0, 2 * math.pi), ax, amp)
    owner = {o: i for i, grp in members.items() for o in grp}

    sway_dir = os.path.join(HERE, ".sway")
    os.makedirs(sway_dir, exist_ok=True)
    for k in range(SWAY):
        t = 2 * math.pi * k / SWAY
        for o in meshes:
            ph, ax, amp = sway[owner[o]]
            R = Matrix.Rotation(amp * math.sin(t + ph), 4, ax)
            P = pivots[owner[o]]
            o.matrix_world = Matrix.Translation(P) @ R @ Matrix.Translation(-P) @ base[o]
        bpy.context.view_layer.update()
        for pad in pads:
            C.two_tone(pad, m_green, m_green_d)
        for f in fruits:
            C.two_tone(f, m_amber, m_rust)
        bpy.context.scene.render.filepath = os.path.join(sway_dir, f"frame-{k:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"WROTE {SWAY} frames to {sway_dir}")

if SPIN:
    spin_dir = os.path.join(HERE, ".spin")
    os.makedirs(spin_dir, exist_ok=True)
    for k in range(SPIN):
        pose(360.0 * k / SPIN)
        bpy.context.scene.render.filepath = os.path.join(spin_dir, f"frame-{k:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"WROTE {SPIN} frames to {spin_dir}")
