# wyo.town brand direction

Sheet 001, rev C. Read `sheet.html`, or `sheet-001-rev-c.png` for the render.

---

## Decisions

- **The scheme is streams in the desert.** The desert is the subject. The machine is the medium.
- **The pricklypear is the hero artifact.** It leads the tile catalog and is shown the way the mark is
  shown.
- **The sunset strip is retired as a device.** SUNSET, PINK and PLUM remain inks 06, 07 and 09. See
  *the sunset, retired* below.
- **SIGN is Ultra.** Holtwood One SC, Sancreek and Rye are downloaded as alternates and are one CSS
  variable away.
- **PLACARD is Chicago Kare**, the 1984 bitmap. No Cooper Black license is needed anywhere.
- **The mark is the only device.** No second symbol, no printer's mark. The brand carries the colophon.
- **The artifact carries data, not commentary.** Numbers, names, hex values, rules. Prose lives in this
  memo.

---

## The frame

A museum, not an experience. Artifacts are shown once, at a fixed size, numbered and captioned. Two
things move and nothing is interactive: the star field, and the one animated tile. Every other artifact
is still.

Two layers, kept separate:

- **The medium is 1984.** Sixteen indexed slots, bitmap type, flat rectangles, a catalog register, a
  tile quoted once. The medium is how a thing is drawn, never what it is a drawing of.
- **The subject is the desert, with water in it.** Sand, bone, clay, dry grass; rain, spring water, a
  stream, deep water; the pear and its fruit; the night sky. Streams in the desert, water from the
  rock. The subject is why the palette holds together: every loud ink is a thing in one landscape, and
  pairing a field with an accent pairs one part of that landscape with another.

Vaporwave works the same material and gets the opposite result, because it treats the period as a ruin:
haze, decay, blending gradients, irony. This treats it as an archive: flat, crisp, dated, catalogued. That
single difference is what keeps the system from being pastiche, and it is also why the AI aesthetic and
the Y2K revival are both out: they are atmosphere where this is inventory.

What each reference contributes, in one line each:

| Reference | Contribution |
|---|---|
| TempleOS | sixteen indexed slots, everything drawn from flat rectangles, one person's complete world |
| Miami Vice | the pink and aqua pairing |
| vintage computer ads | the catalog register: item numbers, spec lines, a product shot |
| Geocities | the tile, quoted once instead of inhabited |

### The sunset, retired

Rev B used a four-band strip of amber, sunset, pink and plum as a signature rule across the cover and the
closings. It came from Miami Vice, not from the concept; it never carried the idea, so it no longer
carries a slot. SUNSET, PINK and PLUM stay in the palette as inks 06, 07 and 09. The mechanic behind the
strip survives as a limitation: a gradient, if one is ever drawn, is flat bands, never a blend.

### The dither is the shoreline

The one permitted texture was always a boundary, and a boundary in this landscape is a shoreline: where a
desert ink meets a stream ink, it dithers. In CSS it is one `repeating-conic-gradient` in `currentColor`,
so it tints to the field it sits on. The rule did not change; what the texture is for did.

---

## Ink

Sixteen inks, numbered 00 to 15 like a hardware palette, curated from the two palettes the era actually
had (EGA/VGA 16, 1984, and web safe 216, 1996; both are drawn on the sheet as specimens).

| | Name | Hex | | | Name | Hex |
|---|---|---|---|---|---|---|
| 00 | INK | `#101418` | | 08 | MAGENTA | `#AA00AA` |
| 01 | SNOW | `#F6F5F0` | | 09 | PLUM | `#7A1FA2` |
| 02 | STOCK | `#EAD2A0` | | 10 | AZURE | `#1E6BFF` |
| 03 | CHROME | `#BFBFBF` | | 11 | SKY | `#88CCEE` |
| 04 | RUST | `#AA3311` | | 12 | AQUA | `#00C2C7` |
| 05 | AMBER | `#FFB300` | | 13 | LIME | `#C8F24E` |
| 06 | SUNSET | `#FF7A45` | | 14 | TEAL | `#0B5D6B` |
| 07 | PINK | `#FF3EA5` | | 15 | TERRITORIAL | `#002F6C` |

