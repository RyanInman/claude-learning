# Scriptified: `release-notes`

## First, a blocker on where to write

The skill lives in a plugin cache:

```
workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes/
```

Claude Code owns that directory. It is rewritten whenever the `release-tools`
plugin updates or is reinstalled, so a script and an edited `SKILL.md` placed
there would vanish without warning. I did not write to it.

Instead I applied the change to your personal skills directory:

```
workspace/.claude-personal/skills/release-notes/
```

That copy is durable, and a user-level skill shadows the plugin's copy of the
same name, so the scriptified version is the one that runs. If you would rather
upstream this to the `release-tools` repo or scope it to a single project, the
whole folder moves as-is — see `gate.md` for the other destinations I
considered.

## What got delegated

The workflow had five steps. Four are deterministic and now live in
`scripts/build_notes.py`; one is judgment and stays with the model.

| Original step | Verdict | Where it lives now |
| --- | --- | --- |
| 1. List every `.md` in `notes/`, sorted, and count | Deterministic | `build_notes.py` — `FILES` / `VALID` |
| 2. Check each file starts with `PR #<number>:`, record failures | Deterministic | `build_notes.py` — `MALFORMED` |
| 3. Group by `type:` and count each group | Deterministic | `build_notes.py` — `COUNTS` |
| 4. Write a two-sentence customer-facing summary | **Judgment** | Stays in `SKILL.md` step 4 |
| 5. Render a markdown list, grouped by type, PR number ascending | Deterministic | `build_notes.py` — `--- NOTES ---` block |

Step 4 is the only step whose answer changes with the input's meaning rather
than its shape, so it is the only one a script would get wrong.

## The script

`scripts/build_notes.py` — one entry point, no flags, optional positional
argument for a notes directory other than the sibling `notes/`.

Run against your three fixture files:

```
$ python3 scripts/build_notes.py
FILES: 3
VALID: 2
MALFORMED: pr-104.md
COUNTS: feat=1 chore=1

--- NOTES ---
### Features
- #101 Add widget batch endpoint

### Chores
- #109 Bump lockfile
```

That immediately caught a real defect in the fixtures: `pr-104.md` starts with
`Merged 104: Fix pagination off-by-one`, not `PR #104:`. Step 2 of the old
workflow asked the model to notice this by eye every single run. Now it fails
loudly and consistently.

Three design decisions worth your review:

- **Malformed files are excluded from the rendered list, not guessed at.** The
  script could regex `104` out of `Merged 104:`, but a wrong PR number in a
  published changelog is worse than a visibly missing entry. Fix the first line
  of `pr-104.md` and rerun; the fix count becomes `fix=1` and the entry appears.
- **Unknown `type:` values are kept, not dropped.** `feat`, `fix`, and `chore`
  render first in that order; anything else renders after them under its raw
  name. A typo like `type: fixes` becomes its own visible group instead of
  silently disappearing.
- **A missing notes directory exits 1.** An empty milestone and a wrong path
  look identical in the output otherwise.

## The rewritten `SKILL.md`

Steps 1-3 and 5 collapsed into "run this, quote what it prints". Two
instructions carry their reason, because you will want to generalize them:

- Quote the `FACTS` numbers verbatim rather than recounting, because a second
  count can disagree with the rendered list.
- Report the `MALFORMED` filenames to the user, because those entries are
  absent from the notes and someone has to fix the source file.

I also added a Gotchas section covering the three decisions above. The
frontmatter `description` is unchanged — it triggers correctly as written.

## Verification

- `python3 scripts/build_notes.py` on the real `notes/` → exit 0, output above.
- Empty directory → exit 0, `FILES: 0`, empty notes block.
- Nonexistent directory → exit 1, `error: notes directory not found: …`.

## Next

1. Fix the first line of `notes/pr-104.md` to `PR #104: Fix pagination
   off-by-one` so the fix ships in the changelog.
2. Decide whether this belongs upstream in the `release-tools` plugin. Right
   now your local copy and the plugin's copy will drift.
