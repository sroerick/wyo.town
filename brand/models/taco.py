# taco.py — build + render the wyo.town low-poly taco de nopal
#
# Usage:
#   blender -b --python brand/models/taco.py
#   blender -b --python brand/models/taco.py -- 160       one still, rotated
#   blender -b --python brand/models/taco.py -- spin 24   24 turntable frames -> .spin/
#
# Writes:
#   brand/models/taco.blend       (source file, re-editable)
#   brand/assets/model-taco.png   (catalog artifact, 512px)
#
# Brand treatment (palette, two-tone, flat render, auto-frame) lives in
# _common.py. This file is only the taco.
#
# Nopales is the language Pricklypear is written in, so its artifact is the
# dish the language is named for. The shell is literally what a taco shell is:
# a tortilla — one flat disc — folded along a diameter. FOLD is the crease
# angle; at 0 the disc is flat, at 90 it is folded shut. The fold line becomes
# the bottom of the shell, the disc's edge becomes the rim, and the disc's
# centre becomes the deepest point. The filling is chopped pads piled in the
# trough, the way the low-poly catalog builds everything.

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# the shell is the dry field; the filling is the pear; the onion is the light
SHELL_L = "AMBER"     # #FFB300, the fried corn, lit faces
SHELL_D = "RUST"      # #AA3311, the fold, shaded faces
NOPAL_L = "#4E8C4A"   # tile-pricklypear pads, lit
NOPAL_D = "#2C4A28"   # tile-pricklypear pads, shaded
ONION_L = "SNOW"      # #F6F5F0
ONION_D = "CHROME"    # #BFBFBF

SEED = 7

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLEND_OUT = os.path.join(HERE, "taco.blend")
PNG_OUT = os.path.join(ROOT, "brand", "assets", "model-taco.png")

# ---- the tortilla ---------------------------------------------------------
R_DISC = 1.08               # the tortilla's radius
FOLD = math.radians(46.0)   # crease angle from flat; the shell's openness
THICK = 0.075               # a tortilla has a thickness
NTH = 48                    # segments around the disc (multiple of 4: keeps
NR = 20                     #   the fold line, θ = 0 and π, on a grid line)
# NR/NTH this fine so the per-face two-tone resolves to a gradient of facets
# end-on, instead of reading as stripes

TAN = math.tan(FOLD)        # the trough walls are planes at this slope
SIN = math.sin(FOLD)
COS = math.cos(FOLD)

C.new_scene(seed=SEED)

m_shell_l = C.material("shell-lit", SHELL_L)
m_shell_d = C.material("shell-shade", SHELL_D)
m_nopal_l = C.material("nopal-lit", NOPAL_L)
m_nopal_d = C.material("nopal-shade", NOPAL_D)
m_onion_l = C.material("onion-lit", ONION_L)
m_onion_d = C.material("onion-shade", ONION_D)


def fold_point(r, th):
    """A point at radius R and angle TH on the flat tortilla, after folding.
    The fold line is the x-axis: perpendicular distance d = r·sin(θ) becomes
    the wall height d·sin(FOLD), and the wall leans in by d·cos(FOLD)."""
    x = r * math.cos(th)
    d = r * math.sin(th)
    return (x, d * COS, abs(d) * SIN)


def shell():
    """A flat disc, folded. One surface: a fan from the centre, then rings.
    Solidify gives it thickness and caps the rim, so this is only the fold."""
    verts = [(0.0, 0.0, 0.0)]
    for i in range(1, NR + 1):
        r = R_DISC * i / NR
        for j in range(NTH):
            verts.append(fold_point(r, 2 * math.pi * j / NTH))
    v = lambda i, j: 1 + (i - 1) * NTH + (j % NTH)

    faces = [(0, v(1, j), v(1, j + 1)) for j in range(NTH)]
    for i in range(1, NR):
        for j in range(NTH):
            faces.append((v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)))

    me = bpy.data.meshes.new("shell")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("shell", me)
    bpy.context.scene.collection.objects.link(ob)

    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    mod = ob.modifiers.new("thickness", "SOLIDIFY")
    mod.thickness = THICK
    mod.offset = 0.0            # the disc is the mid-surface
    mod.use_even_offset = True
    mod.use_rim = True
    bpy.ops.object.modifier_apply(modifier="thickness")
    ob.select_set(False)
    return ob


meshes = []
shell_ob = shell()
meshes.append(shell_ob)


def floor_z(y):
    """The inside of the shell, measured up from the fold, at lateral Y."""
    return abs(y) * TAN - THICK / COS


def half_width(x):
    """The shell's half-width at X: the folded disc can only reach so far
    out before the rim curves back in. No filling goes past this."""
    return COS * math.sqrt(max(0.0, R_DISC * R_DISC - x * x))


def rim_z(x):
    """Height of the rim above the fold at X. The rim is the disc's edge, so
    it dips toward the tips; the pile has to stay under it."""
    return SIN * math.sqrt(max(0.0, R_DISC * R_DISC - x * x))


def mound_top(x, y):
    """How high the filling piles at (x, y). A dome that follows the shell's
    own taper — tall over the belly, dropping away toward the tips — and topped
    out level with the rim, never over it."""
    e = (x / 0.76) ** 2 + (y / 0.52) ** 2
    if e >= 1.0:
        return 0.0
    return (rim_z(x) + 0.03) * math.sqrt(1.0 - e)


# ---- the nopales ----------------------------------------------------------
# Chopped pads piled in the trough, as long thin strips. The pile has to read
# as a pile — strips, not a mass — so the lattice is jittered and holed, no
# two strips in a column are the same chop, and the column tops are ragged:
# most stop short of the dome, a few crest it. Three rules keep the pile
# inside the shell: a strip's flat bottom rests on the highest bit of wall
# beneath its footprint, no strip reaches past the shell's half-width at its
# X, and every strip stays clear of the pinched tips.
rng = random.Random(SEED + 3)
nopal = []


