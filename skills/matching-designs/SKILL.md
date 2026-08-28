---
name: matching-designs
description: Builds or fixes a web page so it matches a design image, then proves the match with a screenshot diff and a computed-style token check, looping fix-and-verify up to 5 rounds. Use whenever the user hands over a mockup, wireframe, comp, Figma export, screenshot, or PNG/JPG of a UI and wants it built, "make this look like the design", "match this mockup", "pixel-perfect this", "why doesn't my page look like the comp", "implement this screenshot", "does my page match the design", or wants a visual regression baseline for a page - even if they never say "design" and just attach an image next to "build this". Do NOT use to invent a design with no source image (use frontend-design or design), for component snapshot suites or a11y audits, or to diagnose a non-visual bug.
---

# Matching designs

Build a page that matches a design image, and prove it with numbers instead of a glance.

Claude's default is to look at the design, write plausible CSS, look at the result, and declare it close. "Close" hides a wrong heading color, a 16px gap that should be 24px, and a button one shade off. This skill replaces the glance with a measured loop: extract exact tokens, build, screenshot, diff, compare computed styles, fix only what the report names, repeat.

## Setup

Run once per machine, because the scripts need Playwright's Chromium and two npm packages:

```
cd <skill>/scripts && npm install && npx playwright install chromium
```

## Step 0: Ask the fidelity level

Before extracting the spec, ask the user which fidelity level to build to. Use `AskUserQuestion` with these options, each mapped to a `check.mjs --threshold` value:

| Level | diffPercent target | `--threshold` |
| --- | --- | --- |
| Low | 10-12% | `11` |
| Medium | 6-10% | `8` |
| High | 6% or lower | `6` |

Pass the chosen `--threshold` on every `check.mjs` call in Step 4 and Step 5. A higher threshold is not a shortcut — still fix every token mismatch and every heatmap region in Step 5, because the threshold only changes when the loop declares victory, not how carefully each round gets reviewed.

## Step 1: Extract the spec from the image

Read the design image. Write `design-spec.json` next to the target page with this shape:

```json
{"viewport":{"width":1440,"height":900},
 "tokens":[
  {"selector":"h1","property":"color","expected":"#1a1a1a"},
  {"selector":"h1","property":"font-size","expected":"40px"},
  {"selector":".cta","property":"background-color","expected":"#2563eb"},
  {"selector":"header","property":"height","expected":"64px"}
 ]}
```

Set `viewport` to the image's pixel size. `check.mjs` refuses any other value. Record 8-15 tokens:

- every text color
- every background color
- the font size of each text level
- the height of each fixed bar
- the gap of each grid or flex row
- the padding of the main container

Write exact values (`#2563eb`, `24px`), never descriptions, because the token script compares strings and numbers.

Sample colors and find element boundaries with `sample.mjs` instead of writing one-off pixel-scan scripts:

```
node <skill>/scripts/sample.mjs --src design.png --points '[["h1-color",40,60],["cta-bg",700,400]]'
node <skill>/scripts/sample.mjs --src design.png --scan row --at 150 --x0 0 --x1 1440
```

Point mode prints the hex at each labeled coordinate. Scan mode walks one row or column and prints where it crosses between background and content, so you get element edges in one call instead of eyeballing a crop or writing a fresh Node script per boundary.

Read `references/spec-extraction.md` when the image is a JPG with compression noise, has no obvious grid, or you cannot tell two similar colors apart.

Use selectors that will exist in the page you build. A selector that matches nothing stops the token check with exit 5.

If the image is a browser screenshot (a title bar, tabs, or an address bar are visible above the content), crop that chrome out before it becomes the spec image. `check.mjs` diffs the whole file, so a URL bar baked into the design guarantees a mismatch no CSS can fix. Crop with:

```
node <skill>/scripts/crop.mjs --src raw.png --out design.png --x 0 --y <chrome-height> --width <full-width> --height <content-height>
```

Find `<chrome-height>` by eye in an image viewer, then confirm the crop kept only page content before writing the spec.

## Step 2: Confirm the output format

Decide what kind of file you're building before you build it. Infer it from the project when you can: an existing `.tsx`/`.jsx` page next to the target path means a component in that framework; a `pages/` or `app/` router directory means a route file in that router's convention; a bare repo with no framework means a standalone `.html` file. Match the project's existing file extension, component style (function vs. class, named vs. default export), and location convention for pages of its kind.

Ask the user when none of that is inferable — no project (a fresh design with no target path given), or a project that mixes conventions (both `.html` and `.tsx` pages, or no existing page of this kind to pattern-match against). Ask specifically: standalone HTML file, or a component — and if a component, which framework and which directory. Guessing here is expensive to undo, because Step 1's token selectors and Step 4's screenshot both target the format you pick.

## Step 3: Build the page

If the target page lives inside an existing project, look for its component library and design tokens first (a `components/` or `ui/` directory, a `theme.ts`/`tailwind.config.*`, an existing button or nav in another page). Reuse what already matches the design instead of writing new markup, because a hand-rolled `<button>` drifts from the project's real button the moment anyone touches either one. Match on function, not name: a design's pill-shaped filter chip can be the project's existing `Badge` or `Tag` component even if the design file calls it something else. Fall back to new markup only for pieces the project has no component for, and write those in the project's existing style (same styling approach — CSS modules, Tailwind, styled-components — same file layout).

Otherwise write plain HTML and CSS unless the repo already uses a framework. Put every token value from the spec into the CSS verbatim. Set `body{margin:0}` and the fonts the design uses, with a fallback stack.