The sixteen split into four families, and the families are the landscape:

| Family | Inks | In the landscape |
|---|---|---|
| Structure | 00 INK, 01 SNOW | the night and the light field; type, rules, paper |
| Desert | 02 STOCK sand, 03 CHROME bone, 04 RUST clay and iron, 05 AMBER dry grass, 06 SUNSET heat | the dry field |
| Streams | 09 PLUM dusk, 10 AZURE the stream, 11 SKY the rain sky, 12 AQUA spring water, 14 TEAL deep water, 15 TERRITORIAL deep water at night | from rain down to the deep |
| The pear | 13 LIME the pads, 07 PINK the fruit, 08 MAGENTA the fruit ripe | blooming in dry country |

**One field per page. Type is INK or SNOW, never a third color. One accent per page, used once.** The
per-field pairing table on the sheet fixes which accent goes with which field, so sixteen loud inks stay a
catalog instead of becoming noise. The library is large; the page is not.

**Nothing blends.**

---

## Type

| Role | Face | License | Job |
|---|---|---|---|
| PLACARD | Chicago Kare | MIT | headings, labels, interface |
| SIGN | Ultra | Apache 2.0 | wordmark and numerals only |
| FIELD | Instrument Sans | OFL | prose |
| REGISTER | IBM Plex Mono | OFL | numbers, codes, dates, specs |

Chicago Kare reproduces the bitmap Chicago Susan Kare drew for Apple in 1984. Apple owns the name; the
reproduction is MIT licensed under a different name, so use is clean. Keep the provenance line in a
colophon if this ever gets prominent.

---

## The mark

The brand is a ranch brand: **W over T**, drawn as the paleo-Hebrew letters **aleph over tav**. The W is the
ox head (aleph); the T is the cross (tav). Read one way it is a Wyoming cattle brand; read the other it is
א-ת, the first and the last. Two readings, one mark, which is the whole trick. Strokes are flat-topped, like
an iron stamp: no horns, no serifs, nothing that would not survive being burned into a hide.

The mark is also the printer's device: a colophon, an anchor, a fleuron. There is no second symbol. It
does not illustrate anything and needs no personality. The brand is a monogram that says the name without
spelling it.

One flat color per artifact: RUST, AMBER, INK or SNOW. Clear space is one mark height, because the mark is
the unit of measure. Floor is 24 px; below that, the wordmark alone. The mark is not rotated, animated,
outlined, given a face, or used as a bullet under 24 px.

---

## Tiles

The period's ornament was a square of flat color, repeated until it filled the viewport. Twenty are
accessioned: sixteen in service, and four withdrawn, marked in the registry below. In service, in two
kinds:

- **patterns**: opaque, seamless, drawn on a 16 by 16 grid. Cloud, grid, dither, ripple, granite and
  strata. Also cowhide (T-09), which repeats on 32 by 32 because a hide has more detail in it
  than a 16 by 16 cell can hold.
- **figures**: transparent, so they sit on any field. Hourglass, pricklypear, sage, mountain,
  starburst, moon, trout, stream and cottonwood.

The hero is **T-11, pricklypear**. It leads the catalog on the sheet, and a new figure is judged against
it the way a setting of the wordmark is judged against the mark.

The figures are drawn on a 32 by 32 grid. At 16 by 16 a cactus, a shrub and a crescent all read as the same
blur; at 32 they read as the things they name. Patterns stay at 16, where the period put them, because a
pattern only has to be a rhythm, not a likeness.

Draw rules: flat rectangles, no stroke, no antialiasing, no gradient, no shadow. Two to four inks from the
house sixteen. `make-tiles.lisp` generates all of them and both palette specimens, with no dependencies;
new tiles cost a few lines of data.

Read by the landscape, the catalog stands as:

- **the desert**: T-06 granite (the rock), T-17 strata (the canyon wall), T-09 cowhide (the range),
  T-12 sage, T-13 mountain, T-20 cottonwood
