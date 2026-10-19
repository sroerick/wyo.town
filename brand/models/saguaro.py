# saguaro.py — build + render the wyo.town low-poly saguaro
#
# Usage:
#   blender -b --python brand/models/saguaro.py
#   blender -b --python brand/models/saguaro.py -- 160       one still, rotated
#   blender -b --python brand/models/saguaro.py -- spin 24   24 turntable frames -> .spin/
#
# Writes:
#   brand/models/saguaro.blend       (source file, re-editable)
#   brand/assets/model-saguaro.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the cactus.
#
# A saguaro is made of two things: columns and patience. A hundred years to
# the first arm. Here it is a trunk and two arms, skinned from rings along a
# path, pleated like the real accordion — eight ribs, sixteen vertices.

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# tile-specific greens with SNOW blooms, the way tile-pricklypear did it
GREEN = "#5A9448"    # column, lit faces
GREEN_D = "#2E4E2A"  # column, shaded faces
BLOOM_L = "SNOW"     # saguaro flowers are white
BLOOM_D = "SKY"      # their shaded side tips blue

SEED = 7
SIDES = 16           # 16 vertices = 8 ribs
RIB = 0.82           # alternating ring radius; the accordion pleat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "saguaro.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-saguaro.png")

C.new_scene(seed=SEED)

m_green = C.material("column-lit", GREEN)
m_green_d = C.material("column-shade", GREEN_D)
m_bloom_l = C.material("bloom-lit", BLOOM_L)
m_bloom_d = C.material("bloom-shade", BLOOM_D)
m_spine_l = C.material("spine-lit", "STOCK")   # spines bleach in the sun
m_spine_d = C.material("spine-shade", "CHROME")

meshes = []


