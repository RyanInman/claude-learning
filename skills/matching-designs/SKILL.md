---
name: matching-designs
description: Builds or fixes a web page so it matches a design image, then proves the match with a screenshot diff, element geometry, and a computed-style token check, looping fix-and-verify up to 5 rounds. Use whenever the user hands over a mockup, wireframe, comp, Figma export, screenshot, or PNG/JPG of a UI and wants it built, "make this look like the design", "match this mockup", "pixel-perfect this", "why doesn't my page look like the comp", "implement this screenshot", "does my page match the design", or wants a visual regression baseline for a page - even if they never say "design" and just attach an image next to "build this". Do NOT use to invent a design with no source image (use frontend-design or design), for component snapshot suites or a11y audits, or to diagnose a non-visual bug.
---

# Matching designs

Build a page that matches a design image, and prove it with numbers instead of a glance.

Claude's default is to look at the design, write plausible CSS, look at the result, and declare it close. "Close" hides a wrong heading color, a 16px gap that should be 24px, and a card sitting 60px too high. This skill replaces the glance with a measured loop: extract exact tokens and rects, build, screenshot, diff, compare computed styles and geometry, fix only what the report names, repeat.

## The three numbers

`check.mjs` reports three percentages. Read them in this order, because they fail for different reasons and only one of them is fully fixable:

| Number | Means | Fix with |
| --- | --- | --- |
| `mismatches` | A token or a box is off by an exact amount | The named CSS rule |
| `layoutDiff` | Pixel difference with all text masked out | Position, size, color, images |
| `diffPercent` | Overall pixel difference | Everything above, plus glyph rendering |

`diffPercent` carries a floor no CSS removes: the design's text was rendered by another font engine at another scale. A run of this skill measured 12.3% overall and 1.71% layout — the page was finished, and two of its five rounds were spent chasing a floor. Judge the build on `layoutDiff` and `mismatches`. Report `diffPercent` for the record.

## Setup

Run once per machine, because the scripts need Playwright's Chromium and two npm packages:

```
cd <skill>/scripts && npm install && npx playwright install chromium
```

## Step 0: Ask the fidelity level

Before extracting the spec, ask the user which fidelity level to build to. Use `AskUserQuestion` with these options:

| Level | Meaning | `--layout-threshold` | `--threshold` |
| --- | --- | --- | --- |
| Low | Layout right, styling approximate | `4` | `11` |
| Medium | Layout tight, styling exact | `2` | `8` |
| High | Every rect within a pixel or two | `1` | `6` |

Pass both on every `check.mjs` call. A run passes on zero mismatches plus either threshold, so a text-heavy design passes on its layout once the layout is right. A higher threshold is not a shortcut — still fix every mismatch and every named region, because the thresholds change when the loop declares victory, not how carefully each round gets reviewed.

## Step 1: Extract the spec from the image

Read the design image. Write `design-spec.json` next to the target page with this shape:

```json
{"viewport":{"width":1440,"height":900},
 "fonts":["Inter"],
 "tokens":[
  {"selector":"h1","property":"color","expected":"#1a1a1a","at":[40,60]},
  {"selector":"h1","property":"font-size","expected":"40px"},
  {"selector":".cta","property":"background-color","expected":"#2563eb","at":[700,400]}
 ],
 "boxes":[
  {"selector":".modal","x":248,"y":40,"width":820,"height":500},
  {"selector":".card","x":276,"y":300,"width":180,"height":140,"tolerance":6}
 ]}
```

Set `viewport` to the image's pixel size. `check.mjs` refuses any other value.

**Boxes are required.** Measure at least the main container, each fixed bar, and one instance of each repeated block. Omit any of `x`, `y`, `width`, `height` you cannot measure; the rest still get checked. `tolerance` defaults to 4px. Skip boxes only with `--allow-no-boxes`, for a page with no layout to measure, because a color-only spec reports a perfect score on a page whose blocks sit in the wrong place — that is how one earlier run held zero mismatches while its whole modal sat 60px too high.

