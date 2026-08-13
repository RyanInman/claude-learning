---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/`
   It lists every `.md` file sorted by version with the total count, checks each
   file's `## vX.Y.Z — YYYY-MM-DD` heading, counts entries per category, and
   prints the summary table of versions, dates, and per-category counts sorted
   by version descending. Add `--json` for the same data structured, and
   `--out FILE` when the table runs long.
   Exit 0 clean, 1 findings, 2 usage error or missing folder.
   Exit 1 → report every finding under its code: `no_changelog_files`,
   `first_line_not_version_heading`, `version_heading_missing`,
   `malformed_version_heading`.
2. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
3. Run exactly: `python3 scripts/check_categories.py changelogs/ --json`
   Entries tagged outside the allowed list (`Added`, `Fixed`, `Changed`,
   `Removed`, `Misc`) come back under `invalid` with code `unknown_category`.
   For each entry under `misc`, judge whether it actually fits one of the other
   categories and suggest the move.
   Exit 0 clean, 1 findings, 2 usage error or missing folder.
4. Verify the entries are clearly written and flag any that a reader would find confusing.
