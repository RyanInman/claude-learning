---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/list_changelogs.py changelogs/ --json`
   Exit 0 files found, 1 the folder holds no `.md` file (`findings: ["no_markdown_files"]`), 2 usage error. `files` is version-sorted and `count` is the total; names carrying no version land in `unversioned`.
2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
3. Run exactly: `python3 scripts/count_entries.py changelogs/ --json`
   Exit 0 entries counted, 1 no entry in any file (`findings: ["no_entries_found"]`), 2 usage error. `per_file` holds the per-category counts and `totals` the cross-file totals; every tag found is reported, including ones outside the expected list, so step 6 can triage them.
4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
7. Verify the entries are clearly written and flag any that a reader would find confusing.
