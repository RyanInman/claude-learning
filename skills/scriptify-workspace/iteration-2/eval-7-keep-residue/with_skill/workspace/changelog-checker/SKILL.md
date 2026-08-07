---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/parse_changelogs.py changelogs/ --json --out .changelog-check/parsed.json`
   Every `.md` file in `changelogs/`, sorted by version, with per-file and
   cross-file per-category counts. Stdout carries the file count and the entry
   total. Exit 0 parsed, 1 no changelog files, 2 usage or unreadable dir.
2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
   Exit 0 clean, 1 findings (JSON on stdout under `findings`), 2 usage error.
   Each finding names the file and the reason, `missing_version_header` or
   `malformed_version_header`.
3. Per-category counts (`Added`, `Fixed`, `Changed`, `Removed`) come from
   step 1: `files[].counts` per file, `totals` across files. Read them from
   `.changelog-check/parsed.json`; do not recount by hand.
4. Write a one-paragraph release narrative summarizing the overall direction of
   the changes for a non-technical reader. Draw the facts from `totals` and the
   entry text in `.changelog-check/parsed.json`.
5. Run exactly: `python3 scripts/render_summary_table.py .changelog-check/parsed.json`
   Renders versions, dates, and per-category entry counts, sorted by version
   descending. Exit 1 means the parsed JSON holds no files.
6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
   Tags outside the allowed list (`Added`, `Fixed`, `Changed`, `Removed`,
   `Misc`) come back under `invalid`. For each entry under `misc`, judge
   whether it actually fits one of the other categories and suggest the move.
   Exit 0 means no invalid tags and no Misc entries, so there is nothing to
   re-triage.
7. Run exactly: `python3 scripts/parse_changelogs.py changelogs/ --entries`
   Every entry comes back with its file, category, and text. Read them and
   verify the entries are clearly written; flag any that a reader would find
   confusing.

## Verifying the scripts

`scripts/tests/` holds the fixtures and the manifest for the four scripts.
Re-run the checks with:

    python3 <scriptify-skill>/scripts/smoke_test.py scripts/tests/manifest.json

Exit 0 means every script still matches its declared interface and still
discriminates good fixtures from bad ones.
