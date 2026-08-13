# Choice point (not presented — non-interactive run)

The target sits at
`workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`,
inside a plugin cache. Step 0 of scriptify rules that path ineligible: the next
plugin update silently clobbers any script written there. So Steps 1-3 ran
report-only against the cached copy, and the Step 4 apply gate was never opened
on it.

## What I would have asked

**Question 1 — the target is not writable in place. Copy it and continue?**

- **Copy into the project and apply there (Recommended)** — copy the skill to
  `.claude/skills/release-notes` in this project, then run Steps 5-9 on the
  copy. The plugin cache stays untouched.
- **Report only** — stop after the report above; write nothing anywhere.
- **Pick a different destination** — name one in Other.

**Question 2 — which rows to apply** (asked only after a copy is agreed):

- **Apply all 4 (Recommended)** — s1, s2, s3 to `scan_notes.py`; s5 to
  `render_notes.py`.
- **Apply a subset — list row ids in Other.**
- **Report only, write nothing.**

**Question 3 — keep verification residue** (fixtures and manifest) in the
target's `scripts/tests/` afterward?

- **No (Recommended)**
- **Yes**

## What the prompt already decided

The prompt says "apply whatever delegations you find", which pre-approves
applying. Per the run instructions, I picked the durable destination myself:

    /Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-9-ineligible-target/with_skill/workspace/.claude/skills/release-notes

It is writable, user-owned, inside the workspace boundary, and outside every
plugin cache path. All 4 SCRIPT rows were applied there. The prompt says
nothing about residue, so the recommended default "No" applied and
`.delegation-review/` was removed after the green smoke run.

The cached original at
`workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`
was not modified.
