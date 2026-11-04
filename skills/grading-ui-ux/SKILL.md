---
name: grading-ui-ux
description: Grades a screenshot or frontend UI code (HTML, CSS, React, Vue, Svelte, SwiftUI, Flutter) against founding UI/UX principles on a 0-5 scale per category, then offers 2-3 principle-backed fix options per weak item in an HTML page the user picks from, iterates on a finalized design mock, and turns the agreed design into a reviewed implementation plan. Use whenever the user shares a screenshot, mockup, or UI file and asks to grade, score, rate, review, critique, audit, or improve its UI, UX, design, usability, accessibility, layout, or "how does this look", even if they never say "grade" or "UX". Also use for "give me design options", "what would a designer change", "is this accessible", "make this page look better". Do NOT use to build a page from a design image with no critique step (use matching-designs), to visually edit a screen by hand (use generating-wysiwyg-editors or visual-page-builder), or for non-UI code review.
---

# Grading UI/UX

Grade a screen, offer options per weak item, let the user choose in an HTML page, converge on a finalized design, then plan and execute the code change. The loop is: grade → options page → selections saved to disk → decisions page → final design mock → another round or implementation plan. Every page is a local HTML file served from the scratchpad, never a claude.ai artifact, because the user reviews in their own browser and keeps the files.

Read `references/rubric.md` before grading and `references/principles.md` before writing options. Every score and every option cites principle IDs from that file, because a critique without a principle is taste and the user cannot argue with taste.

## Workflow

### Step 0: Before starting

Confirm these before grading, because a wrong answer here redoes the whole round:

1. What is the input: screenshot paths, code paths, or both? Read every screenshot with the Read tool and every code file in full.
2. What is the scope: the whole screen or one component? Grade only what the user named.
3. Is there code to modify at the end? Screenshot-only input ends in a build spec, not a code plan.
4. Any fixed constraints: brand colors, design system, framework? Options must stay inside them.
5. What is the form factor and screen real estate: desktop web, mobile web, native iOS or Android, tablet, kiosk? Estimate the viewport from the screenshot's pixel size or the code's breakpoints. A 36 px button passes on desktop and fails on a phone, so the same screen earns different scores and different options per form factor.
6. What does the application do in the real world, and what established thing does it replace? Name the analog and design toward it: a food-ordering page is a restaurant menu joined to an online storefront, a banking app is a statement plus a teller window. Options that break the analog need a stated reason (C6).

Extract answers from the conversation first. Ask only for what is missing. If all six are known, proceed without asking. Record 5 and 6 in the `context` field of `review.json`, because the script refuses a review without them and renders them above the scorecard.

### Step 1: Inventory the components, then grade

Before scoring, list every component on the screen and write your best understanding of what each one does: the user action it takes, what it triggers or navigates to, the state it reflects, and how sure you are. Mark confidence `stated` when a label, code, or tooltip says it, `inferred` when platform convention says it, `unknown` when you are guessing. Record the list in the `components` field of `review.json`, because a redesign that drops a control nobody understood breaks a job the user still has, and the script renders the inventory so the user can correct a wrong guess before choosing options.

Infer function from evidence, not from wishful reading: a button labelled "Customize" on every menu item probably opens an options dialog that ends in an add, so its `does` says that and its confidence is `inferred`. When the code is available, read the handler and cite it.

Score all twelve rubric categories using the 0-5 anchors in `references/rubric.md`. Write one or two sentences of evidence per category with principle IDs. For code input cite `file:line` and quote the offending attribute or style. For screenshot input name the region. Report only what you observed in the image or file, because a plausible finding that is not there costs the user's trust in every other finding.

Score `null` for a category the input cannot show. A static screenshot cannot show loading states or responsiveness.

### Step 2: Write options

For every category scored 0-3, write 2 or 3 options. Each option needs:

