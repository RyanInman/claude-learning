# abcop-ai-101

Training decks for Abcop, built from YAML specs by the `designing-slide-decks` skill in `.claude/skills/`.

## Layout

One deck per directory under `decks/`:

```
decks/claude-code-101/
  claude-code-101-spec.yaml            # the source of truth
  claude-code-101-spec-feedback.json   # studio notes
  outline.md                           # what the deck was written from
  assets/                              # images the spec points at
  dist/                                # build output — gitignored, disposable
```

Image paths in a spec resolve against the spec's own directory, so a deck folder can be moved or copied whole.

`decks/_archive/` holds specs kept for reference that no longer build.

## Design in the browser

Run from the repo root. macOS and Linux:

```bash
.claude/skills/designing-slide-decks/scripts/studio.sh              # port 4321
.claude/skills/designing-slide-decks/scripts/studio.sh <deck-name>  # decks/<deck-name>/<deck-name>-spec.yaml
PORT=4322 .claude/skills/designing-slide-decks/scripts/studio.sh    # a different port
```

Windows:

```powershell
.claude\skills\designing-slide-decks\scripts\studio.ps1
.claude\skills\designing-slide-decks\scripts\studio.ps1 <deck-name>
$env:PORT = 4322; .claude\skills\designing-slide-decks\scripts\studio.ps1
```

The deck name can be dropped while `decks/` holds exactly one deck.

Pick a theme and pacing, edit slide text in place, and leave notes for Claude in the feedback box. Nothing is written until you press **Save + build**, which rewrites the spec and rebuilds into that deck's `dist/`.

**Apply notes** hands every open feedback note to a headless Claude run: it edits the spec, resolves the notes it applied, rebuilds the deck, and the page reloads onto the result. It asks first, refuses while you have unsaved picks, and each press is a real Claude run that costs money. Needs `claude` on PATH, or `CLAUDE_BIN` pointing at it.

The studio watches the spec file. When it changes on disk — Claude applying your feedback, an editor save — the page refreshes itself. If you have unsaved picks in the browser it says so rather than reloading over them; **Revert** loads the version on disk when you are ready.

## Build from the CLI

```bash
node .claude/skills/designing-slide-decks/scripts/build_deck.js decks/claude-code-101/claude-code-101-spec.yaml
```

Writes `dist/claude-code-101.html`, `.pptx`, and `-contact-sheet.html` beside the spec, and reports any slide whose content overflows the safe area. Read open studio notes with `scripts/feedback.js <spec>`.

Never edit files in `dist/` — change the spec and rebuild.

## Known gap

`claude-code-101-spec.yaml` still carries 37 `[TODO: …]` markers in its final section (Abcop Playbooks). They render visibly in the built deck and need real content before it is presented.
