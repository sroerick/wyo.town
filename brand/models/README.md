# brand/models

3D brand artifacts, built as Blender Python scripts and rendered to static
catalog PNGs. See `BRAND.md` for the system: palette-only, nothing blends,
artifacts are still, numbered, captioned.

## Render

```bash
blender -b --python brand/models/pricklypear.py
```

Each script writes its `.blend` here and its catalog PNG to `brand/assets/model-<name>.png`.

## Writing a model

`_common.py` carries the whole treatment; a model script is geometry only:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

C.new_scene(seed=7)                     # deterministic randomness
lit  = C.material("skin-lit", "AMBER")  # ink name from C.INKS ...
dark = C.material("skin-shade", "#2C4A28")  # ... or literal hex

ob = C.ico(2)                           # primitives; set location/scale/euler
C.two_tone(ob, lit, dark)               # per-face lit/shade, no lights

C.finish("name.blend", "name.png", frame=[ob])  # auto-frame camera, render
```

Rules that make it read as the brand:

- **Palette only.** Every color is an ink or a tile hex. No other values.
- **Low poly, flat shaded.** Icospheres and boxes; never subdivision-surface
  smooth, never smooth normals.
- **Two tones per mesh**, split by face normal against `C.LIGHT` — never a
  real lamp.
- **Still and framed.** Fixed ortho 3/4 product shot, transparent field (the
  page supplies the field), 512 px. Reroll `seed` for a variant, then commit
  the number.

## Registered

| Model | Script | Used ink |
|---|---|---|
| pricklypear | `pricklypear.py` | `#4E8C4A` `#2C4A28` `#E8F2D0` AMBER RUST on STOCK |
| taco | `taco.py` | AMBER RUST `#4E8C4A` `#2C4A28` SNOW CHROME, transparent field |
| pufferfish | `pufferfish.py` | `#4E8C4A` `#2C4A28` SNOW STOCK INK PINK MAGENTA AMBER RUST |
| parens | `parens.py` | INK TEAL, transparent field; still, spin and sway |

The taco is the artifact for 0002 Nopales: the language is named for the
dish, so its model is the dish. The parens pricklypear is the language's
second face: Nopales is a Lisp, so its cactus is grown from "()" pads — two
tapered arc-strokes per pad, each pad rolled onto its growth bearing so it
sprouts narrow-side-out like a real pad. The glyph is printed, not green:
INK lit over TEAL shade, areoles as punctuation. No fruit — the plant is
pure type (the tuna code stays in the script; `FRUIT_NODES` is just empty).
It closes `pricklypear.html` in a desert grove: six green pricklypears and
six parens pricklypears swaying on sand under a cloud banner
(`model-parens-sway.gif`; positions in `styles/product.css`).

The pufferfish is Puffy, the OpenBSD fish, naturalized as a barrel cactus:
the spikes are spines, the fins are pads, and he kept the eyes and the grin. `-- spin N` writes N turntable frames to
`.spin/`; assemble the spin GIF with
`magick -dispose Previous -delay 8 -loop 0 .spin/frame-*.png -layers optimize out.gif`.
The `-dispose Previous` is load-bearing: without it ImageMagick writes
delta frames with Undefined disposal, and viewers smear trails behind the
spinning model.
