# Step 4 gate — presented, then closed by the prompt

The prompt said "Don't change anything yet", so the gate below was written but
not acted on. Nothing was written into the target skill.

Both questions would have gone out in one AskUserQuestion call.

## Question 1 — which rows to apply

header: Apply rows
question: Which delegation rows should I write into link-checker?
multiSelect: true
(2 SCRIPT/HYBRID rows, so one option per row)

- "s1 - collect the link inventory (Recommended)" — description: "check_links.py walks docs/ and records every relative link with file and line."
- "s2 - resolve each target (Recommended)" — description: "Same check_links.py pass marks broken targets and reports broken vs total."

## Question 2 — keep verification residue

header: Residue
question: Keep the smoke-test fixtures and manifest in the target's scripts/tests/ afterward?
multiSelect: false

- "No (Recommended)" — description: "Delete fixtures and manifest after the smoke test passes. Leaves only check_links.py."
- "Yes" — description: "Keep scripts/tests/ so you can re-run the smoke test later."

## Answer obeyed

prompt.txt decided: report only, write nothing. Stopped after Step 3's report.
