# Style Report: report-render skill

Files reviewed:
- `/Users/admin/claude-learning/plugins/skillit/skills/style-guide/evals/files/report-render/SKILL.md`
- `/Users/admin/claude-learning/plugins/skillit/skills/style-guide/evals/files/report-render/references/formats.md`

Overall: SKILL.md is short and mostly clean. Nearly all style problems live in `references/formats.md`, which is a single paragraph of vague, passive prose that fails to deliver the template SKILL.md promises.

---

## High priority

### 1. formats.md contains no template (broken promise)
SKILL.md step 2 says: "Render the report with the template in `references/formats.md`." The reference contains no template at all -- no section list, no table layout, no chart spec. The SKILL.md example promises "a summary table and one chart per metric", but neither structure is defined anywhere. An agent following this skill must invent the format on every run, defeating the point of the skill.

Fix: replace the paragraph with an actual template -- required sections in order, the summary table columns, and the chart format (e.g. a fenced mermaid block or ASCII sparkline per metric).

### 2. Passive voice hides the actor throughout formats.md
"The template is chosen", "Sections are generated", "they get assembled", "the file is written out". Instructions should be imperative and addressed to the agent so it knows who does what.

Fix: rewrite as commands. "Choose the template based on X. Generate each section. Assemble sections in this order. Write the result to `report.md`."

### 3. Vague, non-deterministic instructions
- "based on what seems appropriate for the data" -- gives no decision rule; two runs on the same data can pick different templates.
- "Handle missing metrics as needed" -- undefined behavior. Skip the metric? Render "N/A"? Fail?

Fix: state concrete rules, e.g. "If a metric is missing, render the row with `--` and add a 'Missing metrics' note under the table."

### 4. Inconsistent terminology for the same artifact
formats.md: "The report file is sometimes called the output document or the deliverable." Three names for one thing invites drift and confusion, and the sentence itself is filler -- it defines nothing.

Fix: pick one term ("the report") and delete the sentence.

## Medium priority

### 5. Run-on sentence
"Sections are generated and then they get assembled and then the file is written out." Chained "and then... and then" reads poorly and buries the sequence.

Fix: numbered steps or short imperative sentences.

### 6. Emphasis inconsistency
"You MUST NEVER skip the summary section" is the only hard constraint, shouted in caps, sitting between soft hedges ("seems appropriate", "as needed"). Emphasis loses force when the surrounding text is vague, and doubled negation ("MUST NEVER skip") is weaker than a positive requirement.

Fix: state it positively: "Always include the summary section first." Reserve caps/bold for the one or two rules that genuinely need them.

### 7. formats.md has no structure
One heading, one paragraph. Even after a rewrite it should use headings (Template selection, Sections, Summary table, Charts, Missing data) so the agent can scan to the relevant rule.

## Low priority

### 8. SKILL.md description could name the output
Description is fine for triggering ("weekly report", "render the metrics", metrics JSON export). Optionally note the fixed output ("writes report.md") so the model knows the deliverable without opening the body. Minor.

### 9. SKILL.md step 1 lacks an input contract
"Read the metrics JSON" -- from where? If the user names a file, fine, but a default path or "ask if no file is given" would remove ambiguity.

---

## Suggested rewrite of formats.md

```markdown
# Report Formats

Always include sections in this order. The summary section is required.

## Sections

1. **Summary** (required) -- table of all metrics.
2. **Charts** -- one chart per metric, in the same order as the table.

## Summary table

| Metric | This week | Last week | Change |
|--------|-----------|-----------|--------|

## Charts

Render one fenced mermaid chart per metric (line chart of the weekly
values). Title each chart with the metric name.

## Missing metrics

If a metric has no data, render its table row with `--` in every value
column and list it under a "Missing metrics" note after the table. Do
not omit the row and do not fail the render.
```

## Summary

| # | File | Issue | Severity |
|---|------|-------|----------|
| 1 | formats.md | Promised template does not exist | High |
| 2 | formats.md | Passive voice, no actor | High |
| 3 | formats.md | Vague/non-deterministic rules | High |
| 4 | formats.md | Three names for one artifact | High |
| 5 | formats.md | Run-on "and then" sentence | Medium |
| 6 | formats.md | Shouted, negated constraint | Medium |
| 7 | formats.md | No headings/structure | Medium |
| 8 | SKILL.md | Description could name output | Low |
| 9 | SKILL.md | Input path unspecified | Low |
