# parens.py — build + render the wyo.town parenthesis pricklypear
#
# Usage:
#   blender -b --python brand/models/parens.py
#   blender -b --python brand/models/parens.py -- 160       one still, rotated
#   blender -b --python brand/models/parens.py -- spin 24   24 turntable frames -> .spin/
#   blender -b --python brand/models/parens.py -- sway 16   16 idle-sway frames -> .sway/
#
# Writes:
#   brand/models/parens.blend       (source file, re-editable)
#   brand/assets/model-parens.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the plant.
#
# Nopales is a Lisp, so its pricklypear is a pair of parentheses. One pad is
# one "()": two curved strokes facing each other. Each stroke is a real curve
# — a tapered tube swept along a circular arc — so a pad is round in plan and
# holds up when the model turns. Composed as the same growth tree as
# pricklypear.py: seven pads, a spine up-left, a right arm, one trailing pad.
# The ink is printed, not green: the glyph is the plant.
#
# Orientation rule that makes the glyphs read (learned the hard way):
# a "()" pair rolled IN ITS PLANE becomes two opposing arcs — crescents, not
# parens — so in-plane roll is clamped small and the old slab-model `fan`
# budget is spent on YAW (the pad turning like a paddle). A curved stroke
# seen at an angle still reads as a curved stroke.

import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

INK_L = "INK"      # the stroke, lit faces
INK_D = "TEAL"     # the stroke, shaded faces
DOT = "INK"        # areole pips
AMBER = "AMBER"    # fruit (tunas), lit
RUST = "RUST"      # fruit, shaded

SEED = 7

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "parens.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-parens.png")

# one stroke = one curved bar, swept along an arc. These are the real curve:
# a tapered elliptical tube, faceted flat like everything else in the catalog.
ARC_R = 1.00        # radius of the stroke's centerline arc
SPAN = 125.0        # degrees of arc: a paren, not a ring
STROKE_W = 0.24     # half-thickness across the curve (the stroke's weight)
STROKE_D = 0.18     # half-thickness out of plane; slimmer, so it reads flat
STROKE_TAPER = 0.38 # how much thinner the stroke gets at its two tips
ARC_SEGS = 22       # samples along the curve
RING_SEGS = 12      # sides around the stroke

# a raw "()" is wider than tall; pads want a portrait silhouette
PAD_SQUASH_X = 0.85
PAD_STRETCH_Z = 1.10

PAD_UP_R = 1.10     # the base pad's half-height, so the plant frames like the pear

# The same composition as the pricklypear: a spine climbing up-left, a strong
# right arm for counterweight, one low trailing pad to kill any symmetry. The
# slab-silhouette's seventh pad (low on the spine's shaft) is back, plus an
# eighth low on the right: lateral pads break the vertical stack, because a
# bare column of "()" pads reads as something no catalog can sell.
# phi/delta place the pad in the parent's plane (the 2D silhouette, as in
# pricklypear.py); seat is where the child's axis crosses its own half-height.
# Seats run 1.1-1.25: slabs can weld, but crossing parens read as a mistake,
# so every joint keeps a hairline gap and pads meet tip-to-tip at most. yaw turns the pad out of plane (the 3D life); roll spins the glyph
# in plane. Roll is not a styling jitter here but the growth itself: each pad
# is rolled onto its growth bearing (roll = phi+delta), so every pad offers its
# narrow side to the joint and its face outward — pads go narrow-side-out, the
# way a real pad sprouts edge-first. dy layers the
# pad in depth (+ away from camera) so overlaps read clean back-to-front
# instead of crossing coplanar strokes.
#        parent  phi  delta  scale  lean  seat    yaw   roll     dy
NODES = [
    (    -1,    0,   -5,  0.95,   2, 1.00,  +22,   -5,  0.00),  # 0 base, hero
    (     0,  -22,  -14,  0.75,   2, 1.18,  -20,  -36,  0.42),  # 1 spine, behind
    (     1,  -20,  -10,  0.55,  -3, 1.26,  -22,   -6,  0.50),  # 2 crown
    (     0,  +42,  +10,  0.62,   4, 1.20,  +16,  +60, -0.42),  # 3 right arm, front
    (     3,  +16,  -12,  0.50,   4, 1.15,  +34,   +4, -0.44),  # 4 right tip
    (     0, -100,   -5,  0.50,  -4, 1.15,  -18, -105,  0.25),  # 5 tail, low left
    (     1,  +40,   +8,  0.45,   3, 1.00,  +16,  +50, -0.46),  # 6 side, bridging the middle
    (     0,  +98,   +6,  0.50,  -4, 1.02,  +30,  +95, -0.30),  # 7 counter-tail, low right
]
# no fruit: the plant is pure type. the fruit code stays; an empty tuple
# turns the tunas off without disabling the pose/tone plumbing.
FRUIT_NODES = ()


