---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/list_changelogs.py changelogs/ --json`
   Stdout carries `count` and `files`, version ascending. Exit 1 → the folder holds no `.md` files, so say so and stop.
2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
   Exit 0 clean, 1 findings, 2 usage error. Each finding names `file`, `issue` (`missing_version_header` or `malformed_version_header`) and `line`. Report them all.
3. Run exactly: `python3 scripts/count_entries.py changelogs/ --json`
   `per_file[].counts` holds the per-file per-category counts, `totals` and `total_entries` the cross-file totals.
4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader. Ground it in step 3's `totals` and the entry texts from step 7. No script writes this paragraph.
5. Run exactly: `python3 scripts/render_table.py changelogs/`
   The markdown table arrives on stdout, version descending. Exit 1 → a row reads `unknown`, because that file has no version heading; it is the same file step 2 flagged.
6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
   Tags outside the allowed list come back under `invalid`; report those as they stand. For each entry under `misc`, judge whether it actually fits one of the other categories and suggest the move.
7. Run exactly: `python3 scripts/list_entries.py changelogs/ --json`
   Every entry comes back with its `text` plus neutral length facts. Judge which entries a reader would find confusing and flag those, quoting `file` and `line`. The script scores nothing.

## Bundled scripts

All six scripts take the changelogs folder as their one positional argument, share `scripts/changelog_lib.py`, and use exit 0 clean / 1 findings / 2 usage error.

Their fixtures and manifest ship in `scripts/tests/`. Re-verify every script with:

    python3 /Users/admin/claude-learning/skills/scriptify/scripts/smoke_test.py scripts/tests/manifest.json
