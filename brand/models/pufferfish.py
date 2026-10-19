# pufferfish.py — build + render the wyo.town low-poly pufferfish cactus
#
# Puffy, the OpenBSD pufferfish, naturalized to the desert. The body is a
# barrel cactus in brand green, the fish's spikes are cactus spines, the
# fins and tail are pricklypear pads, and he keeps the big eyes and the
# grin. One flower, because he is happy where he landed.
#
# Usage:
#   blender -b --python brand/models/pufferfish.py
#   blender -b --python brand/models/pufferfish.py -- 160     one still, rotated
#   blender -b --python brand/models/pufferfish.py -- spin 24  24 turntable frames -> .spin/
#
# Writes:
#   brand/models/pufferfish.blend       (source file, re-editable)
#   brand/assets/model-pufferfish.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the fish.

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# cactus greens come from the pricklypear tile; everything else is an ink
GREEN = "#4E8C4A"    # body and fins, lit faces
GREEN_D = "#2C4A28"  # body and fins, shaded faces
SPINE_L = "SNOW"     # spines, lit
SPINE_D = "STOCK"    # spines, shaded
EYE = "SNOW"         # eyeballs
PUPIL = "INK"        # pupils and the grin
PETAL_L = "PINK"     # flower petals, lit
PETAL_D = "MAGENTA"  # flower petals, shaded
CORE_L = "AMBER"     # flower core, lit
CORE_D = "RUST"      # flower core, shaded

SEED = 11

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "pufferfish.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-pufferfish.png")

# the body: a plump barrel, slightly taller than deep (he floats belly down)
R_BODY = (1.00, 0.92, 1.05)
BODY_Z = 1.10           # raised so the spin clears the frame's low edge
FACE = Vector((0.16, -1.0, 0.10)).normalized()  # his look, slightly to camera

# spine field: fibonacci scatter, thinned at the face so the grin reads
N_SPINES = 72
SPINE_LEN = (0.30, 0.52)   # short near the belly, long up top

C.new_scene(seed=SEED)

m_green = C.material("skin-lit", GREEN)
m_green_d = C.material("skin-shade", GREEN_D)
m_spine_l = C.material("spine-lit", SPINE_L)
m_spine_d = C.material("spine-shade", SPINE_D)
m_eye = C.material("eye", EYE)
m_pupil = C.material("pupil", PUPIL)
m_petal_l = C.material("petal-lit", PETAL_L)
m_petal_d = C.material("petal-shade", PETAL_D)
m_core_l = C.material("core-lit", CORE_L)
m_core_d = C.material("core-shade", CORE_D)

meshes, greens, spines, petals, cores = [], [], [], [], []


def surface(p):
    """Unit-sphere direction -> world point on the body ellipsoid."""
    return Vector((p.x * R_BODY[0], p.y * R_BODY[1], p.z * R_BODY[2] + BODY_Z))


def normal(p):
    """Unit-sphere direction -> world normal of the body ellipsoid."""
    return Vector((p.x / R_BODY[0], p.y / R_BODY[1], p.z / R_BODY[2])).normalized()


# ---------------------------------------------------------------- body

body = C.ico(3)
body.name = "body"
body.scale = R_BODY
body.location = (0.0, 0.0, BODY_Z)
# barrel ribs: pinch the sphere at 8 longitudes so it reads as a cactus
for v in body.data.vertices:
    a = math.atan2(v.co.y, v.co.x)
    pinch = 1.0 - 0.045 * (0.5 - 0.5 * math.cos(a * 8))
    v.co.x *= pinch
    v.co.y *= pinch
meshes.append(body)
greens.append(body)

# ---------------------------------------------------------------- spines

GA = math.pi * (3.0 - math.sqrt(5.0))      # golden angle
for i in range(N_SPINES):
    z = 1.0 - 2.0 * (i + 0.5) / N_SPINES
    r = math.sqrt(max(0.0, 1.0 - z * z))
    a = i * GA
    p = Vector((r * math.cos(a), r * math.sin(a), z))
    if p.dot(FACE) > 0.55:                 # keep the face clear
        continue
    n = normal(p)
    length = random.uniform(*SPINE_LEN)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.055, radius2=0.0,
                                    depth=length)
    sp = bpy.context.active_object
    sp.name = f"spine-{i}"
    sp.rotation_mode = "QUATERNION"
    sp.rotation_quaternion = n.to_track_quat("Z", "Y")
    sp.location = surface(p) + n * (length * 0.32)
    meshes.append(sp)
    spines.append(sp)

# ---------------------------------------------------------------- fins & tail
# pricklypear pads standing in for fins: tapered ellipsoids, in the skin inks

def pad(name, loc, scale, rot):
    ob = C.ico(2)
    ob.name = name
    for v in ob.data.vertices:
        if v.co.z < 0:
            w = 1.0 + 0.28 * v.co.z
            v.co.x *= w
            v.co.y *= w
    ob.scale = scale
    ob.location = loc
    ob.rotation_euler = rot
    meshes.append(ob)
    greens.append(ob)
    return ob

# pectoral fins, low and swept back like little wings, nowhere near the ears
pad("fin-left", (-1.02, 0.24, 0.78), (0.44, 0.17, 0.60),
    (math.radians(14), math.radians(46), math.radians(58)))
