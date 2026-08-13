# Step 4 gate (would have been one AskUserQuestion call with both questions)

## Question 1 -- which rows to apply
header: "Apply rows"
question: "2 mechanical rows found. Which delegations should I write into link-checker?"
multiSelect: true
options:
1. "s1 collect_links.py (Recommended)" -- Walk docs/ and emit every relative link with its source file and line to .link-check/links.json.
2. "s2 resolve_links.py (Recommended)" -- Test each collected target against disk; print broken/total, exit 1 when broken links exist.

(4 or fewer SCRIPT/HYBRID rows, so one option per row, every option marked Recommended. s3 and s4 are CLAUDE and are not offered.)

## Question 2 -- keep verification residue
header: "Residue"
question: "Keep the smoke-test fixtures and manifest in the target's scripts/tests/ afterward?"
multiSelect: false
options:
1. "No (Recommended)" -- Delete the fixtures and manifest once the smoke test passes.
2. "Yes" -- Leave scripts/tests/ in the target so the scripts can be re-verified later.

## Resolution under the non-interactive rule

prompt.txt says "Don't change anything yet." -> report-only. Stopped after the report.
Nothing written into the target skill: no scripts/, no SKILL.md rewrite, no fixtures.
