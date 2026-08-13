# Deck spec format

A spec is YAML (JSON works too) with three top-level keys: `meta`, `design`, and `slides`. The generator adds no words of its own — every visible string comes from the spec, so editing the spec is exactly what changes in the rebuilt deck.

- [Design block](#design-block)
- [Slide chrome](#slide-chrome)
- [Layout model](#layout-model)
- [Elements](#elements)
- [Layout variants](#layout-variants)
- [Capacity limits](#capacity-limits)

## Design block

```yaml
meta: { title: "Installing Claude Code", author: "Ryan" }
design:
  theme: ember          # ember | ink | slate | press
  personality: technical # technical | keynote | editorial
  vcenter: true         # optional; see below
  overrides: { accent: "2D6BB0" }   # optional single-token nudges
```

`vcenter` slides each slide's whole composition — kicker, title and body together — down so it sits optically centred rather than jammed against the top. Content that already fills the page does not move. The `keynote` and `editorial` personalities turn it on by default; `technical` does not, so set `vcenter: true` at the design level for any deck whose slides are running short. Individual slides override it with their own `vcenter: true|false`.

`theme` sets colour and type pairing; `personality` sets scale, spacing, and how much air each slide gets. The studio writes both keys back when the user picks a look, so never hand-edit them while the studio has unsaved changes.

Colours are always 6-digit hex **without** a leading `#` — a `#` corrupts the pptx. Anywhere a colour is accepted you may instead use a theme key: `accent`, `muted`, `text`, `ok`, `bad`, `okCode`, `badCode`, `code`, `codeDim`, `line`, `fill`, `panel`, `dark`.

## Slide chrome

```yaml
- background: dark        # light (default) | dark | 6-digit hex
  kicker: "02 · Prompting"          # small uppercase accent label
  title: "Plain string"
  # or styled:  title: { text: "...", size: 36, color: accent, w: 8.5, align: center }
  # or two-line: title: { size: 40, lines: [ {text: "Getting it"}, {text: "Just Right", color: accent} ] }
  subtitle: "One muted line under the title."
  margin: 0.9             # side margin, inches — defaults come from the personality
  contentTop: 1.15        # where the kicker starts
  gapAfterTitle: 0.3
  elementGap: 0.28        # default space between elements
  notes: >-
    Everything the presenter says. Keep it here, not on the slide.
  elements: [ ... ]
```

A slide with a custom hex `background` picks its own text contrast by luminance, so a dark custom colour behaves like `dark` automatically.

## Layout model

Elements stack top to bottom; each reports its height and the next begins below it. Three tools shape the flow:

- **`columns`** — an element whose `items` is a list of element-lists, laid side by side. `widths` takes fractions (equal by default), `gap` the space between. Columns nest.
- **`at: {x, y, w}`** — absolute inches. The element draws there and the flow ignores it. Use for pinned art and callouts that should hang off the grid.
- **`gap`** on any element overrides the space after it; `indent` shifts it right; the `spacer` element adds explicit room.

The page is 13.333 × 7.5 in. Keep content above **7.05 in** — fonts are fixed size, so text that does not fit overflows the slide instead of shrinking. The builder prints every overflowing slide with the exact overshoot; fix it by splitting or shortening in the spec, never by nudging the renderer.

## Elements

Each element is an object with a `type`.

**`text`** — a paragraph. Either `text:` with `size/color/bold/italic/mono/align`, or `runs:` for mixed styling: `[{text, bold?, italic?, mono?, color?, size?, break?}]`. Each run is separately editable in the studio, so mixed styling survives an edit.

**`bullets`** — `items:` of strings or `{text, bold?, color?}`. `marker: dash` swaps • for –.

**`code`** — dark console panel with traffic-light chrome. `title:` labels the bar (`false` removes the bar entirely), `lines:` takes strings or `{t, c?, b?, s?}` (text, colour, bold, size), `fontSize` defaults to the personality's code size. Lines never wrap — break them by hand.

**`callout`** — rounded statement box. `style:` is `solid` (dark fill), `tint` (accent wash), `onDark` (for dark slides), or `outline`. Content is `bold` plus `text` for the two-line emphasis pattern, or plain `text`/`runs`. `icon` puts an accent circle at the left.

**`chips`** — pill labels. `labels: []`, `style: tint|solid|muted`. Chips size to their text and wrap across rows; `fit: false` spreads them evenly across the full width instead.

**`cards`** — a row of boxes, all sharing one height so their edges line up. `cards:` entries compose from `icon`, `name`, `sub` (accent subtitle), `mono` (path line), `lead` (bold line), `rows:` (`{label?, labelColor?, text}` for Pro/Con pairs), `bullets: []`, `example` (italic, pinned to the card bottom), `tag` + `tagStyle: solid` (chip pinned bottom-left), `emphasis: true` (tinted and outlined — use it to mark the recommended option). `height` overrides the shared height.

**`icon_rows`** — two layouts. Grid (default): `{icon, head, body}` in `columns` (default 2). List (`layout: list`): `{icon, name, cmd?, body}` with the name and mono command at the left and body at the right; `dividers: true` rules between rows.

**`numbered`** — accent-numbered action rows from `items:`. Reads best on a dark closing slide.

**`quote`** — accent italic line with optional `caption`. `align` defaults to right.

**`image`** — `path`, `w`, `h`. The path must be a real file on disk at build time, and it resolves relative to the spec file's own directory — so a spec and its `assets/` folder move together without any path edits.

**`divider`** — a rule. **`spacer`** — vertical space (`h`).

Every string that comes from the spec is click-editable in the studio, down to individual runs — a card row's label and its body edit independently. Only two kinds of text are not: decorative glyphs (bullet markers, icon characters) and the digits on a `numbered` list, which are derived from position rather than stored.

Icon names: `terminal bolt check cross star dot arrow up down book gear flag pin bulb warn clock layers search chat doc brain one two three four five`. Any 1–2 character literal also works. An unknown name fails the build rather than rendering a blank circle.

## Layout variants

To offer the user a real choice of arrangement for a slide, give that slide a `variants:` list. Each entry is a label plus an alternative element stack:

```yaml
- kicker: "01 · Options"
  title: "3 Install Options"
  elements: [ ... ]        # the default arrangement
  variants:
    - label: "As cards"
      elements: [ {type: cards, cards: [...] } ]
    - label: "As icon rows"
      elements: [ {type: icon_rows, layout: list, items: [...] } ]
```

The studio renders each variant full-size next to the others. When the user picks one, its elements replace `elements` and the `variants` block is deleted — the spec ends up holding the decision, not the menu.

Author variants only where the arrangement is genuinely arguable (a comparison that could be cards or a table, a list that could be prose). Offering three versions of an obvious title slide wastes the user's attention.

## Capacity limits

Fonts do not shrink to fit, so these are real limits, not style advice:

| Slot | Budget |
|---|---|
| Card `rows` text | ~110 chars |
| `icon_rows` grid body | ~100 chars |
| `icon_rows` list body | ~150 chars (wraps to 2 lines) |
| `numbered` item | ~90 chars |
| `code` line | short enough for the panel at its font size — never wraps |
| Slide total height | 7.05 in |

When a slide exceeds its budget, split it into two slides. A cramped slide and an overflowing slide are the same defect at different severities.
