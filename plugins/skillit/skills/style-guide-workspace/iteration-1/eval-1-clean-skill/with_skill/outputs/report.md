## Style grade: csv-dedupe

**Grade:** A — full Part A adherence; at most one isolated borderline sentence.

The body and Gotchas pass every Part A rule:

- **Rule 1 (command verbs):** every instruction opens with one — "Read the CSV with pandas.", "Drop duplicate rows…", "Write the result…", "Report the row counts…", "Compare rows after whitespace normalization…".
- **Rule 2 (actor visible):** no passive voice; the imperative implies Claude throughout.
- **Rules 3–4 (one instruction per sentence, length):** each step is a single short sentence; nothing approaches the 20-word tripwire.
- **Rule 5 (one term per concept):** the only wobble is "Remove duplicate rows" (intro) vs. "Drop duplicate rows" (step 2), and step 2's verb mirrors the `df.drop_duplicates` API name, which justifies it. Borderline, not a violation.
- **Rule 6 (specific action and amount):** `keep="first"`, `<input>-deduped.csv`, and "row counts before and after" are all exact; zero instances of "handle / process / appropriately / as needed / various / etc."
- **Rules 7–8 (terms of art, flat grammar):** standard terms (pandas, CSV, whitespace normalization); present tense and imperative only; no stacked clauses.
- **Rule 9 (reason on non-obvious rules):** both non-obvious rules carry a "because" — keep-first ("downstream reports assume the earliest entry is canonical") and whitespace normalization ("exported CSVs often pad cells with trailing spaces"). Zero ALL-CAPS directives.
- **Rule 10 (no filler):** every word does work.

Exempt zones, not graded per Rules 11–12:

- The frontmatter description (third person, verbatim trigger phrasings like "dedupe this CSV") — deliberately colloquial and correct for its zone.
- The Example section's input→output pair ("dedupe leads.csv" → `leads-deduped.csv`, "Removed 42 duplicates; 958 rows remain.") — verbatim, as Rule 12 requires.

No `references/` folder exists, so there is nothing further to grade.

No checklist section: at grade A there are no edits to reach an A.
