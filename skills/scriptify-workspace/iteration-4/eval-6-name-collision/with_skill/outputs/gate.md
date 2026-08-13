# Gate — what I would have asked

Two AskUserQuestion questions in one call at Step 4, plus one collision question that Step 6 requires.

## Question 1 — which rows to apply

header: "Apply rows"
question: "3 SCRIPT rows are ready to apply to docs-linter. Which should I write?"
multiSelect: true
options (4 or fewer rows, so one option per row, every one recommended):

1. "s1 — file inventory (Recommended)" — List every `.md` under `docs/`, sorted, with a total count. Becomes part of `scripts/lint_docs.py`.
2. "s2 — level-1 heading rule (Recommended)" — Flag every file whose first line is not an H1 followed by a blank line. Becomes part of `scripts/lint_docs.py`.
3. "s3 — fenced-block counts (Recommended)" — Count fenced code blocks per file and in total. Becomes part of `scripts/lint_docs.py`.
4. "None — report only, write nothing" — Stop after the report.

(s4 is CLAUDE and is not on offer: prioritizing the flagged files for the sprint is judgment no script replaces.)

## Question 2 — keep verification residue

header: "Residue"
question: "Keep the smoke-test fixtures and manifest in docs-linter/scripts/tests/ afterward?"
multiSelect: false
options:

1. "No (Recommended)" — Verify, then delete `.delegation-review/`. The target keeps only `scripts/lint_docs.py`.
2. "Yes" — Install fixtures, manifest, and a vendored `smoke_test.py` under `scripts/tests/`, and prove the suite survives relocation.

## Question 3 — name collision (Step 6 requires asking before writing)

header: "Script name"
question: "`scripts/check_headings.py` already exists in the target. It checks image alt text, not headings, and its docstring says the release pipeline calls it by that exact path. Where should the heading-rule code go?"
multiSelect: false
options:

1. "New file `scripts/lint_docs.py` (Recommended)" — Leave `check_headings.py` byte-identical. The new script carries the inventory, the heading rule, and the fence counts in one pass.
2. "Add the heading rule inside `check_headings.py`" — Keeps the name honest but changes a file the release pipeline depends on.
3. "Overwrite `check_headings.py`" — Breaks the release pipeline's alt-text check. Not recommended.

## What was decided without asking

The prompt says "find the steps worth delegating and apply all of them", so every SCRIPT row (s1, s2, s3) counts as selected.
Question 2 took its recommended default: No residue.
Question 3 took option 1, `scripts/lint_docs.py`, because options 2 and 3 both modify a file another pipeline calls by path, and the skill forbids overwriting silently.