When you write new markup, decompose it the way the design's own hierarchy suggests: one component or named block per repeated unit (a card, a nav item, a form row), not one flat wall of markup for the whole page. Follow the project's naming convention if it has one; otherwise use PascalCase for components, `handleX` for event handlers, and `onX` for event props. If the page has interactive states the design doesn't show by itself (loading, empty, error, hover, disabled), model each as its own explicit branch instead of a pile of boolean flags — see `references/ui-principles.md` for when the design leaves a state undetermined.

Read `references/ui-principles.md` when the image leaves a decision open. Open decisions include: the spacing step between two unlabeled blocks, the pairing of a heading with implied body copy, and the contrast a secondary text color needs.

## Step 4: Verify one round

Run exactly:

```
node <skill>/scripts/check.mjs --design <design.png> --page <page.html> --spec design-spec.json --threshold <chosen-threshold> --reset
```

Drop `--reset` on later rounds so the round count carries over. The script writes its outputs to `.design-check/` unless you pass `--out-dir`. The script screenshots the page at the design's size, diffs it, and checks every token. It prints one JSON report with `diffPercent`, `mismatches`, a heatmap path, and the round history. Exit 0 is a pass. Exit 2 means fix and rerun. Exit 6 means the script reached the round cap.

Convert a JPG design first with `sips -s format png design.jpg --out design.png` (macOS) or `magick design.jpg design.png`, because the diff script reads PNG only.

## Step 5: Fix only what the report names

Work the report in this order, because token mismatches are exact and cheap while pixel diff is noisy:

1. Fix every entry in `mismatches`. Each one names the selector, the property, the expected value, and the actual value.
2. Open the heatmap PNG. Red regions show where pixels differ. A red band along one edge means an offset or a wrong height. The diff already discounts antialiasing, so red on text means the font, size, weight, or hinting differs.
3. When a large glyph or block shows as a thick red outline (a "double image" of the same shape twice, slightly offset), do not eyeball the shift. Measure it:

   ```
   node <skill>/scripts/align.mjs --design design.png --actual .design-check/round-N.png --rgb <hex of the element's fill> --y0 <top of region> --y1 <bottom of region>
   ```

   Bound `--y0`/`--y1` (and `--x0`/`--x1`) to the element's own area, because an unbounded scan mixes in other elements that share the color. Apply the printed `deltaX`/`deltaY` as a position change, and scale `font-size` by `widthRatio`/`heightRatio` if either is more than a few percent from 1. Guessing the shift instead of measuring it costs rounds: in one session, three guessed shifts moved the diff from 6.2% to 18.5% and back before a single measured pass landed it at 6.2% again.
4. Change only the CSS rules behind the red regions. Do not rewrite the page, because a rewrite discards the parts that already matched. Change one variable at a time and rerun, because stacking two untested shifts hides which one helped when the diff moves the wrong way.
5. If the fix changes layout math that an earlier crop depended on (a gap, a margin, a container edge), re-crop any asset made with `crop.mjs` whose `--x`/`--y` came from the old math. A stale crop still renders and can look identical to the design by eye, but its content sits at the design's *old* coordinates — comparing it against the new layout is comparing an asset against itself, not against the design, and the diff stays wrong no matter what else gets fixed.

Rerun Step 4. Stop when the report passes or exit 6 arrives. On exit 6, show the user the last heatmap, the remaining `mismatches`, and the `history` line. Then ask whether to continue, because five rounds without a pass means the spec or the design needs a human eye — and because a design photo with no source asset (see Gotchas) can hold `diffPercent` a few points above threshold even once the layout is right, so pushing further rounds may not be worth it.

## Step 6: Report and keep the baseline

On pass, the script writes `<out-dir>/baseline.png`. Tell the user the final `diffPercent`, the round count, and the baseline path. For a later regression check, capture at the baseline's size, then diff:

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
{"round":1,"maxRounds":5,"pass":false,"diffPercent":6.4,"threshold":3,
 "mismatches":[{"selector":"h1","property":"font-size","expected":"48px","actual":"40px"},
               {"selector":".hero","property":"padding-top","expected":"96px","actual":"64px"}],
 "history":"1:6.4%/2tok","baseline":null}
```

Fix: `h1{font-size:48px}` and `.hero{padding-top:96px}`. Rerun.

**Output, second report:** `"pass":true,"diffPercent":1.9,"history":"1:6.4%/2tok 2:1.9%/0tok","baseline":".design-check/baseline.png"`

## Gotchas

- A match declared by eye. The token check exists because a 10% darker heading passes a glance and fails the spec. Never report "matches" without a passing `check.mjs` run.
- Vague tokens. `"expected":"dark gray"` compares as a string and always fails. Sample the image and write the hex.
- Missing fonts. A missing font substitutes and shifts every line. Load the font with `@font-face` or a `<link>`. If the font stays missing, name the substitution in the report.
- Browser chrome in the design image. A screenshot of a browser window (tab bar, URL bar) is not the design — it's the design plus fixed UI the page will never render. Crop it out per Step 1 before writing the spec, or every round measures against pixels the page can't match.
- A design photo with no source asset. When the design has a photograph (a product shot, a portrait, a background image) and no export of it exists, lift it directly from the design image instead of leaving it out:

  ```
  node <skill>/scripts/crop.mjs --src design.png --out photo.png --x <x> --y <y> --width <w> --height <h> --matte <bg-hex>
  ```

  `--matte` turns pixels near the design's own background color transparent, so the lifted photo has no visible seam when placed on the built page's background. Name this substitution in the final report — it is a fallback, not a real asset, and it caps how low `diffPercent` can go if the crop misses part of the subject.
