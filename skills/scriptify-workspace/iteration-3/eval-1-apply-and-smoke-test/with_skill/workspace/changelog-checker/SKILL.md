---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json`
   One pass lists every `.md` file sorted by version, checks each file starts with
   `## vX.Y.Z — YYYY-MM-DD`, and counts the entries per category (`Added`, `Fixed`,
   `Changed`, `Removed`, `Misc`) with totals across files.
   Exit 0 no findings, 1 findings, 2 the folder is missing, unreadable, or holds no `.md`.
   Exit 2 → stop and name the path that failed. Exit 1 → pass every finding line
   through to the user verbatim; each reads `<code> <file>: <detail>`.

2. Write a one-paragraph release narrative summarizing the overall direction of the changes
   for a non-technical reader. Source it from `.changelog-scan.json`.

3. Run exactly: `python3 scripts/render_summary.py .changelog-scan.json`
   It renders the versions, dates, and per-category entry counts sorted by version
   descending. Show its table to the user.

4. Step 1 already flagged every category tag outside the allowed list as an `unknown_tag`
   finding. For each entry under `misc_entries` in `.changelog-scan.json`, judge whether it
   actually fits `Added`, `Fixed`, `Changed`, or `Removed`, and suggest the move.

5. Verify the entries are clearly written and flag any that a reader would find confusing.

## Scripts

| Script (run, do not reimplement) | Does |
|---|---|
| `scripts/scan_changelogs.py <dir> --out F` | file list, header check, per-category counts, tag validation, Misc collection. Exit 0, 1, or 2 |
| `scripts/render_summary.py <scan.json>` | markdown summary table, versions descending. Exit 0 or 2 |

Finding codes from `scan_changelogs.py`: `header_not_first`, `header_malformed`,
`unknown_tag`, `entry_outside_category`. A `Misc` entry is not a finding, because
re-filing one is a judgment call left to step 4.
