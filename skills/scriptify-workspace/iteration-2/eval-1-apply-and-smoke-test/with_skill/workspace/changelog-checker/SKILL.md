---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --json`
   Exit 0 scanned, 1 no changelog files (stop and say so), 2 usage error.
   `files` is sorted by version ascending; `file_count` is the total.
2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
   Exit 0 clean, 1 findings (JSON on stdout), 2 usage error. Each finding
   names the file missing a `## vX.Y.Z — YYYY-MM-DD` header.
3. Per-category counts come from step 1's scan: `files[].counts` per file and
   `totals` across files. Do not re-count by hand.
4. Write a one-paragraph release narrative summarizing the overall direction of
   the changes for a non-technical reader. Draw on the entries in step 1's
   `files[].entries`.
5. Run exactly: `python3 scripts/render_summary.py changelogs/`
   Prints the versions/dates/per-category table, sorted by version descending.
6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
   Tags outside the allowed list (`Added`, `Fixed`, `Changed`, `Removed`,
   `Misc`) come back under `invalid`, exit 1. For each entry under `misc`,
   judge whether it actually fits one of the other categories and suggest the
   move.
7. Read the entries listed under `files[].entries` from step 1 and flag any
   that a reader would find confusing.

## Scripts

| Script | Does |
|---|---|
| `scripts/scan_changelogs.py <dir> [--json] [--out F]` | files by version, per-category counts, totals, every entry. Exit 0/1/2 |
| `scripts/check_headings.py <dir> [--json] [--out F]` | version-header check. Exit 0 clean / 1 findings / 2 usage |
| `scripts/check_tags.py <dir> [--json] [--out F]` | tag allow-list check plus Misc entries to re-triage. Exit 0/1/2 |
| `scripts/render_summary.py <dir> [--out F]` | summary table, version descending. Exit 0/1/2 |

`scripts/_changelog.py` is the shared parser the four scripts import. It has no
CLI; never invoke it directly.