Record 8-15 tokens:

- every text color
- every background color
- the font size of each text level
- the gap of each grid or flex row
- the padding of the main container

Write exact values (`#2563eb`, `24px`), never descriptions, because the token script compares strings and numbers.

**Put `at:[x,y]` on every color token.** `check.mjs` re-samples the design image at that pixel and refuses to run when it disagrees with `expected`. Without it, a mis-sampled hex is indistinguishable from a correct one, and five rounds go into moving the page toward the wrong color.

List every typeface in `fonts`. `tokens.mjs` fails when the family is not actually loaded, because a silent fallback shifts every line and shows up as unfixable text diff.

Sample colors and find element boundaries with `sample.mjs` instead of writing one-off pixel-scan scripts:

```
node <skill>/scripts/sample.mjs --src design.png --points '[["h1-color",40,60],["cta-bg",700,400]]'
node <skill>/scripts/sample.mjs --src design.png --scan row --at 150 --x0 0 --x1 1440
```

Point mode prints the hex at each labeled coordinate. Scan mode walks one row or column and prints where it crosses between background and content, so you get the box edges for the `boxes` array in one call.

Read `references/spec-extraction.md` when the image is a JPG with compression noise, has no obvious grid, or you cannot tell two similar colors apart.

Use selectors that will exist in the page you build. A selector that matches nothing stops the check with exit 5.

### Crop browser chrome first

If the image is a browser screenshot (a title bar, tabs, or an address bar are visible above the content), crop that chrome out before it becomes the spec image. `check.mjs` diffs the whole file, so a URL bar baked into the design guarantees a mismatch no CSS can fix.

```
node <skill>/scripts/crop.mjs --src raw.png --out design.png --x 0 --y <chrome-height> --width <full-width> --height <content-height>
```

Find `<chrome-height>` by eye in an image viewer, then confirm the crop kept only page content before writing the spec.

### Check the design's capture scale

A design exported from a 2x screen and downscaled has softer edges than anything Chromium renders at 1x, which puts a permanent few points on `diffPercent`. Test for it: scan one horizontal rule or one solid edge with `sample.mjs --scan col`. A crisp one-pixel transition means a 1x capture. A two-pixel ramp between the two colors means the design was downscaled from 2x. Pass `--dpr 2` to `check.mjs` in that case, so the page renders at 2x and gets averaged down through the same resampling the design went through.

## Step 2: Confirm the output format

Decide what kind of file you're building before you build it. Infer it from the project when you can: an existing `.tsx`/`.jsx` page next to the target path means a component in that framework; a `pages/` or `app/` router directory means a route file in that router's convention; a bare repo with no framework means a standalone `.html` file. Match the project's existing file extension, component style (function vs. class, named vs. default export), and location convention for pages of its kind.

Ask the user when none of that is inferable — no project (a fresh design with no target path given), or a project that mixes conventions (both `.html` and `.tsx` pages, or no existing page of this kind to pattern-match against). Ask specifically: standalone HTML file, or a component — and if a component, which framework and which directory. Guessing here is expensive to undo, because Step 1's selectors and Step 4's screenshot both target the format you pick.

## Step 3: Build the page

If the target page lives inside an existing project, look for its component library and design tokens first (a `components/` or `ui/` directory, a `theme.ts`/`tailwind.config.*`, an existing button or nav in another page). Reuse what already matches the design instead of writing new markup, because a hand-rolled `<button>` drifts from the project's real button the moment anyone touches either one. Match on function, not name: a design's pill-shaped filter chip can be the project's existing `Badge` or `Tag` component even if the design file calls it something else. Fall back to new markup only for pieces the project has no component for, and write those in the project's existing style (same styling approach — CSS modules, Tailwind, styled-components — same file layout).