def tube(pts, radii, name, sides=SIDES):
    """Skin a ribbed column along a path: ring per point, ring vertices
    alternating radius so the column reads pleated. Hard edges, ngon caps."""
    n = len(pts)
    verts, faces = [], []
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = ((pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])).normalized()
        u = t.cross(Vector((0, 1, 0))).normalized()
        v = t.cross(u).normalized()
        for j in range(sides):
            a = 2 * math.pi * j / sides
            rm = r * (1.0 if j % 2 == 0 else RIB)
            verts.append(tuple(p + rm * (u * math.cos(a) + v * math.sin(a))))
    for i in range(n - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple((n - 1) * sides + j for j in range(sides)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# the trunk: a slight foot, a long straight climb, a domed crown.
# radius per ring carries the whole profile.
TRUNK_PTS = [
    Vector((0, 0, 0.00)), Vector((0, 0, 0.25)), Vector((0, 0, 1.70)),
    Vector((0, 0, 3.60)), Vector((0, 0, 4.15)),
    # dome
    Vector((0, 0, 4.36)), Vector((0, 0, 4.47)), Vector((0, 0, 4.53)),
]
TRUNK_R = [0.50, 0.54, 0.50, 0.44, 0.42, 0.32, 0.19, 0.04]
trunk = tube(TRUNK_PTS, TRUNK_R, "trunk")
meshes.append(trunk)

# two arms, out then up. Nothing mirrors: the right arm leaves low and short,
# the left leaves high and climbs past it. Each path starts buried in the
# trunk so the joint is a seat, not a seam.
# arms are nearly trunk-thick at the seat; that thickness is the whole
# difference between a saguaro and a saguaro drawn from memory
ARM_R = [0.30, 0.30, 0.29, 0.27, 0.25, 0.17, 0.05]
ARM_RIGHT = [
    Vector((0.24, 0, 1.70)), Vector((0.52, 0, 1.74)), Vector((0.74, 0, 1.92)),
    Vector((0.86, 0, 2.25)), Vector((0.88, 0, 2.62)),
    Vector((0.88, 0, 2.88)), Vector((0.88, 0, 2.96)),
]
ARM_LEFT = [
    Vector((-0.27, 0, 2.35)), Vector((-0.68, 0, 2.40)), Vector((-1.00, 0, 2.68)),
    Vector((-1.17, 0, 3.10)), Vector((-1.20, 0, 3.70)),
    Vector((-1.20, 0, 3.98)), Vector((-1.20, 0, 4.06)),
]
arms = [tube(ARM_RIGHT, ARM_R, "arm-right"), tube(ARM_LEFT, ARM_R, "arm-left")]
meshes += arms

# the blooms: white, always at the very tips, always out of season somewhere
# each bloom sits proud of its dome, tipped a touch toward the camera
BLOOM_TIPS = [TRUNK_PTS[-1] + Vector((0, -0.08, 0.09)),
              ARM_RIGHT[-1] + Vector((0, -0.08, 0.09)),
              ARM_LEFT[-1] + Vector((0, -0.08, 0.09))]
for i, tip in enumerate(BLOOM_TIPS):
    b = C.ico(1)
    b.name = f"bloom-{i}"
    b.scale = (0.12, 0.12, 0.12)
    b.location = tip
    meshes.append(b)

bpy.context.view_layer.update()

# the spines: on a real saguaro they read as pale lines running down the
# ribs, so that's what these are — a thin streak laid along each crest,
# segment by segment, just proud of the green
def spines(pts, radii, prefix):
    n = 0
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        t = (p1 - p0).normalized()
        u = t.cross(Vector((0, 1, 0))).normalized()
        v = t.cross(u).normalized()
        length = min((p1 - p0).length * 0.55, 0.30)
        p = p0.lerp(p1, 0.5)
        r = (radii[i] + radii[i + 1]) / 2
        for k in range(SIDES // 2):
            a = 2 * math.pi * (2 * k) / SIDES
            d = (u * math.cos(a) + v * math.sin(a)).normalized()
            x = d.cross(t).normalized()
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            s = bpy.context.active_object
            s.name = f"spine-{prefix}-{n}"
            R = Matrix((x, d, t)).transposed().to_4x4()
            s.matrix_world = (Matrix.Translation(p + d * (r + 0.005)) @ R
                              @ Matrix.Diagonal((0.03, 0.022, length, 1.0)))
            meshes.append(s)
            n += 1

spines(TRUNK_PTS, TRUNK_R, "trunk")
spines(ARM_RIGHT, ARM_R, "right")
spines(ARM_LEFT, ARM_R, "left")

bpy.context.view_layer.update()

# two tones, per face, against the fixed light — no lamps
def tone():
    for ob in meshes:
        if ob.name.startswith("bloom"):
            C.two_tone(ob, m_bloom_l, m_bloom_d)
        elif ob.name.startswith("spine"):
            C.two_tone(ob, m_spine_l, m_spine_d)
        else:
            C.two_tone(ob, m_green, m_green_d)

tone()

# membership: which column each mesh rides with in the wind
col = {}
for o in meshes:
    if o.name.startswith(("arm-right", "bloom-1", "spine-right")):
        col[o] = 1
    elif o.name.startswith(("arm-left", "bloom-2", "spine-left")):
        col[o] = 2
    else:
        col[o] = 0
PIVOTS = [Vector((0, 0, 0)), ARM_RIGHT[0].copy(), ARM_LEFT[0].copy()]

# optional spin / turn / sway
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TURN, SPIN, SWAY = 0.0, 0, 0
if args and args[0] == "spin":
    SPIN = int(args[1]) if len(args) > 1 else 24
elif args and args[0] == "sway":
    SWAY = int(args[1]) if len(args) > 1 else 16
elif args:
    TURN = float(args[0])

from mathutils import Matrix

base = {o: o.matrix_world.copy() for o in meshes}


def pose(angle):
    """Rotate the whole plant to `angle` deg around Z; light stays world-fixed."""
    Rz = Matrix.Rotation(math.radians(angle), 4, "Z")
    for o in meshes:
        o.matrix_world = Rz @ base[o]
    bpy.context.view_layer.update()
    tone()


pose(TURN)
if TURN:
    stem, dot = os.path.splitext(PNG_OUT)
    PNG_OUT = f"{stem}-{int(TURN)}{dot}"

C.finish(BLEND_OUT, PNG_OUT, frame=meshes)

if SWAY:
    # a tiny wind, no more: THE wind — axis and phase lifted from the
    # pricklypear's root pad, so the two plants ride one gust in the
    # masthead. The plant rocks around its foot; the arms go a touch harder.
    GUST_AX = Vector((0.9545323, 0.2981075, 0.0))
    GUST_PH = 5.57324400474959
    gust = {0: (GUST_PH, GUST_AX, math.radians(0.50)),
            1: (GUST_PH, GUST_AX, math.radians(0.85)),
            2: (GUST_PH, GUST_AX, math.radians(1.10))}

    sway_dir = os.path.join(HERE, ".sway")
    os.makedirs(sway_dir, exist_ok=True)
    for k in range(SWAY):
        t = 2 * math.pi * k / SWAY
        rots = {}
        for g, (ph, ax, amp) in gust.items():
            R = Matrix.Rotation(amp * math.sin(t + ph), 4, ax)
            P = PIVOTS[g]
            rots[g] = Matrix.Translation(P) @ R @ Matrix.Translation(-P)
        for o in meshes:
            g = col[o]
            o.matrix_world = rots[0] @ rots[g] @ base[o]
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
