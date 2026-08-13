# Gate that would have been presented (Step 4)

Not presented. `prompt.txt` says "Don't change anything yet", which pre-answers the gate
as report-only, so the skill stops after Step 3 and writes nothing into the target.
Recorded here verbatim for the record.

The call would have been a single AskUserQuestion with both questions:

## Question 1 — which rows to apply

header: "Apply"
question: "5 steps are delegable (4 SCRIPT, 1 HYBRID). Which should I write scripts for?"
multiSelect: true

- "s1 - list and count changelog files (Recommended)"
- "s2 - check the version heading of each file (Recommended)"
- "s3 - count entries per category (Recommended)"
- "s5 - render the summary table (Recommended)"
- "s6 - audit category tags, Claude re-triages Misc (Recommended)"

(5 rows exceeds the 4-option cap, so the real call collapses to the three-option form:)

- "Apply all 5 (Recommended)"
- "Apply a subset - list row ids in Other"
- "Report only, write nothing"

## Question 2 — keep verification residue

header: "Residue"
question: "Keep the smoke-test fixtures and manifest in changelog-checker/scripts/tests/ afterward?"
multiSelect: false

- "No (Recommended)"
- "Yes"

## Answer taken from prompt.txt

"Report only, write nothing." Question 2 is moot with no rows applied.
