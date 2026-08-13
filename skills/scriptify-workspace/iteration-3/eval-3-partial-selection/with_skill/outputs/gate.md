# Step 4 gate — the questions I would have asked

Both questions would have gone out in a single AskUserQuestion call.

## Question 1 — Which rows to apply?

6 SCRIPT/HYBRID rows, which is more than 4, so the three-option form applies.

**header:** Apply
**question:** 6 steps are mechanical (s1, s2, s3, s5, s6, s7). Which delegations should I write into changelog-checker?
**multiSelect:** false

| Option | Description |
|---|---|
| Apply all 6 (Recommended) | Write scan_changelogs.py, check_headings.py, render_summary.py, and check_categories.py into changelog-checker/scripts/, then rewrite steps 1, 2, 3, 5, 6, 7 to invoke them. |
| Apply a subset — list row ids in Other | Type the row ids to apply, for example "s1 s3". Unlisted rows stay as prose. |
| Report only, write nothing | Stop after the report. changelog-checker is left untouched. |

## Question 2 — Keep the verification residue?

**header:** Residue
**question:** Keep the smoke-test fixtures and manifest in changelog-checker/scripts/tests/ afterward?
**multiSelect:** false

| Option | Description |
|---|---|
| No (Recommended) | Delete .delegation-review/ after a green run. The target ships only the scripts. |
| Yes | Install fixtures, manifest, and a vendored smoke_test.py under scripts/tests/, and prove they still pass from a relocated copy. |

## What the prompt already decided

The user's prompt says: "apply only the delegations for steps 1 and 3. Leave everything
else untouched."

- Question 1 → "Apply a subset", row ids **s1 and s3**. Rows s2, s5, s6, s7 stay as prose.
- Question 2 → no instruction given, so the recommended default stands: **No**, remove the
  review directory after a green run.

Rows s1 and s3 share one proposed script, `scan_changelogs.py`, so applying both writes one
script. Row s5's proposed `render_summary.py` consumes that script's JSON, but s5 was not
picked, so step 5 keeps its original prose and no render script is written.