Otherwise write plain HTML and CSS unless the repo already uses a framework. Put every token value from the spec into the CSS verbatim. Set `body{margin:0}`, and load every family listed in `fonts` with `@font-face` or a `<link>` plus a fallback stack.

When you write new markup, decompose it the way the design's own hierarchy suggests: one component or named block per repeated unit (a card, a nav item, a form row), not one flat wall of markup for the whole page. Follow the project's naming convention if it has one; otherwise use PascalCase for components, `handleX` for event handlers, and `onX` for event props. If the page has interactive states the design doesn't show by itself (loading, empty, error, hover, disabled), model each as its own explicit branch instead of a pile of boolean flags — see `references/ui-principles.md` for when the design leaves a state undetermined.

Read `references/ui-principles.md` when the image leaves a decision open. Open decisions include: the spacing step between two unlabeled blocks, the pairing of a heading with implied body copy, and the contrast a secondary text color needs.

## Step 4: Verify one round

Run exactly:

```
node <skill>/scripts/check.mjs --design <design.png> --page <page.html> --spec design-spec.json \
  --threshold <chosen> --layout-threshold <chosen> --reset
```

Drop `--reset` on later rounds so the round count carries over. Add `--dpr 2` when Step 1 found a downscaled design. The script writes its outputs to `.design-check/` unless you pass `--out-dir`.

The report names what to fix:

| Field | Use it for |
| --- | --- |
| `mismatches` | Exact token and box errors, each with expected and actual |
| `regions` | Diff percent inside each spec box, worst first |
| `gridTop` | The five worst 1/8-image cells, for damage outside every box |
| `layoutDiff` / `textDiff` | Whether the remaining error is layout or glyph rendering |
| `regressed` / `best` / `bestPage` | Whether this round made the page worse, and where the best page is saved |
| `stalled` | Two rounds in a row moved nothing |

Exit 0 is a pass. Exit 2 means fix and rerun. Exit 4 means the spec contradicts the design or has no boxes — fix the spec, not the page. Exit 6 means the script reached the round cap.

Convert a JPG design first with `sips -s format png design.jpg --out design.png` (macOS) or `magick design.jpg design.png`, because the diff script reads PNG only.

## Step 5: Fix only what the report names

Work one layer at a time, in this order, and do not start a layer while the one above it has an open error. A color fix inside a misplaced block cannot lower the diff.

1. **Geometry.** Fix every `box-*` mismatch. Each names the selector, the side, the expected pixel value, and the actual one.
2. **Type.** Fix every `font-loaded` mismatch, then every `font-size`. A loaded-but-wrong face shows as `widthRatio` off by more than 2% in `align.mjs` at the correct font size.
3. **Color.** Fix every remaining token mismatch.
4. **Position residue.** Take `regions` in order, worst first, then `gridTop` for damage outside every box.

Then:

- **Never guess a shift.** When a large glyph or block shows as a thick red outline (a "double image" of the same shape twice, slightly offset), measure it:

  ```
  node <skill>/scripts/align.mjs --design design.png --actual .design-check/round-N.png --rgb <hex of the element's fill> --y0 <top> --y1 <bottom>
  ```

  Bound `--y0`/`--y1` (and `--x0`/`--x1`) to the element's own area, because an unbounded scan mixes in other elements that share the color. Apply the printed `deltaX`/`deltaY` as a position change, and scale `font-size` by `widthRatio`/`heightRatio` when either is more than a few percent from 1. Guessing costs rounds: in one session, three guessed shifts moved the diff from 6.2% to 18.5% and back before a single measured pass landed it at 6.2% again.
