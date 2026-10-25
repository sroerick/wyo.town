# wyo.town

Marketing site for wyo.town Super Intelligence and the reference for the
`wyo.town` identity.

## Files

- `index.html`: the homepage. A stack of brand "sheets" (one field and one
  accent per sheet), built from `brand/brand.css` plus `styles/main.css`.
- `founder.html` and `agents.html`: the two letters, each on its own page. The
  founder's is how he came to this; the agents' is what they run, what they
  claim, what they get wrong, and the gates they work behind. Both are single
  sheets in the record-page form, on `brand/brand.css` plus `styles/main.css`.
- `pricklypear.html`: the product page for 0001 Pricklypear, the flagship.
  An entry opening, what it is (with the spinning model and the intro
  paragraph), and the eight likenesses. Built from `brand/brand.css` plus
  `styles/main.css` and `styles/product.css`. Its closing field is a desert
  grove rather than the starfield: a cloud banner, then the wordmark, then a
  stand of six green pricklypears and six parens pricklypears (`parens.py`,
  the Nopales glyph plant) swaying on sand.
- `nopales.html`: the product page for 0002 Nopales, the language. The
  entry opening, the language statement with the taco model, and the
  register (family, host, store, interface, model, branches, effects).
- `tuna.html`: the product page for 0003 Tuna, the auditable runtime. The
  entry opening, what it is with the can model, and the register (kind,
  foundation, audit, safety, scope, relation).
- `midbar.html`: the product page for 0005 Midbar, the workstation. The
  entry opening, the workstation statement with the pufferfish model, and
  the register (kind, base, posture, path, defaults, config).
- `saguaro.html`: the product page for 0008 Saguaro, the always-on agent.
  The entry opening, the agent statement with the saguaro model, and the
  register (kind, mind, body, transport, runtime, dependencies).
- `borge.html`: the product page for 0007 Borge, the spec engine. The
  entry opening, the specification statement, the three gated phases
  (plan, make, review), and the register. Borge has no model, so the page
  is prose-led and carries no specimen plate.

The six product pages share `brand/brand.css`, `styles/main.css` and
`styles/product.css`. The matching entries in `index.html` link to them.
- `styles/main.css`: homepage components only — the desert masthead, the
  four numbered approach steps, the numbered product entry and its hero,
  and the section statement.
- `styles/product.css`: product-page components only — the entry opening
  with its register line, the specimen plate and its intro, the register
  of spec lines, the numbered likeness ledger, and the way back to the
  catalog.
- `brand/`: identity standards for wyo.town, rev B. Open `brand/sheet.html`;
  the rendered reference is `brand/sheet-001-rev-b.png`. See `brand/BRAND.md`
  for the direction. `brand/starfield.js` is the one moving thing on the page.
  `brand/assets/model-pricklypear-sway.gif` and
  `model-saguaro-sway.gif` are the masthead cacti (the swaying models);
  `model-pricklypear-spin.gif` is the flagship's spinning hero.

## The page

- **Masthead** — desert sand field, ink wordmark, with the saguaro tall on
  the left (bleeding off the trim into the banner) and the smaller
  pricklypear standing in the sand at the right (the swaying models, in
  place of the old pepper glyph). Two things drift through the banner sky:
  the pufferfish on the right and the tuna can on the left.
- **§1 time to get a little western** — the statement ("This Town Is Big Enough For All Of Us")
  and the research-lab paragraph.
- **§2 Our approach** — four numbered steps for small and medium businesses:
  1. SI Literacy · 2. Token Efficiency · 3. Build · 4. Sovereignty.
- **Products** — numbered entries, prose only, each linking to its page
  where one exists (numbers are stable and are not reused):
  - 0001 Pricklypear (flagship, with the spinning model; `pricklypear.html`)
  - 0002 Nopales (the language, with the spinning taco de nopal model;
    `nopales.html`)
  - 0003 Tuna (with the spinning can model; `tuna.html`)
  - 0005 Midbar (with the spinning pufferfish model; `midbar.html`)
  - 0007 Borge (the spec engine; `borge.html`)
  - 0008 Saguaro (the always-on agent, with the spinning model;
    `saguaro.html`)

  0004 Glochid and 0006 Autolith UI have been retired from the catalog.
  Their numbers are not reused.
- **Closing field** — starfield behind the mark and wordmark.

## The product pages

Each product page is the same catalogue form, in the field and accent the
pairing table gives that entry:

- **Entry opening** — the wordmark and the register line "Catalog / 000N",
  the name set wide (with the T-11 tile where it belongs), then the spec
  line for that entry.
- **§1 The statement** — the model shown once, framed and spinning, beside
  the prose for the product.
- **§2 The register** — the spec lines that record the thing.
- **Closing field** — the wordmark and the way back. On most pages it sits
  in the night starfield; on `pricklypear.html` it is the daylight grove.

Per page: `pricklypear.html` carries the eight likenesses (SNOW 01–04, INK
05–08) rather than a second register; `borge.html` carries the three
gated phases instead of a specimen; `nopales.html`, `tuna.html`,
`midbar.html` and `saguaro.html` carry a two-column register.

## Local preview

Serve the directory with any static file server. For example:

```bash
python3 -m http.server 8000
```
