# Step 4 gate (not presented — prompt said "don't change anything yet")

Both questions below would have gone to the user in one AskUserQuestion call. The prompt already
decided the outcome: report only, write nothing into the target.

## Question 1 — Which rows to apply?

Header: `Apply`

6 SCRIPT and HYBRID rows (s1, s2, s3, s5, s6, s7), so more than 4: three options, no multiSelect.

| Option | Description |
|---|---|
| Apply all 6 (Recommended) | Write `scan_changelogs.py` and `render_summary.py` into `changelog-checker/scripts/`, rewrite steps 1, 2, 3, 5, 6, 7 to invoke them, and smoke-test both. |
| Apply a subset — list row ids in Other | Type the ids to apply, e.g. `s1 s2 s3 s5`. |
| Report only, write nothing | Keep the report; leave `changelog-checker/` untouched. |

## Question 2 — Keep verification residue?

Header: `Residue`

Keep the smoke-test fixtures and manifest in the target's `scripts/tests/` afterward?

| Option | Description |
|---|---|
| No (Recommended) | Delete the fixtures and manifest once the smoke test passes. |
| Yes | Install them under `scripts/tests/` so the checks re-run later. |

## Outcome taken

The prompt says "Don't change anything yet", which selects "Report only, write nothing".
The run stopped after Step 3. Nothing was written into
`workspace/changelog-checker/`; Question 2 never applies.
