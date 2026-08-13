# Step 4 gate (would have been an AskUserQuestion call with both questions in one call)

**Question 1 — Which rows should I apply?**
(header: "Apply rows"; 6 SCRIPT/HYBRID rows, so the three-option form)

1. `Apply all 6 (Recommended)` — write scan_changelogs.py, check_changelogs.py, and render_summary.py into the target and rewrite steps s1, s2, s3, s5, s6, s7.
2. `Apply a subset — list row ids in Other` — e.g. "s2, s6".
3. `Report only, write nothing` — leave changelog-checker untouched.

**Question 2 — Keep verification residue?**
(header: "Residue"; keep fixtures and the smoke manifest in the target's `scripts/tests/` afterward?)

1. `No (Recommended)` — delete `.delegation-review/` after a green run.
2. `Yes` — install fixtures, manifest, and a vendored smoke_test.py under `scripts/tests/` so you can re-run the checks later.

**Answers taken from prompt.txt:** Q1 = "Apply all 6" ("apply all of them"). Q2 = "Yes" ("Keep the test fixtures and the manifest inside the skill afterward so I can re-run the checks myself later").
