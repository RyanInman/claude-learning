# Step 4 gate (unattended run)

The skill's Step 4 opens an AskUserQuestion gate with two questions. No live
user, so both are recorded here.

## Question 1 — which delegations to apply

3 SCRIPT/HYBRID rows, so the 4-or-fewer branch applies (`multiSelect: true`,
one option per row, each marked Recommended):

- s1 — `check_endpoints.py` (list + count endpoint files) — (Recommended)
- s3 — `check_endpoints.py` (required frontmatter fields) — (Recommended)
- s5 — `list_descriptions.py` (extract descriptions, Claude judges clarity) — (Recommended)
- Report only, write nothing

**Chosen: "Report only, write nothing."** Not the recommended default — the
user's request already answers this question: "Just tell me — don't write
anything yet." The skill's Step 4 is explicit that no pick means stop after the
report and never write into the target.

## Question 2 — keep verification residue in `scripts/tests/`?

- No (Recommended)
- Yes

**Moot.** Question 2 only matters once scripts get written. Nothing was
written, so no fixtures or manifest exist.

## Consequence

Ran Steps 0-3 only. Steps 5-9 (contract, implement, smoke test, SKILL.md
rewrite, wrap-up) were not run. The target skill folder is untouched.
`scratch/.delegation-review/` holds `SKILL.md.orig`, `inventory.json`, and
`classification.json` so a later run can resume from Step 5.