pad("fin-right", (1.02, 0.24, 0.78), (0.44, 0.17, 0.60),
    (math.radians(-14), math.radians(-46), math.radians(-58)))
# tail: one pad held vertical in the wind, scraping the +Y horizon
pad("tail", (0.0, 1.05, 1.30), (0.34, 0.16, 0.55),
    (math.radians(90), 0.0, 0.0))

# ---------------------------------------------------------------- face

def surface_at(p, lift=0.0):
    n = normal(p)
    return surface(p) + n * lift

# eyes: snow bulbs with ink pupils, set close and high; pupils tucked a
# hair toward the nose and up to the light, so he reads keen, not startled
for side in (-1, 1):
    p = Vector((0.23 * side, -0.90, 0.40)).normalized()
    eye = C.ico(2)
    eye.name = f"eye-{side}"
    eye.scale = (0.148, 0.148, 0.148)
    eye.location = surface_at(p, 0.05)
    eye.data.materials.append(m_eye)
    meshes.append(eye)
    pupil = C.ico(1)
    pupil.name = f"pupil-{side}"
    pupil.scale = (0.092, 0.092, 0.092)
    pupil.location = (surface_at(p, 0.16) + FACE * 0.07
                      + Vector((-0.030 * side, 0.0, 0.035)))
    pupil.data.materials.append(m_pupil)
    meshes.append(pupil)

# the grin: a low tube bent over the lower arc of a circle, square section,
# planted just proud of the chin so the corners dimple into the cheeks
GRIN_R = 0.38
GRIN_A = (math.radians(200), math.radians(340))
GRIN_STEPS = 12
grin_center = surface_at(Vector((0.0, -1.0, -0.10)).normalized(), 0.02)
front = normal(Vector((0.0, -1.0, -0.10)).normalized())
upv = Vector((0.0, 0.0, 1.0))
right = front.cross(upv).normalized()
upv = right.cross(front).normalized()

verts, faces = [], []
T = 0.055                      # half the tube's square section
for k in range(GRIN_STEPS + 1):
    t = GRIN_A[0] + (GRIN_A[1] - GRIN_A[0]) * k / GRIN_STEPS
    c = grin_center + right * (GRIN_R * math.cos(t)) + upv * (GRIN_R * math.sin(t))
    tang = right * (-math.sin(t)) + upv * math.cos(t)
    side = tang.cross(front).normalized()
    for s, f in ((T, T), (-T, T), (-T, -T), (T, -T)):
        verts.append(c + side * s + front * f)
for k in range(GRIN_STEPS):
    b = k * 4
    for j in range(4):
        faces.append((b + j, b + (j + 1) % 4,
                      b + 4 + (j + 1) % 4, b + 4 + j))
faces.append((0, 1, 2, 3))
faces.append(tuple(range(GRIN_STEPS * 4, GRIN_STEPS * 4 + 4)))
gm = bpy.data.meshes.new("grin")
gm.from_pydata([v[:] for v in verts], [], faces)
gm.update()
grin = bpy.data.objects.new("grin", gm)
bpy.context.scene.collection.objects.link(grin)
grin.data.materials.append(m_pupil)
meshes.append(grin)

# ---------------------------------------------------------------- flower
# one bloom up top, canted to the light: ink-pink petals, amber core

bloom_p = Vector((0.28, 0.05, 1.0)).normalized()
bloom_n = normal(bloom_p)
bloom_c = surface(bloom_p) + bloom_n * 0.05
bloom_right = bloom_n.cross(Vector((0.0, 0.0, 1.0)))
if bloom_right.length < 0.01:
    bloom_right = Vector((1.0, 0.0, 0.0))
bloom_right.normalize()
bloom_up = bloom_n.cross(bloom_right).normalized()

core = C.ico(2)
core.name = "bloom-core"
core.scale = (0.13, 0.13, 0.13)
core.location = bloom_c + bloom_n * 0.10
meshes.append(core)
cores.append(core)

for k in range(5):
    a = 2 * math.pi * k / 5
    d = bloom_right * math.cos(a) + bloom_up * math.sin(a)
    petal = C.ico(2)
    petal.name = f"bloom-petal-{k}"
    petal.scale = (0.13, 0.13, 0.24)
    petal.rotation_mode = "QUATERNION"
    petal.rotation_quaternion = (d + bloom_n * 0.55).normalized().to_track_quat("Z", "Y")
    petal.location = bloom_c + d * 0.20 + bloom_n * 0.06
    meshes.append(petal)
    petals.append(petal)

bpy.context.view_layer.update()

# two tones, per face, against the fixed light — no lamps
def tone():
    for ob in greens:
        C.two_tone(ob, m_green, m_green_d)
    for ob in spines:
        C.two_tone(ob, m_spine_l, m_spine_d)
    for ob in petals:
        C.two_tone(ob, m_petal_l, m_petal_d)
    for ob in cores:
        C.two_tone(ob, m_core_l, m_core_d)

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
    """Rotate the whole fish to `angle` deg around Z; light stays world-fixed."""
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

if SPIN:
    spin_dir = os.path.join(HERE, ".spin")
    os.makedirs(spin_dir, exist_ok=True)
    for k in range(SPIN):
        pose(360.0 * k / SPIN)
        bpy.context.scene.render.filepath = os.path.join(spin_dir, f"frame-{k:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"WROTE {SPIN} frames to {spin_dir}")
