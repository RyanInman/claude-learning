# Step 4 gate

The gate was reached but not opened with AskUserQuestion. The user request
already answers it.

## Question 1 - which rows to apply

Would have been asked as: 3 SCRIPT/HYBRID rows (s1, s3, s5), so 4 or fewer ->
`multiSelect: true`, one option per row, each marked "(Recommended)":

- s1 - list/count endpoint files -> `check_endpoints.py` (Recommended)
- s3 - frontmatter required-field check -> `check_endpoints.py` (Recommended)
- s5 - extract descriptions + mechanical clarity signals ->
  `collect_descriptions.py` (Recommended)

**Proceeded with: apply none - report only.** The user wrote "Just tell me -
don't write anything yet." That is an explicit instruction to stop after the
Step 3 report, and SKILL.md Step 4 says "No pick -> stop after the report. Never
write into the target without an explicit pick."

## Question 2 - keep verification residue

Would have been asked as: keep fixtures and manifest in the target's
`scripts/tests/` afterward? Options "No (Recommended)" / "Yes".

**Not applicable.** No scripts are being written, so there is no residue to
keep. The question only matters once Step 5 onward runs.

## Note on the DEAD rows

s2 and s4 were never gate candidates. Only SCRIPT and HYBRID rows go through the
gate; DEAD steps are reported and routed to a `skillit:review` follow-up, never
auto-deleted, because the user owns the target's workflow.

## What a follow-up run needs

An explicit "apply s1, s3, s5" (or a subset) plus a residue answer. State
`.delegation-review/` in the working directory holds the inventory,
classification, and the `SKILL.md.orig` restore point, so a later run resumes at
Step 5 without redoing Steps 0-3.
