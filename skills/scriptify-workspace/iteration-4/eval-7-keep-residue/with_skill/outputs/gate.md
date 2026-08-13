# Step 4 gate — the choice point (asked with AskUserQuestion, both questions in one call)

## Question 1 — Which rows to apply?

*header:* Apply rows
*multiSelect:* false (5 SCRIPT/HYBRID rows exceed the 4-option inline cap)

| Option | Description |
|---|---|
| Apply all 5 (Recommended) | Write `scan_changelogs.py` (s1, s3), `check_headings.py` (s2), `render_summary.py` (s5), `check_tags.py` (s6), rewrite SKILL.md to invoke them, smoke-test each. |
| Apply a subset — list row ids in Other | Type the row ids to apply, e.g. `s2, s6`. |
| Report only, write nothing | Stop after the report. The target SKILL.md stays untouched. |

## Question 2 — Keep verification residue?

*header:* Keep residue
*Question:* Keep the fixtures and the smoke manifest in `changelog-checker/scripts/tests/` afterward?

| Option | Description |
|---|---|
| No (Recommended) | Delete `.delegation-review/` after a green run. The target keeps only the scripts. |
| Yes | Move fixtures + manifest into `scripts/tests/`, vendor `smoke_test.py` beside them, and rewrite fixture paths so the suite survives relocation. |

## What the prompt already decided

- Question 1 → **Apply all 5.** The prompt says "apply all of them."
- Question 2 → **Yes.** The prompt says "Keep the test fixtures and the manifest inside the skill afterward so I can re-run the checks myself later."

Proceeded to Steps 5-9 on those answers without asking.