- **Change.** The concrete edit: values, sizes, copy, structure.
- **Reasoning.** Why this change raises the score, tied to named principle IDs.
- **Projected score.** The 0-5 score after the change.
- **Preview.** A self-contained HTML snippet (inline styles only) showing the affected region after the change. Keep it under about 40 lines and 220 px tall.
- **Affects.** The component names from the inventory this option changes, removes, or merges. The script refuses a name not in the inventory. For each affected component, the `change` text says where its job goes: kept as is, moved to another component, or dropped with a reason. A redesign may change how a job is done, never lose the job silently.

Order items worst score first. When more than 6 categories score 0-3, ask the user whether they want all of them or only the worst 6, because a 12-item page with 25 radio buttons buries the decisions that matter.

Give each concrete change one home. When a fix serves two categories (removing Cancel and Reset serves both Consistency and Navigation), put it in the lower-scored item and have the other item's evidence point to it, because duplicated options make the user decide the same thing twice.

Mark exactly one option recommended and say why in one sentence. Make the options differ in scope, not in wording: a minimal fix, a full fix, and sometimes a rethink. Pick the recommended one by principle coverage per unit of change, because the user chooses by trade-off, not by which sounds nicest.

Write the result to `review.json` in the scratchpad using the schema in `references/review-schema.md`. Add a `current_preview_html` per item when the current state can be mocked in a few lines. The script renders it as the last card of every item, titled "Change nothing", with its own radio button, so the user weighs doing nothing against each option and the real options still lead.

### Step 3: Build and show the options page

Run exactly:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/build_review.py review.json -o options.html
```

The script validates the JSON and prints each error with the item and field, so fix the JSON and rerun until it reports success. Then serve and open the page:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/serve.py <scratchpad dir> options.html
```

The script starts one local server per directory, reuses it on later calls, opens the page in the default browser, and prints the URL. Put that URL in the terminal reply. Do not publish any review page as a claude.ai artifact, and do not open the file with `file://`, because the Save button needs the server.

The page opens with the reviewed screenshot beside the context and scorecard, then one collapsible section per item (the first open, the rest closed) whose summary line shows the current pick, so the user sees the whole screen and every score before any option. Every preview and the screenshot have an Expand button that opens them full screen with a zoom control, so the user can inspect a 220 px snippet at 150 to 300 percent. The bottom bar has a "Save selections" button that writes `selections.txt` next to the page (`options-2.html` writes `selections-2.txt`). There is no copy button, because a pasted string is one more place for a typo.

In the terminal, list the items with their scores and the recommended option per item, then ask the user to click Save selections and say "saved". The file holds one line in the form `1B, 2A, 3-`, where `-` means Change nothing.

### Step 4: Record decisions

Read `selections.txt` from the scratchpad (`cat`). It holds one line like `1B, 2A, 3-`. If the file is missing, ask the user to click Save selections. Run exactly:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/build_review.py review.json --selections "1B,2A,3-" -o decisions.html
```

Open it with `serve.py <scratchpad dir> decisions.html`. This is the saved record of finalized options; keep it unchanged after this point, because later rounds reference it.

### Step 5: Show the finalized design

Write `final-design.html` by hand: a mock of the whole reviewed screen with every chosen change applied, followed by a short "What changed" list that maps each decision (`1B`, `2A`) to a principle. Reuse the chosen `preview_html` snippets and the original input as the base. Mock it at the form factor from `context`: a phone screen at phone width, a desktop app at desktop width. Open it with `serve.py <scratchpad dir> final-design.html`.

Then ask in the terminal: accept this design, or run another round? For another round, treat `final-design.html` as the new input and return to Step 1. Number rounds in file names (`review-2.json`, `options-2.html`) so earlier pages stay intact.

### Step 6: Plan the implementation

When the user accepts the design and code exists:

1. Write a plan that lists, per decision, the file, the exact edits, and the principle it serves.
2. Add a verification step per decision: a measured contrast ratio, a rendered screenshot, an axe or Lighthouse check, or a test.
3. Present the plan in the terminal and wait for the user's review. Revise on request.
4. After approval, offer to execute. Execute only on a yes, because the plan is the user's last checkpoint before files change.

Screenshot-only input: write a build spec instead (component list, tokens, copy), and offer to generate the code from it.

## Example

Use this terminal shape every round, because the user reads the terminal before the page.

Input: user shares `login.html` and says "rate this login page and tell me how to fix it".

Output, abbreviated:

```
Graded: Login page (code)
Context: desktop web, about 1280 px wide · Real-world use: sign-in gate for a SaaS admin tool (analog: a reception desk, one question then through)
Scorecard: 1 Visual hierarchy 3 · 2 Layout 3 · 3 Typography 2 · 4 Color 1 · 5 Consistency 4 · 6 Feedback 2 · 7 Affordance 3 · 8 Navigation 4 · 9 Forms 1 · 10 Accessibility 1 · 11 Content 3 · 12 Responsiveness 2

