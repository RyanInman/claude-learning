---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out scan.json`
   Stdout carries the file count, the entry total, and one line per file, sorted
   by version. `scan.json` holds the per-file, per-category counts. Exit 0
   scanned, 2 the folder is missing or unreadable.
2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
   Exit 0 clean, 1 findings on stdout under `findings`, 2 usage error. Each
   finding names its condition: `no_h2_first_line`, `h2_not_version_dated`, or
   `version_filename_mismatch`. Report every finding with its file.
3. Covered by step 1. Per-category counts are in `scan.json` under
   `files[].counts`, and the cross-file totals under `totals`.
4. Write a one-paragraph release narrative summarizing the overall direction of
   the changes for a non-technical reader.
5. Run exactly: `python3 scripts/render_summary.py changelogs/`
   Stdout is the finished markdown table, sorted by version descending. Paste it
   verbatim. Exit 0 rendered, 2 the folder is missing or unreadable.
6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
   Exit 0 clean, 1 findings, 2 usage error. Tags outside the allowed list come
   back under `invalid` as `unknown_category`. For each entry under `misc`,
   judge whether it actually fits one of the categories in its `candidates` list
   and suggest the move.
7. Verify the entries are clearly written and flag any that a reader would find
   confusing.

## Re-running the checks

The bundled scripts ship with their fixtures and a manifest. To verify them
after editing one, run exactly:

    python3 scripts/tests/smoke_test.py scripts/tests/manifest.json

Exit 0 every check passed, 1 a check failed, 2 the manifest is unusable.
