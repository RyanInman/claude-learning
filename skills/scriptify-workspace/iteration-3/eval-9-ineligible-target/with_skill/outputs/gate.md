# Choice point presented (AskUserQuestion)

The target sits in a plugin cache
(`workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`),
so it is ineligible: the next plugin update silently clobbers any script written
there. Steps 1-3 ran report-only. The Step 4 apply gate is not opened on the
original. What I would have asked instead:

## Question 1 — ineligible target: copy it?

**Header:** Ineligible target

The release-notes skill lives in a plugin cache, so I cannot write scripts into
it. Copy it into the project and continue from Step 4 on the copy?

| Option | Description |
|---|---|
| Copy into the project and continue (Recommended) | Copy the skill to `workspace/.claude/skills/release-notes`, then apply the delegations to that copy. The plugin-cache original stays untouched. |
| Report only, write nothing | Keep the report above and stop. No copy, no scripts. |
| Other | Name a different destination for the copy. |

## Question 2 — which rows to apply (on the copy)

**Header:** Rows to apply

4 SCRIPT rows, so one option per row, `multiSelect: true`, all marked
(Recommended), defaulting to all four:

| Option | Description |
|---|---|
| s1 — list and count notes (Recommended) | `scan_notes.py` |
| s2 — check `PR #<number>:` header (Recommended) | `scan_notes.py` |
| s3 — group and count by `type:` (Recommended) | `scan_notes.py` |
| s5 — render grouped markdown list (Recommended) | `render_notes.py` |

s4 (two-sentence customer summary) is CLAUDE and is not offered.

## Question 3 — keep verification residue

**Header:** Keep residue

Keep the fixtures and manifest in the copy's `scripts/tests/` afterward?

| Option | Description |
|---|---|
| No (Recommended) | Delete `.delegation-review/` after a green smoke test. |
| Yes | Install fixtures, manifest, and a vendored `smoke_test.py` under `scripts/tests/`. |

## What the prompt decided

`prompt.txt` says "apply whatever delegations you find", so:

- Question 1 → copy into the project and continue. Nothing is written into the
  plugin cache.
- Question 2 → all four SCRIPT rows selected.
- Question 3 → not decided by the prompt, so the default "No" applies.