def inside_shell(s):
    """True if no corner of the (placed, rotated) strip escapes the shell:
    nothing past the trough walls, nothing past the rim, nothing under the
    fold. Grazing the wall is fine — a strip rests on it — escaping is not."""
    bpy.context.view_layer.update()
    for corner in s.bound_box:
        w = s.matrix_world @ Vector(corner)
        if w.z < (abs(w.y) - 0.02) * TAN:        # through a trough wall
            return False
        if abs(w.x) > 0.66:                       # out at the pinched tips
            return False
    return True


def strip(x, y, z):
    """One chop of nopal, bottom edge at Z; returns it, or None if it leaks."""
    h = rng.uniform(0.085, 0.17)                 # ragged: every chop is its own
    hx = rng.uniform(0.12, 0.27)                 # the strip runs with the fold
    hy = rng.uniform(0.045, 0.08)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    s = bpy.context.active_object
    s.name = f"nopal-{len(nopal)}"
    s.scale = (2 * hx, 2 * hy, h)
    s.location = (x + rng.uniform(-0.05, 0.05),
                  y + rng.uniform(-0.03, 0.03),
                  z + h / 2)
    s.rotation_euler = (rng.uniform(-0.16, 0.16), rng.uniform(-0.16, 0.16),
                        rng.uniform(-0.38, 0.38))
    if not inside_shell(s):
        bpy.data.objects.remove(s)
        return None
    nopal.append(s)
    return s


for x in [(-0.58 + 0.145 * i) + rng.uniform(-0.045, 0.045) for i in range(9)]:
    for y in [(-0.34 + 0.097 * j) + rng.uniform(-0.035, 0.035) for j in range(8)]:
        top = mound_top(x, y)
        if top <= 0.0 or abs(y) > half_width(x) - 0.06 or rng.random() < 0.27:
            continue
        z = (abs(y) + 0.07) * TAN               # the flat bottom sits on the wall
        crest = rng.random() < 0.10             # a few strips crest the rim
        # wide variance: the pile has a skyline, not a plateau
        ragged = top - (rng.uniform(0.0, 0.05) if crest else rng.uniform(0.06, 0.30))
        while z < ragged:
            s = strip(x, y, z)
            if s is None:
                break
            z += s.dimensions.z * rng.uniform(0.75, 1.0)  # overlap: a pile is a pile
meshes += nopal

# ---- the onion ------------------------------------------------------------
# Diced white, scattered over the top of the pile — most pieces sit proud,
# a few are buried deep enough to just show.
onion = []
for _ in range(10):
    x = rng.uniform(-0.44, 0.44)
    y = rng.uniform(-0.22, 0.22)                # over the belly, not the bare wall
    top = mound_top(x, y)
    if top <= 0.0 or abs(y) > half_width(x) - 0.10:  # stay in the trough
        continue
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    s = bpy.context.active_object
    s.name = f"onion-{len(onion)}"
    s.scale = (rng.uniform(0.04, 0.06), rng.uniform(0.035, 0.05), rng.uniform(0.03, 0.045))
    # buried in the pile: proud of it, but never dabbing the bare wall
    s.location = (x, y, min(rim_z(x) - 0.08,
                            max(floor_z(y) + 0.05, top - rng.uniform(0.02, 0.16))))
    s.rotation_euler = (rng.uniform(0, 0.7), rng.uniform(0, 0.7), rng.uniform(0, 0.7))
    if not inside_shell(s):
        bpy.data.objects.remove(s)
        continue
    onion.append(s)
meshes += onion

bpy.context.view_layer.update()

# two tones, per face, against the fixed light — no lamps
C.two_tone(shell_ob, m_shell_l, m_shell_d)
for ob in nopal:
    C.two_tone(ob, m_nopal_l, m_nopal_d)
for ob in onion:
    C.two_tone(ob, m_onion_l, m_onion_d)

# ---- pose -----------------------------------------------------------------
# the fold runs along x, so the default camera (looking along -y, raised) sees
# the shell lengthwise and over the near rim. A small turn gives it the
# product-shot three-quarter instead of a dead-on elevation.
TURN_Z = math.radians(38.0)

base = {o: o.matrix_world.copy() for o in meshes}
POSE = Matrix.Rotation(TURN_Z, 4, "Z")


def pose(angle):
    """Rotate the taco to `angle` deg around Z; light stays world-fixed."""
    Rz = Matrix.Rotation(math.radians(angle), 4, "Z")
    for o in meshes:
        o.matrix_world = Rz @ POSE @ base[o]
    bpy.context.view_layer.update()


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TURN, SPIN = 0.0, 0
if args and args[0] == "spin":
    SPIN = int(args[1]) if len(args) > 1 else 24
elif args:
    TURN = float(args[0])

pose(TURN)
if TURN:
    stem, dot = os.path.splitext(PNG_OUT)
    PNG_OUT = f"{stem}-{int(TURN)}{dot}"

# a three-quarter, looking over the near rim and down into the trough
C.finish(BLEND_OUT, PNG_OUT, frame=meshes, cam_offset=(1.7, -9.5, 5.6))

if SPIN:
    spin_dir = os.path.join(HERE, ".spin")
    os.makedirs(spin_dir, exist_ok=True)
    for k in range(SPIN):
        pose(360.0 * k / SPIN)
        bpy.context.scene.render.filepath = os.path.join(spin_dir, f"frame-{k:03d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"WROTE {SPIN} frames to {spin_dir}")
