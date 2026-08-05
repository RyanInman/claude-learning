# Style Report: csv-dedupe

Skill: `/Users/admin/claude-learning/plugins/skillit/skills/style-guide/evals/files/csv-dedupe/SKILL.md`
House style: `/Users/admin/claude-learning/plugins/skillit/references/writing-style-guide.md`

## Grade: A — Full adherence

Part A checklist passes across the entire body. No rule is violated; at most borderline observations below.

## Part A walkthrough (body)

| Rule | Verdict | Evidence |
|---|---|---|
| 1 — Command verb openers | Pass | Every instruction opens imperative: "Read the CSV with pandas." "Drop duplicate rows…" "Write the result…" "Report the row counts…" "Compare rows after whitespace normalization…" |
| 2 — Visible actor | Pass | No passive voice anywhere in procedures. Imperative implies Claude throughout. |
| 3 — One instruction per sentence | Pass | Steps 1–4 are each a single instruction. No "and then" compounds. |
| 4 — 20-word tripwire | Pass | Longest procedural sentence is well under 20 words. |
| 5 — One term per concept | Pass | "CSV", "rows", "duplicate(s)" used consistently. "Spreadsheet" appears only in the description (Rule 11 exempt zone, where matching user language is correct). "Output" appears only inside the example (Rule 12 exempt zone). |
| 6 — Specific action and amount | Pass | Concrete throughout: `df.drop_duplicates(keep="first")`, output filename `<input>-deduped.csv`, "row counts before and after". Zero instances of handle/process/appropriately/as needed/various/etc. |
| 7 — Standard terms of art | Pass | Uses "dedupe", "whitespace normalization", pandas API names directly; nothing paraphrased. |
| 8 — Flat grammar | Pass | Present tense facts, imperative steps, no stacked subordinate clauses. |
| 9 — Reason on non-obvious rules | Pass | Both non-obvious rules carry a "because": keep-first ("because downstream reports assume the earliest entry is canonical") and whitespace normalization ("because exported CSVs often pad cells with trailing spaces"). No ALL-CAPS directives. Obvious steps correctly carry no reason. |
| 10 — No filler | Pass | No hedges, throat-clearing, or restatement. Every sentence does work. |

## Part B walkthrough

| Rule | Verdict | Evidence |
|---|---|---|
| 11 — Description in user language | Pass | Third person ("Removes duplicate rows…"), verbatim trigger phrases ("dedupe this CSV", "remove duplicate rows"), implicit case covered ("shares a spreadsheet with repeated entries"). No "when to use" content leaked into the body. |
| 12 — Verbatim example | Pass | Concrete input→output example present: `dedupe leads.csv` → `leads-deduped.csv` with the literal reply "Removed 42 duplicates; 958 rows remain." Output shown, not described. |

## Non-graded observations

These do not affect the adherence grade (grading covers Part A prose; hygiene items are separate checklist entries), but they are worth fixing:

1. **No negative triggers in the description** (Rule 11 checklist item). Add a "Do NOT use for X" clause for near-miss cases, e.g. deduplicating on a subset of columns, fuzzy near-duplicate matching, or non-CSV formats — those are the likeliest mis-fires for this skill.
2. **No `evals/evals.json`** (general hygiene checklist: "≥2 realistic eval prompts in evals/evals.json, tested against the no-skill baseline"). The skill folder contains only SKILL.md.
3. Borderline: the whitespace gotcha says to compare after normalization but not whether the written rows keep original or normalized whitespace. One clarifying clause would remove the ambiguity. Borderline, not a violation, because the instruction itself is specific.

## Summary

The body reads exactly to house style: imperative, active, one instruction per sentence, specific amounts, reasons attached where non-obvious, exempt zones (description, example) correctly written in user language rather than Part A prose. Grade A. To ship-quality per the full checklist, add negative triggers to the description and an `evals/evals.json` with at least two prompts.
