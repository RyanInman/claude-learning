---
name: designing-slide-decks
description: Turn a talk outline, presentation plan, training agenda, or rough notes into a designed slide deck the user picks the look of in their browser, then export both a self-contained HTML deck and a .pptx from one spec. Use this whenever someone wants slides built or redesigned and cares how they look - "turn this outline into a deck", "make me slides from these notes", "design a presentation", "build a deck for this talk", "restyle my deck", "show me some design options for these slides", "let me pick a theme" - and whenever they ask to preview, tweak, or rebuild a deck that was previously generated from a deck spec. Also use it when they hand over a markdown outline and just say "make this presentable" or "turn this into a talk", even if they never say the words slides, deck, or design. Do NOT use it to write the outline itself (draft that first, then come back), to edit an existing .pptx that has no spec, or to build a live web page rather than slides.
---

# Outline → designed deck

The user brings an outline. They leave with a deck they chose the look of, in two formats, plus the spec that regenerates both.

The pipeline is deliberately three separate things:

1. **Author the spec** (judgment) — read the outline, decide what each slide says and which elements carry it.
2. **Pick the design** (the user's call) — `studio.js` renders real slides in their browser so they choose a look by seeing it, not by reading adjective lists.
3. **Build** (deterministic) — one spec renders to `deck.html` and `deck.pptx` through a shared layout engine.

Because layout is computed once and drawn twice, the .pptx cannot drift from the browser preview. That is the reason for the split, and it is why **all content and design fixes go in the spec** — never patch the generated files, and never edit a renderer to change what a deck says.

## Step 0: before starting

Answer these from the conversation and the outline before asking the user anything. Ask only about what is genuinely missing, in one batch:

- **Source outline** — which file? If it is not obvious, ask.
- **Audience and setting** — an internal training, a conference talk, and a client pitch want different densities.
- **Runtime** — drives slide count. Roughly one slide per 1–2 minutes of speaking.
- **Where the deck will be presented from** — the HTML deck if they present from a laptop, the .pptx if it has to land in someone else's hands. Build both regardless; this only changes which you QA hardest.
- **Brand constraints** — an existing palette or font list narrows or replaces the theme choice.

If the outline answers all of it, say what you inferred in one line and start work. Do not open with a questionnaire when the outline already told you.

## Where files live

One deck is one directory, `decks/<name>/`, holding everything it needs:

```
decks/claude-code-101/
  claude-code-101-spec.yaml            # the source
  claude-code-101-spec-feedback.json   # studio notes, written beside the spec
  outline.md                           # what the deck was built from
  assets/                              # images the spec points at
  dist/                                # generated, gitignored, disposable
```

**Image paths resolve against the spec file's directory**, so a spec and its `assets/` move together and the paths never need editing. The builder writes `<specdir>/dist/<title-slug>.{html,pptx}` plus the contact sheet unless `--out` says otherwise; the studio's Save + build lands in the same place. Everything under `dist/` is regenerable — never edit it, never commit it.

## Stage 1 — Plan the sections

Read the outline in full first. Map its top-level headings to deck sections and propose the slide budget for each:

```
1. Installing Claude Code      → 2 slides   (title, 3 options)
2. How Does It Work?           → 4 slides   (turns, context window, 3 states)
3. Getting it Just Right       → 6 slides   (5 S's, before/after, setup, memories)
4. Good Practices              → 5 slides   (models, plan mode, context commands)
                                 17 slides ≈ 25 min
```

Show this and get agreement before writing any slides. A wrong section budget wastes far more work than a wrong slide.

Watch for outline content that is not yet real — `<come up with example>` placeholders, unstaged screenshots, commands the author never filled in. List these explicitly now and ask whether to invent them or mark them. Anything unresolved goes into the spec as visible `[TODO: …]` text so it cannot silently ship.

## Stage 2 — Draft the spec, section by section

Write `decks/<deck>/<deck>-spec.yaml`. Read `references/spec-format.md` for the element vocabulary, the layout model, and the capacity limits before writing the first slide. `assets/example-spec.yaml` is a full worked spec covering most of the vocabulary — read it when the reference leaves you guessing how elements combine.

**Gate after each section.** Draft one section's slides, build the contact sheet, and show the user that section before starting the next:

```bash
node <skill>/scripts/build_deck.js decks/<deck>/<deck>-spec.yaml
open decks/<deck>/dist/<deck>-contact-sheet.html
```

Then say which slides you added and what you are unsure about, and wait. Section-level gates exist because a structural habit you get wrong — every slide a bullet list, speaker notes too thin, the running example abandoned halfway — is cheap to correct after three slides and expensive after twenty.

When nobody is there to answer (an automated run, a subagent, an eval), do not stall waiting for a gate. State the assumption you are proceeding under, keep going, and collect the open questions for the end.

Authoring guidance:

- **Vary the layout across slides.** A deck where every slide is a bulleted list reads as unmade. Comparisons → two `code` panels or two `cards` in `columns`; option menus → `cards` with the recommended one marked `emphasis: true`; step lists → `icon_rows`; a single big claim → a two-line `title` plus a `callout`; openers and closers → a `dark` background.
- **Put the talking on the slide's `notes`, not the slide.** The outline's spoken lines, asides, and timing cues belong in `notes`. Slides carry the skeleton the audience reads in three seconds.
- **Keep the outline's running examples running.** If the outline uses one login-bug example across four slides, do not swap in a fresh example halfway — a reused example is what makes a section feel authored.
- **Offer layout variants where the arrangement is genuinely arguable**, using the `variants:` block (see the reference). Two or three per deck, on the slides that carry the most weight. Variants on an obvious title slide just spend the user's attention.

## Stage 3 — Let the user choose the design

```bash
node <skill>/scripts/studio.js decks/<deck>/<deck>-spec.yaml
```

The wrappers do the same thing plus open the browser and clear a stale studio off the port — `<skill>/scripts/studio.sh <deck>` on macOS and Linux, `<skill>\scripts\studio.ps1 <deck>` on Windows. Run them from the project root; a bare deck name expands to `decks/<deck>/<deck>-spec.yaml`, and with exactly one deck the name can be dropped.

It serves `http://127.0.0.1:4321` on loopback only and writes nothing until the user presses **Save + build**. It watches the spec, so a change you make on disk while it is open refreshes the page by itself — no restart, and no need to tell the user to reload. If they have unsaved picks in the browser, or the studio is holding text edits of theirs, it says the spec changed instead of reloading over their work; **Revert** then loads the version on disk. A spec you leave mid-edit or broken shows the parse error and keeps the last good version on screen. Tell them what they are looking at:

- **Theme** — four colour and type pairings, each rendered on whichever slide they have selected.
- **Pacing** — how much air and how large the type; the same content at three densities.
- **Edit** — any layout variants for that slide, click-to-edit on the slide's text, and a **feedback box** for anything they cannot fix by typing on the slide.

The feedback box is the important one. Tell the user plainly: **write what you want changed in your own words — you are talking to Claude, not filling in a form.** "These cards feel cramped", "cut the Simon Says bit, it lands flat", "this should be two slides" are all exactly right. Notes save the instant they press Add note, and the slide list marks which slides have open ones.

## Stage 3b — Apply the feedback

The user can also press **Apply notes** in the studio, which runs this stage without you: it starts a headless `claude -p` session in the project directory that reads the notes, edits the spec, resolves what it applied, and rebuilds. The page then reloads onto the new deck. That run is a fresh session — everything it needs has to be in the spec, the notes, and this file. It refuses to start while the studio holds unsaved edits, since it reads the spec from disk.

When the user says they are done in the studio (or asks you to apply their notes), read them:

```bash
node <skill>/scripts/feedback.js <deck>-spec.yaml
```

Notes are grouped by slide. Exit code 3 means there is nothing open, so there is no need to guess whether they left anything.

Work through them one at a time, editing the spec — feedback is a change request against the spec, exactly like any other edit. Then rebuild, and close out what you did:

```bash
node <skill>/scripts/feedback.js <deck>-spec.yaml --resolve <id>   # one note
node <skill>/scripts/feedback.js <deck>-spec.yaml --resolve-all    # all of them
```

Resolve a note only once the change is actually in the spec and the deck rebuilds clean. If a note is ambiguous or you disagree with it, leave it open and raise it with the user rather than resolving it silently — an unresolved note is visible in the studio, a wrongly-resolved one disappears.

Report back per note: what you changed, or why you did not. Notes the user phrased as a symptom ("slide 12 feels heavy") usually have several possible fixes; say which one you picked.

Point them at a content-heavy slide before they judge a theme. Themes all look fine on a title slide; they differentiate on the slide with three cards and a terminal panel.

Do not pick the theme for them and present it as done. Choosing the look is the part of this job that is theirs, and seeing four real slides side by side is the whole reason the studio exists.

## Stage 4 — QA, then deliver

The builder prints every slide whose content runs past the safe area. **Overflow is a defect, not a warning** — fonts are fixed size, so overflowing text runs off the slide rather than shrinking. Fix it by shortening or splitting in the spec, then rebuild.

Look at the deck before delivering it. Open the contact sheet and check for: text colliding with text, a card row that is mostly empty space, a code panel whose lines are cut off, a slide that is 80% blank.

If slides look top-heavy — content stopping well short of the bottom edge — set `vcenter: true` in the `design` block rather than padding each slide with spacers. It centres each composition optically and leaves full slides alone.

Deliver all three files and say plainly what each is for:

- `decks/<deck>/dist/<deck>.html` — present from a browser; arrow keys move, `N` toggles speaker notes.
- `decks/<deck>/dist/<deck>.pptx` — hand to anyone who needs a PowerPoint file; speaker notes travel with it.
- `decks/<deck>/<deck>-spec.yaml` — **the source.** Change it, rerun the builder, and the change appears in both outputs. The two files above are build output; a rebuild replaces them.

## Edit-loop requests

When the user asks for a change to a built deck ("cut slide 6", "make the CLI card the recommended one", "these two should be side by side"), edit the spec and rebuild. Layout requests are spec edits too: wrap elements in `columns`, reorder the list, pin with `at:`. Never edit the `.pptx` or `.html` — they are build artifacts and the next rebuild overwrites them.

For a restyle with no content change, skip straight to Stage 3.

## Gotchas

- **Hex colours never take a `#`.** A `#`-prefixed colour produces a .pptx that PowerPoint reports as corrupt. The builder rejects them, but hand-written overrides are where they sneak in.
- **`code` lines do not wrap.** A long line is silently clipped at the panel edge. Break console lines by hand.
- **Fonts must be on the safe list** (`themes.js`). A font only you have looks right in your browser and substitutes to something else on the machine the deck is presented from.
- **Saving in the studio rewrites the spec through a YAML dump, which drops comments.** Keep notes for yourself in `meta:` or in slide `notes:`, not in YAML comments.
- **Auto-numbers are not editable.** The digits on a `numbered` list come from position, not from the spec, so reorder the `items` instead of trying to retype a number.
- **The studio serves on loopback only.** It rewrites files on disk and **Apply notes** starts an agent that can edit the repo, so do not expose the port. Every POST it accepts carries a per-run token minted into the page, which is what stops another site's page from firing those requests at the port behind the user's back.
- **Apply notes needs `claude` on PATH.** Set `CLAUDE_BIN` to the full path if it is not (a shell alias will not do — the studio spawns the binary, not a shell).
- **`scripts/node_modules` is vendored and committed.** The scripts load their deps through hardcoded `__dirname` joins (`build_deck.js:11`, `render_pptx.js:9`), so the tree has to stay inside `scripts/`. If it needs reinstalling, run `npm install` **from inside `scripts/`** — installing at the repo root puts it where nothing can find it.

## Worked example

Outline fragment:

```markdown
## 3 Install Options
- Claude Desktop
  - Best for viewing artifacts
- VS Code Extension
  - Best for working in code
- Claude Code CLI
  - Most fancy features

This training will focus on Claude Code CLI
```

Spec — three cards, the one the talk is actually about marked, and the outline's framing sentence moved into the notes where it belongs:

```yaml
- kicker: "01 · Surfaces"
  title: "Three ways to run Claude"
  elements:
    - type: cards
      cards:
        - icon: star
          name: "Claude Desktop"
          sub: "Best for artifacts"
          rows: [{label: "Use it for", text: "Reading output, sharing results", labelColor: ok}]
          tag: "Casual"
        - icon: layers
          name: "VS Code"
          sub: "Best inside code"
          rows: [{label: "Use it for", text: "Editing specific sections inline", labelColor: ok}]
          tag: "Daily driver"
        - icon: terminal
          name: "Claude Code CLI"
          sub: "Most capable"
          emphasis: true
          rows: [{label: "Use it for", text: "Skills, hooks, subagents, everything", labelColor: ok}]
          tag: "This training"
          tagStyle: solid
  notes: >-
    We'll focus on the CLI, but most of these principles apply across all three.
    I'll call out where they differ.
```
