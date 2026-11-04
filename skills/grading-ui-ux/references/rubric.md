# Grading rubric

Score every category on the 0-5 scale below. Use `null` when the input cannot show the category (a static screenshot cannot show loading states), because a guessed score misleads more than a gap. Cite principle IDs from `references/principles.md` in every piece of evidence.

## Contents

- [The 0-5 scale](#the-0-5-scale)
- [Categories](#categories)
- [What counts as evidence](#what-counts-as-evidence)
- [Context sets the bar](#context-sets-the-bar)

## The 0-5 scale

| Score | Anchor | Meaning |
|---|---|---|
| 0 | Absent or broken | The category is not addressed at all, or what exists actively harms use. |
| 1 | Major problems | The user is likely to fail or abandon the task because of this category. |
| 2 | Several noticeable problems | The user completes the task but with friction they would mention. |
| 3 | Adequate with clear gaps | Works; a designer would list two or three concrete fixes. |
| 4 | Good, minor polish left | One small, non-blocking improvement remains. |
| 5 | Exemplary | A reference example; nothing to change. |

Raise an item for every category scored 0 to 3. Leave 4 and 5 as strengths unless the user asks for a full polish pass, because options on a 4 cost review time for little gain.

## Categories

Grade all twelve. The principle IDs in the third column are the ones most often cited for the category; cite others when they fit better.

| # | Category | Primary principles | What to look at |
|---|---|---|---|
| 1 | Visual hierarchy | C1, L6, G5 | Is there one focal point? Does size, weight, and color order match task importance? |
| 2 | Layout and spacing | T5, T6, G1, G3 | Consistent base unit, aligned edges, grouping by proximity, breathing room. |
| 3 | Typography | T1, T2, T3, T4 | Scale discipline, measure, line height, minimum sizes. |
| 4 | Color and contrast | W1, W6, G2 | Measured contrast ratios, color never sole carrier, palette restraint. |
| 5 | Consistency and standards | N4, L4, G2 | Same component for same job, platform conventions, icon and label pairing. |
| 6 | Feedback and system status | N1, L7, C5 | Hover, active, loading, success, and error states visible. |
| 7 | Affordance and interaction clarity | L1, W2, N4 | Clickable things look clickable, targets large enough, disabled states clear. |
| 8 | Navigation and information architecture | L2, L8, N6, C4 | Option count, grouping, current-location marker, link scent. |
| 9 | Forms and error handling | N5, N9, W4, L3 | Labels, input constraints, inline error text, recovery path. |
| 10 | Accessibility | W1-W7 | Focus, names, alt, semantics, order. Overlaps with 4 and 9; score the technical conformance here. |
| 11 | Content and microcopy | C3, C4, N2 | Button verbs, plain language, tone, specific headings. |
| 12 | Responsiveness and adaptivity | L1, T1, G4 | Behavior across widths, touch targets, reflow. `null` for a single static screenshot. |

## What counts as evidence

- **Screenshot input.** Name the region ("top-right icon cluster", "the second card"). Estimate sizes from visible proportions and say so ("about 11 px, judged against the 16 px body"). Measure contrast only from sampled hex values you can state; otherwise write "appears below 4.5:1".
- **Code input.** Cite `file:line`. Quote the attribute or style that creates the problem (`outline: none` at `styles.css:42`). Report only what you read in the file, because plausible-sounding findings that are not in the code destroy trust in the whole review.
- **Both.** Prefer code evidence for technical categories (10, 6, 9) and screenshot evidence for perceptual ones (1, 2, 3, 4).

## Context sets the bar

Grade against the form factor and the real-world use recorded in `review.json` `context`, because the same pixel count is a strength on a 1440 px desktop and a failure on a 390 px phone.

- **Form factor and real estate.** Desktop web: mouse targets of 24 px pass (W2), multi-column layouts and persistent side panels are expected, hover states count as feedback. Mobile web and native mobile: 44 px targets (L1, W2), one column, thumb reach for primary actions (C2), no hover. Tablet: 44 px targets with two columns allowed. Kiosk or TV: 10-foot type sizes and focus-driven navigation (W3). Estimate the viewport from the screenshot's pixel size and name it in the evidence.
- **Real-world use.** Name what the product replaces and grade Navigation (8), Content (11), and Consistency (5) against that analog (C6). A food-ordering page is a restaurant menu joined to a storefront: sections, item codes, prices beside names, a visible order total. A dashboard is an instrument panel: status first, detail on demand. An option that breaks the analog needs a stated reason, because users arrive with that mental model already loaded.
