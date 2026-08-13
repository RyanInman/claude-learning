# Step 4 gate (not presented — prompt said "just tell me, don't write anything yet")

I would have sent both questions below in one AskUserQuestion call. The prompt
already decided the answer: report only, nothing written into the target.

## Question 1 — which rows to apply?

header: Apply
question: The review found 2 SCRIPT rows and 1 HYBRID row, all backed by one
script (`check_endpoints.py`). Which should I write into api-docs-checker?
multiSelect: true

- **s1 — file list + count (Recommended)**: SCRIPT. `check_endpoints.py` globs
  `endpoints/*.md`, sorts, and reports the count.
- **s3 — frontmatter check (Recommended)**: SCRIPT. Same script reports which of
  `summary:` / `description:` is missing from which file.
- **s5 — description clarity (Recommended)**: HYBRID. Same script extracts every
  description string; I judge clarity from its output.

(3 SCRIPT/HYBRID rows, so multiSelect with one option per row, per Step 4. The
DEAD rows s2 and s4 are not offered — this skill never auto-edits another
skill's steps; they are routed to a `skillit:review` follow-up in the report.)

## Question 2 — keep verification residue?

header: Residue
question: Keep the smoke-test fixtures and manifest in
api-docs-checker/scripts/tests/ after verification?

- **No (Recommended)**: Delete the fixtures and manifest once the smoke test
  passes.
- **Yes**: Keep them in the target so you can re-run the smoke test later.

## What the prompt decided

"Just tell me — don't write anything yet" → stop after the report. No scripts
written, no SKILL.md rewritten, nothing created under
workspace/api-docs-checker/.
