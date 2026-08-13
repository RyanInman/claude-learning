# Step 4 gate — the choice point (asked via AskUserQuestion, both questions in one call)

## Question 1 — Which rows to apply?

header: "Apply which?"
question: "5 of 7 steps are mechanical. Which delegations should I write into changelog-checker?"
multiSelect: true

| Option | Description |
|---|---|
| s1+s2+s3 → scan_changelogs.py (Recommended) | List and count files, validate the `## vX.Y.Z — YYYY-MM-DD` header, tally entries per category — one pass, one script. |
| s5 → render_summary.py (Recommended) | Render the version/date/counts table from the scan JSON, versions descending. |
| s6 → scan_changelogs.py, HYBRID (Recommended) | Script flags tags outside the allowed list and lists every `Misc` entry; you still judge which category each `Misc` entry belongs in. |
| Report only, write nothing | Leave changelog-checker untouched. |

(s4 release narrative and s7 clarity check stay CLAUDE and are not offered.)

## Question 2 — Keep the verification residue?

header: "Keep residue?"
question: "Keep the smoke-test fixtures and manifest in changelog-checker/scripts/tests/ afterward?"
multiSelect: false

| Option | Description |
|---|---|
| No (Recommended) | Smoke-test now, then delete `.delegation-review/`. Target gets scripts only. |
| Yes | Install fixtures, manifest, and a vendored smoke_test.py under `scripts/tests/` so the checks are rerunnable. |

## What the prompt already decided

prompt.txt says "apply all the delegations you find, and verify the generated scripts work".

- Question 1 → every SCRIPT and HYBRID row selected (s1, s2, s3, s5, s6).
- Question 2 → no residue instruction given, so the recommended default: No. "Verify the generated scripts work" is satisfied by the Step 7 smoke test, which runs whether or not the residue is kept.