- **Verify every lifted image the same way.** Run `align.mjs` bounded to the image's rect and require `deltaX`/`deltaY` within 2px and both ratios within 1%, because a crop placed by eye reads as a full ghost outline in the heatmap and never converges.
- **Revert on a regression.** When the report says `regressed: true`, restore `bestPage` before trying a different fix. Stacking a change onto a regression hides which change hurt. An earlier run went 8.4% → 9.13% → 8.4% and spent its third round undoing its second.
- **Change one thing per round.** Two untested shifts in one round hide which one helped.
- **Re-crop stale assets.** If a fix changes layout math an earlier crop depended on (a gap, a margin, a container edge), re-crop any asset made with `crop.mjs` whose `--x`/`--y` came from the old math. A stale crop still renders and looks right by eye, but its content sits at the design's old coordinates.

Rerun Step 4. Stop when the report passes, when `stalled` is true with zero mismatches and a small `layoutDiff`, or when exit 6 arrives. On exit 6, show the user the last heatmap, the remaining `mismatches`, the `layoutDiff`, and the `history` line, then ask whether to continue — five rounds without a pass means the spec or the design needs a human eye.

## Step 6: Report and keep the baseline

On pass, the script writes `<out-dir>/baseline.png`. Tell the user `layoutDiff`, `diffPercent`, the round count, the `passReason`, and the baseline path. Name every substitution: a missing font, a photo lifted from the design image, a guessed interactive state.

For a later regression check, capture at the baseline's size, then diff:

```
node <skill>/scripts/capture.mjs --page <page.html> --width 1440 --height 900 --out new.png
node <skill>/scripts/diff.mjs --design baseline.png --actual new.png --out diff.png
```

## Step 7: Open the built page

Open the final page in the default browser, so the user sees the live result, not just the report:

```
open <page.html>        # macOS
xdg-open <page.html>    # Linux
start <page.html>       # Windows
```

Do this once, after Step 6, whether the check passed or stopped at the round cap.

## Example

**Input:** "here's the landing page comp (comps/landing.png, 1440x900). build it as landing.html"

**Output, first report:**

```
{"round":1,"pass":false,"diffPercent":9.4,"layoutDiff":6.1,"textDiff":28.7,
 "mismatches":[{"selector":".hero","property":"box-y","expected":"96px","actual":"64px"},
               {"selector":"h1","property":"font-size","expected":"48px","actual":"40px"}],
 "regions":[{"label":".hero","percent":41.2}],"regressed":false,"stalled":false,
 "history":"1:9.4%/L6.1%/2tok"}
```

Fix `.hero` position first, then the font size. Rerun.

**Output, second report:** `"pass":true,"passReason":"layout matches; remaining diff is glyph rendering","diffPercent":8.1,"layoutDiff":1.2,"history":"1:9.4%/L6.1%/2tok 2:8.1%/L1.2%/0tok"`

## Gotchas

- A match declared by eye. The token and box checks exist because a 10% darker heading and a 60px shift both pass a glance. Never report "matches" without a passing `check.mjs` run.
- A spec with no boxes. Colors are the easiest thing to hit and prove nothing about layout. Four earlier runs held zero token mismatches while none of them matched its design.
- Chasing `diffPercent` past its floor. When `layoutDiff` is under 2% and `mismatches` is empty, the page is done. Further rounds move nothing.
- Vague tokens. `"expected":"dark gray"` compares as a string and always fails. Sample the image and write the hex with its `at` coordinate.
- Missing fonts. A missing font substitutes and shifts every line. List it in `fonts` so the check catches the fallback instead of leaving it as unexplained text diff.
- Browser chrome in the design image. A screenshot of a browser window is the design plus fixed UI the page will never render. Crop it out per Step 1.
- A design photo with no source asset. When the design has a photograph and no export of it exists, lift it out of the design image:

  ```
  node <skill>/scripts/crop.mjs --src design.png --out photo.png --x <x> --y <y> --width <w> --height <h> --matte <bg-hex>
  ```

  `--matte` turns pixels near the design's own background color transparent, so the lifted photo has no visible seam. Verify the placement with `align.mjs`, and name the substitution in the final report.
