---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out scan.json`
   Exit 0 the scan is written and stdout carries the file count, the entry total, and one line per file, sorted by version; exit 1 the folder holds no `.md` files, so say so and stop; exit 2 usage error.
2. Run exactly: `python3 scripts/check_changelogs.py changelogs/ --json`
   Exit 0 clean, 1 findings, 2 usage error. Heading problems arrive under `violations` with codes `no_version_heading`, `version_heading_not_first`, and `malformed_version_heading`. Report every file named there. Keep this JSON; step 6 reads it too.
3. Per-category counts come from `scan.json`: `counts` per file, `totals` across files.
4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
5. Run exactly: `python3 scripts/render_summary.py scan.json`
   Exit 0 the markdown table is on stdout, sorted by version descending; exit 1 `invalid_scan`, so re-run step 1.
6. Read the step 2 findings. Entries under a category outside the allowed list arrive as `invalid_tag`. For each entry under `misc`, judge whether it actually fits `Added`, `Fixed`, `Changed`, or `Removed`, and suggest the move.
7. Read `entries` in `scan.json` and flag any entry a reader would find confusing.

## Verifying the scripts

Run exactly: `python3 scripts/tests/smoke_test.py scripts/tests/manifest.json`
Exit 0 every script still meets its contract, 1 a check failed, 2 the manifest is missing or malformed.
