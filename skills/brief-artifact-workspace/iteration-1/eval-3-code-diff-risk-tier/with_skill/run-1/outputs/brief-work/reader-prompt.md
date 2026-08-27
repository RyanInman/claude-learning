You are reading one chunk of a larger artifact (a git diff). Read only the chunk text file named below.
Do not look at other files (except inventory.json for your anchor), run code, or search the web.

Type: diff
Anchor: the "anchor" field for your chunk id in /Users/admin/claude-learning/skills/brief-artifact-workspace/iteration-1/eval-3-code-diff-risk-tier/with_skill/outputs/brief-work/inventory.json (read it with grep/python).

Write a JSON object to /Users/admin/claude-learning/skills/brief-artifact-workspace/iteration-1/eval-3-code-diff-risk-tier/with_skill/outputs/brief-work/{CHUNK_ID}.json with exactly these fields:
- summary: 120 words max. Say what this chunk does or argues, top-down, in plain language.
- claims: list of atomic claims (prose) or behaviors (code). Each has text, anchor
  (file:line range or heading from the chunk), and status:
    verified      the chunk shows the evidence (code visible, source cited, data shown)
    unverified    stated with no evidence in the chunk; use this when unsure
    contradicted  two places in the chunk disagree; anchor must read "A vs B"
- risks: list of {kind, anchor, note}. kind is one of
    hallucinated-api, duplicate-logic, missing-edge-case (code)
    uncited-number, unsupported-claim (prose)
  Flag only what you see. Do not invent risks to fill the list.
- least_confident: one sentence naming the part you understood least or could not check.

Rules:
- Every claim and risk needs an anchor copied from the chunk, because the reader
  will drill in from that pointer.
- Do not summarize anything outside the chunk text.
- Output the JSON file only. Reply with one line: the path written.
