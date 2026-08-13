---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --json`
   `files` holds every `.md` file sorted by version and `file_count` is the total. Exit 1 means the folder holds no changelog files — report that and stop. Exit 2 is a usage or read error.
2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
3. Take the per-category counts from the same scan JSON: `versions[].counts` per file, `totals` across files. Entries under any other category heading are tallied under `other_categories`, so they are counted rather than dropped.
4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
7. Verify the entries are clearly written and flag any that a reader would find confusing.
