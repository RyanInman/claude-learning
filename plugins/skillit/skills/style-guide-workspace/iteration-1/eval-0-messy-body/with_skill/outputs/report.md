## Style grade: extract-invoices

**Grade:** F — Rule 2 (keep the actor visible), Rule 6 (name the specific action and amount), Rule 5 (one term per concept)

The guide was not applied: passive voice is pervasive, vague delegation words appear in most instructions, and the skill explicitly sanctions synonym drift. Scope note: only SKILL.md exists (no `references/`). The frontmatter description and the Example section are exempt zones (Rules 11-12) and were not graded; both are fine as-is.

- **Rule 2 (keep the actor visible)** — "The PDFs are scanned and then the text gets extracted and then results are written to `data.json`." Seven passive constructions run through the body ("are scanned", "gets extracted", "are written", "gets validated", "be reviewed", "gets sent", "should be dealt with"); no sentence names who acts.
- **Rule 6 (name the specific action and amount)** — "Handle any errors appropriately and retry as needed." "Appropriately" appears twice, "as needed" three times, plus "handle", "various", and "clean up ... as needed" — every one delegates a decision without the information to make it.
- **Rule 5 (one term per concept)** — "The deliverable can also be called the output or the final artifact depending on context." The skill codifies drift instead of banning it, and step 2 alone uses "settings file", "config", and "preferences" for one file.

Also costly: Rule 9 (three ALL-CAPS directives, none with a reason), Rule 1 ("You should probably start...", "It is recommended that..."), Rule 3 (double "and then" in step 1), Rules 4/8 (the 35-word opener with nested clauses).

### Checklist to reach an A

1. **Rule 1 (command verb) + Rule 2 (actor) + Rule 4 (20-word tripwire) + Rule 6 (specific action) + Rule 8 (flat grammar) + Rule 10 (cut filler)** — "You should probably start by making sure that the input folder, which may or may not have been checked previously by the user or by an earlier run of this workflow, gets validated appropriately." → "Validate the input folder before extraction, even when an earlier run already checked it." State what validation means (e.g. "confirm every file is a readable PDF"), because "appropriately" gives Claude nothing to act on.

2. **Rule 2 (actor) + Rule 3 (one instruction per sentence)** — "The PDFs are scanned and then the text gets extracted and then results are written to `data.json`." → "Scan the PDFs. Extract the text. Write the results to `data.json`."

3. **Rule 6 (specific action) + Rule 5 (one term)** — "Clean up the settings file as needed." → name the actual cleanup and use the chosen term, e.g. "Remove stale keys from the config." (Author supplies the real cleanup steps; "as needed" is banned in instructions.)

4. **Rule 9 (reason, no ALL-CAPS)** — "NEVER modify the config without a backup." → "Back up the config before modifying it, because a bad edit is unrecoverable without one." (Author substitutes the true reason.)

5. **Rule 1 (command verb) + Rule 5 (one term) + Rule 9 (reason, no ALL-CAPS)** — "You MUST ALWAYS validate the preferences before running." → "Validate the config before running, because an invalid config aborts extraction midway." (Author substitutes the true reason; "preferences" → "config".)

6. **Rule 6 (specific action and amount)** — "Handle any errors appropriately and retry as needed." → "On an extraction error, retry twice, then log the file name and skip that PDF." (Author sets the real retry count and fallback.)

7. **Rule 1 (command verb) + Rule 2 (actor) + Rule 5 (one term)** — "It is recommended that the output be reviewed before it gets sent." → "Review the deliverable before sending it."

8. **Rule 2 (actor) + Rule 6 (specific action)** — "Various edge cases should be dealt with." → enumerate the actual cases as `If X → do Y` lines, e.g. "If a PDF is image-only, run OCR first. If the amount column is missing, log the vendor and skip the row." — or delete the sentence, because a vague catch-all carries no information.

9. **Rule 5 (one term per concept)** — "The deliverable can also be called the output or the final artifact depending on context." → delete this sentence. Pick "deliverable" as the single term and use it in every sentence (item 7 already applies it), because variety reads as distinction: three names imply three files.

10. **Rule 5 (terminology sweep)** — after items 3, 5, 7, and 9, sweep the body once: "config" is the only term for the settings file; "deliverable" is the only term for the final CSV; "extract" is the only verb for getting data out. (The Example section's "Output:" line is exempt — leave it verbatim.)

Applying all ten items yields an A on re-review.
