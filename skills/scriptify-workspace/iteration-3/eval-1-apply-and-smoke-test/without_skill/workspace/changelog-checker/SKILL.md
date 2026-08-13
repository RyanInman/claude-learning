---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Collect the structure facts. Run the scanner from the skill folder:

   ```bash
   python3 scripts/scan_changelogs.py changelogs
   ```

   It prints JSON holding the file list sorted by version, the file count,
   per-file and total per-category entry counts, `bad_headings` (files whose
   first non-empty line is not `## vX.Y.Z — YYYY-MM-DD`), `unknown_tags`
   (category headings outside `Added`, `Fixed`, `Changed`, `Removed`, `Misc`),
   and `misc_entries` (the text of every `Misc` entry). Read the counts from
   this JSON rather than recounting, because a second count by hand can
   disagree with the table.

2. Render the summary table, sorted by version descending:

   ```bash
   python3 scripts/scan_changelogs.py changelogs --format table
   ```

   Paste its output into the report unchanged.

3. Write a one-paragraph release narrative for a non-technical reader, using
   the entry text from the JSON. Say where the product moved overall, not what
   each commit did.

4. Recategorize the `Misc` entries. For each item in `misc_entries`, judge
   whether it belongs under `Added`, `Fixed`, `Changed`, or `Removed`, and
   recommend the move with a one-line reason. Leave it under `Misc` when no
   category fits.

5. Flag unclear entries. Read the entry text in the JSON and call out any entry
   a reader outside the team could not act on — missing subject, unexplained
   jargon, or an effect that is not stated.

## Report

Return, in this order: the table from step 2, the narrative from step 3, the
structural problems (`bad_headings` and `unknown_tags`), the `Misc`
recommendations from step 4, and the clarity flags from step 5.

## Gotchas

- The heading check demands an em dash (`—`), matching the documented format. A
  hyphen heading is reported in `bad_headings`, so read the `heading_problem`
  field before telling the user the heading is missing entirely.
- Entries under an unknown tag are excluded from the category counts, because
  the counts cover only the allowed categories. A file's row total can be lower
  than its visible bullet count when `unknown_tags` is non-empty for that file.
- The scanner exits 2 when the folder argument is not a directory. Check the
  path before reporting an empty changelog set.
