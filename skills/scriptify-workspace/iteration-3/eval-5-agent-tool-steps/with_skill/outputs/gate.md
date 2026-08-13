Step 4 gate reached. Prompt said "Report only for now, don't change anything",
so no AskUserQuestion call was made and nothing was written into the target.
Both questions below would have gone out in a single AskUserQuestion call.

## Question 1 - which rows to apply

header: "Apply"
question: "6 SCRIPT/HYBRID rows are ready to apply to research-brief-writer.
Which do you want written into the skill?"
multiSelect: false
options (more than 4 rows, so the three-option form applies):

1. "Apply all 6 (Recommended)" - Write normalize_topics.py, plan_fetch.py,
   source_stats.py, and render_index.py into research-brief-writer/scripts/,
   rewrite steps 1-5 and 7 to invoke them, and smoke-test each script.
2. "Apply a subset - list row ids in Other" - Name the rows to apply, for
   example "s1 s4 s7". Unnamed rows stay as prose.
3. "Report only, write nothing" - Stop here. The report above is the whole
   deliverable.

## Question 2 - keep verification residue

header: "Residue"
question: "Keep the smoke-test fixtures and manifest in
research-brief-writer/scripts/tests/ after the run?"
multiSelect: false
options:

1. "No (Recommended)" - Smoke-test, then delete the fixtures and manifest.
2. "Yes" - Leave scripts/tests/ in the target so you can re-run the smoke
   tests later.

## Answer taken from the prompt

Question 1 -> option 3, "Report only, write nothing". The prompt says
"Report only for now, don't change anything".
Question 2 -> not applicable; no scripts are written, so there is no residue.
