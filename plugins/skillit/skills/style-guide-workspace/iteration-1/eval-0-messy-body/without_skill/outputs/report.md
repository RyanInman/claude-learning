# Style Report: extract-invoices/SKILL.md

File: `/Users/admin/claude-learning/plugins/skillit/skills/style-guide/evals/files/extract-invoices/SKILL.md`

## Verdict

Frontmatter description is solid. Body writing is weak: hedging, passive voice, vague directives, inconsistent terminology, and emphasis inflation. Every body section needs a rewrite; the structure itself (Steps / Example / Notes) is fine.

## What works

- **Description (line 3).** Concrete, states what the skill does and when to trigger, includes user phrasings ("pull data from these invoices", "billing PDFs"). Keep as-is.
- **Example (lines 17-20).** Concrete input/output pair with named columns. Best-written section in the file.

## Issues, prioritized

### 1. Hedging and non-committal language (high)

Skill instructions should be direct commands. Hedges force the model to guess.

- Line 8: "You should probably start by making sure that the input folder, which may or may not have been checked previously..." - 33 words, one buried instruction. "Probably" and "may or may not" add nothing.
  - Rewrite: "Validate the input folder before processing, even if a previous run checked it."
- Line 15: "It is recommended that the output be reviewed before it gets sent."
  - Rewrite: "Review the output before sending it."

### 2. Passive voice hides the actor (high)

Steps read as descriptions of things happening rather than instructions to act.

- Line 12: "The PDFs are scanned and then the text gets extracted and then results are written to `data.json`." Also a run-on ("and then... and then").
  - Rewrite: "Scan the PDFs, extract the text, and write results to `data.json`."
- Line 24: "Various edge cases should be dealt with." Says nothing - which cases, dealt with how?
  - Either list the actual edge cases or delete the sentence.

### 3. Vague directives with no decision criteria (high)

"Appropriately" and "as needed" appear four times (lines 8, 13, 14). Each one is a decision punted to the reader.

- Line 13: "Clean up the settings file as needed." - When is it needed? What does "clean up" mean?
- Line 14: "Handle any errors appropriately and retry as needed." - Which errors are retryable? How many retries?
  - Rewrite pattern: name the condition and the action, e.g. "On PDF parse failure, retry once; if it fails again, log the filename and skip it."

### 4. Inconsistent terminology (medium)

Three names for what appears to be one file: "settings file", "config", "preferences" (line 13). And line 24 explicitly admits the problem for outputs: "The deliverable can also be called the output or the final artifact depending on context."

Pick one term per concept ("config", "output") and use it everywhere. Delete the line-24 terminology disclaimer; it creates ambiguity instead of resolving it.

### 5. Emphasis inflation (medium)

Line 13: "NEVER modify the config without a backup. You MUST ALWAYS validate the preferences before running." Two all-caps mandates in one step, next to a vague "as needed", flattens the signal - nothing reads as more important than anything else. Reserve caps for at most one genuinely critical rule; plain imperatives ("Back up the config before modifying it. Validate it before running.") carry the same instruction.

### 6. Mixed voice (low)

The file drifts between second person ("You should..."), passive ("The PDFs are scanned..."), and impersonal ("It is recommended..."). Standardize on imperative mood throughout, matching the Steps format.

## Suggested rewrite of the body

```markdown
# Invoice Extractor

Validate the input folder before processing, even if a previous run checked it.

## Steps

1. Scan the PDFs, extract the text, and write results to `data.json`.
2. Back up the config before modifying it. Validate the config before running.
3. On extraction errors, retry once; if the retry fails, log the file and continue.
4. Review the output before sending it.

## Example

Input: "pull the invoices from march"
Output: `invoices_march.csv` with columns date, vendor, amount
```

(Notes section deleted: line 24 contained no actionable content. If real edge cases exist, list them concretely under Steps or a dedicated section.)

## Summary

| Issue | Severity | Lines |
|---|---|---|
| Hedging ("probably", "may or may not", "it is recommended") | High | 8, 15 |
| Passive voice | High | 12, 15, 24 |
| Vague directives ("appropriately", "as needed") | High | 8, 13, 14 |
| Inconsistent terminology (config; output) | Medium | 13, 24 |
| Emphasis inflation (NEVER / MUST ALWAYS) | Medium | 13 |
| Mixed voice | Low | body-wide |