def arc_sample(hand, t):
    """Centerline point of one stroke at parameter t in [0, 1], plus its taper
    weight. hand=+1 is "(" (bulges -X); hand=-1 is ")" (bulges +X)."""
    beta = math.radians(SPAN) / 2
    th = (math.pi - beta) + 2 * beta * t                 # pi-beta .. pi+beta
    c = Vector((hand * ARC_R * math.cos(th), 0.0, ARC_R * math.sin(th)))
    taper = 1.0 - STROKE_TAPER * abs(2 * t - 1) ** 1.4
    return c, taper


def stroke_into(verts, faces, hand):
    """Append one curved stroke to a vert/face buffer."""
    n = ARC_SEGS
    base = len(verts)
    for i in range(n + 1):
        c, taper = arc_sample(hand, i / n)
        radial = c.normalized()   # outward = bulge direction of the arc
        w = STROKE_W * taper                          # radial half-thickness
        d = STROKE_D * taper                          # out-of-plane half-thickness
        for j in range(RING_SEGS):
            a = 2 * math.pi * j / RING_SEGS
            p = c + radial * (w * math.cos(a)) + Vector((0.0, d * math.sin(a), 0.0))
            verts.append(tuple(p))
    for i in range(n):
        for j in range(RING_SEGS):
            a = base + i * RING_SEGS + j
            b = base + i * RING_SEGS + (j + 1) % RING_SEGS
            e = base + (i + 1) * RING_SEGS + (j + 1) % RING_SEGS
            f = base + (i + 1) * RING_SEGS + j
            faces.append((a, b, e, f))
    faces.append(tuple(base + RING_SEGS - 1 - j for j in range(RING_SEGS)))
    faces.append(tuple(base + n * RING_SEGS + j for j in range(RING_SEGS)))


def pad_mesh(name):
    """One pad: a "(" and a ")", built as one mesh, squashed to a portrait
    silhouette and recentred on its bbox. Returns (object, half-extents)."""
    verts, faces = [], []
    stroke_into(verts, faces, +1)
    stroke_into(verts, faces, -1)

    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                (min(zs) + max(zs)) / 2))
    verts = [tuple(Vector(v) - c) for v in verts]

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.transform(Matrix.Diagonal((PAD_SQUASH_X, 1.0, PAD_STRETCH_Z, 1.0)))
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    half = ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2,
            (max(zs) - min(zs)) / 2)
    return ob, half


# unit-pad local coords of a point on a stroke's outer face (front or back),
# for scattering areole pips — honoring the same squash/stretch the mesh got
def stroke_pt(hand, t, front=True):
    c, taper = arc_sample(hand, t)
    dy = STROKE_D * taper + 0.02
    return Vector((c.x * PAD_SQUASH_X, dy if front else -dy,
                   c.z * PAD_STRETCH_Z))


C.new_scene(seed=SEED)

m_ink = C.material("glyph-lit", INK_L)
m_ink_d = C.material("glyph-shade", INK_D)
m_dot = C.material("areole", DOT)
m_amber = C.material("fruit-lit", AMBER)
m_rust = C.material("fruit-shade", RUST)

# build one pad to learn its proportions, then scale that mesh to the plant's
# unit so a pad's scale factor is simply its generation size
prototype, half = pad_mesh("pad-proto")
UNIT = PAD_UP_R / half[2]
PAD_R = (half[0] * UNIT, half[1] * UNIT, half[2] * UNIT)
prototype.data.transform(Matrix.Diagonal((UNIT, UNIT, UNIT, 1.0)))
prototype.data.update()