Items raised, recommended in bold:
4. Color and contrast (1): A darken helper text / **B darken + text 'Required' label** / C new palette
9. Forms (1): A add visible labels / **B labels + inline error text + autocomplete** 
10. Accessibility (1): **A restore focus ring and add aria-labels** / B full semantic rewrite
...
Options page: http://127.0.0.1:52113/options.html
Click Save selections on the page, then say "saved"
```

Item 4, option B in `review.json`:

```json
{"key":"B","title":"Darken helper text and add a 'Required' label",
 "change":"Helper and placeholder color #9aa0a6 -> #5f6368 (7.0:1 on white); replace the red asterisk with the word 'Required' after the label.",
 "reasoning":"Fixes contrast (W1) and color-only meaning (W6); a text label survives grayscale and screen readers (W4).",
 "principles":["W1","W6","W4"],"projected":5,"recommended":true,"affects":["Required marker","Helper text"],
 "why_recommended":"Clears every cited violation for one extra word per field.",
 "preview_html":"<div style='font:14px system-ui;padding:16px'><label style='display:block;color:#1a1d23'>Email <span style='color:#5f6368'>Required</span></label><input style='width:100%;padding:8px;border:1px solid #777' placeholder='you@example.com'><p style='color:#5f6368;margin:4px 0 0'>We never share your email.</p></div>"}
```

## Gotchas

- `preview_html` renders inside a sandboxed iframe with no page CSS, so external stylesheets, classes from the user's app, and scripts do nothing there. Inline every style.
- The script needs exactly one `recommended: true` per item and 2-3 options; it refuses the file otherwise. Read its stderr instead of guessing.
- Items are the categories scored 0-3 only. Writing options for a 4 doubles the page for no decision the user wants to make.
- Grade the code the user gave, not the framework's defaults. A React component with no styles shown gets `null` on perceptual categories, not a low score.
- Do not estimate a contrast ratio to one decimal from a screenshot. Write "appears below 4.5:1" unless you sampled the hex values.
- Keep each round's files separate (`review-2.json`). Overwriting round 1 loses the decisions record the user already saw.
- Pillow is usually not installed, so hex sampling from a screenshot fails. Say "appears below 4.5:1" rather than installing packages mid-review.
- In Step 6, do not start editing files on "looks good" about the design. The plan review is a separate yes.
- `serve.py` writes `.serve.json` next to the pages and leaves the server running for the session, so a later round reuses the same port and earlier URLs keep working. Pass the directory, not a file, as its first argument.
- `serve.py` also accepts `POST /selections?name=<file>.txt` and writes the body into the served directory. A stale server from an older skill version has no POST handler, so `serve.py` replaces it when `.serve.json` lacks the current `version`.
- Read `selections.txt` fresh each round. The Save button overwrites it, so a stale read from round 1 would replay old choices into round 2; later rounds write `selections-2.txt`.
- Never publish review pages with the Artifact tool, even when it is available, because the page cannot send selections back and the user wants the files locally.
- Fill `components` before writing options, not after. Options written first describe the look; options written against the inventory describe what still has to work, which is what the user is deciding.
- Do not grade a phone screenshot by desktop norms or the reverse. Check `context.form_factor` before scoring Affordance (7), Layout (2), and Responsiveness (12).
