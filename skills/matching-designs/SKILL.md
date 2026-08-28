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

Read `references/spec-extraction.md` when the image is a JPG with compression noise, has no obvious grid, or you cannot tell two similar colors apart.

Use selectors that will exist in the page you build. A selector that matches nothing stops the token check with exit 5.

## Step 2: Build the page

Write plain HTML and CSS unless the repo already uses a framework. Put every token value from the spec into the CSS verbatim. Set `body{margin:0}` and the fonts the design uses, with a fallback stack.

Read `references/ui-principles.md` when the image leaves a decision open. Open decisions include: the spacing step between two unlabeled blocks, the pairing of a heading with implied body copy, and the contrast a secondary text color needs.

## Step 3: Verify one round

Run exactly:

```
node <skill>/scripts/check.mjs --design <design.png> --page <page.html> --spec design-spec.json --reset
```

Drop `--reset` on later rounds so the round count carries over. The script writes its outputs to `.design-check/` unless you pass `--out-dir`. The script screenshots the page at the design's size, diffs it, and checks every token. It prints one JSON report with `diffPercent`, `mismatches`, a heatmap path, and the round history. Exit 0 is a pass. Exit 2 means fix and rerun. Exit 6 means the script reached the round cap.

Convert a JPG design first with `sips -s format png design.jpg --out design.png` (macOS) or `magick design.jpg design.png`, because the diff script reads PNG only.

## Step 4: Fix only what the report names

Work the report in this order, because token mismatches are exact and cheap while pixel diff is noisy:

1. Fix every entry in `mismatches`. Each one names the selector, the property, the expected value, and the actual value.
2. Open the heatmap PNG. Red regions show where pixels differ. A red band along one edge means an offset or a wrong height. The diff already discounts antialiasing, so red on text means the font, size, weight, or hinting differs.
3. Change only the CSS rules behind the red regions. Do not rewrite the page, because a rewrite discards the parts that already matched.

Rerun Step 3. Stop when the report passes or exit 6 arrives. On exit 6, show the user the last heatmap, the remaining `mismatches`, and the `history` line. Then ask whether to continue, because five rounds without a pass means the spec or the design needs a human eye.

## Step 5: Report and keep the baseline

On pass, the script writes `<out-dir>/baseline.png`. Tell the user the final `diffPercent`, the round count, and the baseline path. For a later regression check, capture at the baseline's size, then diff:

```
node <skill>/scripts/capture.mjs --page <page.html> --width 1440 --height 900 --out new.png
node <skill>/scripts/diff.mjs --design baseline.png --actual new.png --out diff.png
```

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