pads, pivots, members = [], {}, {}
for i, row in enumerate(NODES):
    parent, phi, delta, s, lean, seat_depth, yaw, roll, dy = row
    pad = prototype.copy()
    pad.data = prototype.data.copy()
    pad.name = f"pad-{i}"
    bpy.context.scene.collection.objects.link(pad)
    members[i] = [pad]
    lean_r = math.radians(lean + random.uniform(-2, 2))
    roll_r = math.radians(roll + random.uniform(-2, 2))
    yaw_r = math.radians(yaw + random.uniform(-3, 3))
    # paddle turn, then glyph spin, then nod — applied parent-first
    local_rot = (Matrix.Rotation(yaw_r, 4, "Z")
                 @ Matrix.Rotation(roll_r, 4, "Y")
                 @ Matrix.Rotation(lean_r, 4, "X"))
    if parent < 0:
        pad.location = (0.0, 0.0, PAD_UP_R * s)
        pivots[i] = Vector((0.0, 0.0, 0.0))
        rot = local_rot
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
        c = p.matrix_world @ (seat + axis * (PAD_R[2] * s * seat_depth))
        pad.location = (c.x, c.y + dy + random.uniform(-0.05, 0.05), c.z)
        rot = p.matrix_world.to_quaternion().to_matrix().to_4x4() @ local_rot
    pad.scale = (s, s, s)
    pad.rotation_mode = "QUATERNION"
    pad.rotation_quaternion = rot.to_quaternion()
    pads.append(pad)
    bpy.context.view_layer.update()  # refresh matrix_world for children
prototype.hide_render = True
for pad in pads:
    C.two_tone(pad, m_ink, m_ink_d)

# areole pips: the pear's dots become points of punctuation, riding each
# stroke's outer face, front and back
for i, pad in enumerate(pads):
    spin = random.uniform(0.15, 0.85)                 # slide along the arc, per pad
    n = 3 if NODES[i][3] > 0.5 else 2
    for k in range(n):
        hand = 1 if (i + k) % 2 == 0 else -1
        t = spin + (k - (n - 1) / 2) * 0.22
        t = min(0.9, max(0.1, t))
        for front in (True, False):
            d = C.ico(1)
            d.name = f"areole-{i}"
            d.scale = (0.05, 0.05, 0.05)
            d.location = pad.matrix_world @ (UNIT * stroke_pt(hand, t, front))
            d.data.materials.append(m_dot)
            members[i].append(d)

# fruit (tunas) at pad tips, the only thing on the plant that is not type
fruits = []
for i in FRUIT_NODES:
    tip = pads[i].matrix_world @ Vector((0.0, 0.0, PAD_R[2]))
    f = C.ico(2)
    f.name = f"fruit-{i}"
    f.scale = (0.17, 0.15, 0.22)
    f.location = tip + Vector((0.0, 0.0, 0.06))
    C.two_tone(f, m_amber, m_rust)
    fruits.append(f)
    members[i].append(f)

# optional spin:
#   blender -b --python parens.py -- 160      one still, rotated
#   blender -b --python parens.py -- spin 24  24 turntable frames -> .spin/
#   blender -b --python parens.py -- sway 16  16 idle-sway frames -> .sway/
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TURN, SPIN, SWAY = 0.0, 0, 0
if args and args[0] == "spin":
    SPIN = int(args[1]) if len(args) > 1 else 24
elif args and args[0] == "sway":
    SWAY = int(args[1]) if len(args) > 1 else 16
elif args:
    TURN = float(args[0])

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
bpy.context.view_layer.update()        # matrices fresh before snapshot
base = {o: o.matrix_world.copy() for o in meshes}


def tone():
    for pad in pads:
        C.two_tone(pad, m_ink, m_ink_d)
    for f in fruits:
        C.two_tone(f, m_amber, m_rust)


def pose(angle):
    """Rotate the whole plant to `angle` deg around Z; light stays world-fixed."""
    R = Matrix.Rotation(math.radians(angle), 4, "Z")
    for o in meshes:
        o.matrix_world = R @ base[o]
    bpy.context.view_layer.update()
    tone()


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
        tone()
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
