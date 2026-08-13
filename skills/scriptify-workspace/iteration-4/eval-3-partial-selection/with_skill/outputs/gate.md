# Step 4 gate — what I would have asked with AskUserQuestion

Both questions would have been sent in one AskUserQuestion call.

## Question 1 — Which delegations should I apply?

header: "Apply"
question: "5 steps are delegable (s1, s2, s3, s5 SCRIPT; s6 HYBRID). Which should I write into changelog-checker?"
multiSelect: false

| Option | Description |
|---|---|
| Apply all 5 (Recommended) | Write list_changelogs.py, check_headings.py, count_entries.py, render_summary.py, check_categories.py and rewrite steps 1, 2, 3, 5, 6. |
| Apply a subset — list row ids in Other | Type the row ids to apply, e.g. "s1 s3". Unlisted rows stay untouched. |
| Report only, write nothing | Stop after the report. The target skill is not modified. |

## Question 2 — Keep the verification residue?

header: "Residue"
question: "Keep the smoke-test fixtures and manifest in changelog-checker/scripts/tests/ afterward?"
multiSelect: false

| Option | Description |
|---|---|
| No (Recommended) | Delete .delegation-review/ after a green run. Nothing extra ships in the target. |
| Yes | Install fixtures, manifest, and a vendored smoke_test.py under scripts/tests/ so the checks are rerunnable. |

## What the prompt already decided

- Question 1: "apply only the delegations for steps 1 and 3. Leave everything else untouched." → subset = s1, s3. Rows s2, s5, s6 are reported only; steps 4 and 7 stay CLAUDE.
- Question 2: not addressed by the prompt → default answer "No (Recommended)". No residue is installed; `.delegation-review/` is removed after the green smoke run.