- **the streams**: T-01 cloud (rain), T-03 dither (the shoreline), T-05 ripple, T-18 trout, T-19 stream
- **the pear**: T-11 pricklypear
- **the night**: T-14 starburst, T-16 moon
- **the record**: T-02 grid (the survey), T-08 hourglass (the one clock)

### Withdrawn

Four tiles belonged to the medium rather than the subject. Accession numbers are not reused: the
replacements accessioned as T-17 to T-20, and the withdrawn tiles stay in the registry, marked
withdrawn.

| Tile | Withdrawn for | Succeeded by |
|---|---|---|
| T-04 hazard | an industrial stripe; the machine, not the land | T-17 strata, the river-cut bands of a canyon wall |
| T-07 bullet | violent craft; nothing in the landscape | T-18 trout, the fish the streams were made for |
| T-10 sunset | was drawn for the retired device | T-19 stream, so the scheme has its own figure |
| T-15 disc | pure medium | T-20 cottonwood, the tree that marks water in the desert |

**T-08, the hourglass, stays.** It is the one artifact in the catalog that measures time, so it is the
one that runs: eight frames of sand draining top to bottom, emitted as a stepped SMIL loop so it runs
inside a plain `<img>`, no script. No other tile moves.

Two permitted placements for the star field, and no others. The field is the night sky over the desert:

1. **behind the sheet**: the field is drawn live on a canvas at `brand/starfield.js` and fixed behind the
   whole catalog. It is visible in the sheet's margins, and it stops under `prefers-reduced-motion`.
2. **as the closing field**: at the foot of the sheet, the field takes the whole viewport behind the
   wordmark. Flat pixel stars fly out from the centre, straight out rather than in depth shells, each at
   its own speed, growing as they reach the edge. The sheets are opaque, so the field is only ever seen
   in the margins and in this closing field. The old bitmap starfield tile is retired.

The tile placements are these:

1. **beside content**: one square, fixed size, at the size of a printed specimen. The default.
2. **in a band**: a tile may repeat horizontally inside a bounded strip, as in the masthead banner. A band
   is not a field. A figure is never repeated into a band.

The sheet also carries two documents, because they are how the artifacts are recorded: the cloud shown
twice by two so the seam can be checked, and the hourglass, which is simply running. The still frame is
the artifact; the running loop is the same artifact, in its eight states.

---

## Photograph

`assets/cloud.jpg` is the one photograph in the system: rain building over the desert. `assets/photo-cloud-4up.jpg`
is a square centre crop tiled two by two with mirrored halves, so it repeats seamlessly: four up, at a fixed
size, in a sidebar or a band. Photographs never take a whole page and never mix into the ink system, because
flat ink and photographic depth are two different worlds and the contrast is the point.

---

## The two registers

A project is listed twice, with the same number, the same sentence and the same date: a **museum label**
(accession, name, medium, date, credit) and a **catalog line item** (product shot, name, specs, reg. no.
panel). The shop and the museum describe a thing identically, and an addition to the shelf is a numbered
entry rather than a redesign.

---

## Files

```
wyo.town/brand/
  BRAND.md              this memo
  sheet.html            identity standards, sheet 001 rev C
  starfield.js          the closing star field, a canvas of flat pixel stars
  brand.css             inks, pairing system, banner, photograph, components
  sheet-001-rev-b.png   render, rev B
  sheet-001-rev-c.png   render, rev C
  make-tiles.lisp       regenerates assets/ from scratch
  assets/               20 tiles (16 in service, 4 withdrawn), mark-brand.svg,
                        photo-cloud-4up.jpg, cloud.jpg, 2 palette specimens
  fonts/                Chicago Kare, Ultra, Holtwood One SC, Sancreek, Rye,
                        Instrument Sans, IBM Plex Mono, each woff2 with its license
```

Everything loads locally, so the sheet renders with no network access.

---

## Open

1. The new `index.html`, built from this sheet, with your copy.
