---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

Two scripts do the mechanical work — enumerating files, validating headings, counting
entries, rendering the table. Do not redo any of that by hand or by reading the files
yourself; run the scripts and spend your own effort on the judgement calls in steps 3-5.

## Workflow

### 1. Scan (replaces the old steps 1, 2, 3, and the tag check in 6)

```bash
python3 scripts/scan_changelogs.py changelogs -o /tmp/changelog-scan.json
```

Pass a different folder as the first argument if the changelogs live elsewhere. The
script writes one JSON report containing: the version-sorted file list and total count,
each file's heading validation, per-file and total entry counts per category, any
category tag outside `Added`/`Fixed`/`Changed`/`Removed`/`Misc`, every `Misc` entry, and
the full text of every entry.

Exit `2` means the folder is missing or holds no `.md` files — report that and stop.

Read the JSON once. It carries every entry's text, so you never need to open the
changelog files individually.

### 2. Render the summary table (replaces the old step 5)

```bash
python3 scripts/render_summary.py /tmp/changelog-scan.json
```

Prints the version-descending table of versions, dates, and per-category counts, plus the
structural-problem sections. Paste that output into your reply as-is. Exit `1` just means
structural problems exist and are listed in the output; it is not a script failure.

### 3. Write the release narrative (was step 4)

From the entry text in the scan JSON, write one paragraph summarizing the overall
direction of the release for a non-technical reader. Name the theme, not the individual
commits.

### 4. Judge the `Misc` entries (was the second half of step 6)

The scan lists every `Misc` entry. For each one, decide whether it actually belongs in
`Added`, `Fixed`, `Changed`, or `Removed`, and recommend the move with a one-line reason.
Leave it in `Misc` if none of the four genuinely fit.

### 5. Flag confusing entries (was step 7)

Read the entry text in the scan JSON and flag any entry a reader outside the team would
not understand — unexplained internal names, missing subject, or an effect the reader
cannot infer. Suggest a clearer rewording for each.

## Re-running the script checks

The scripts ship with fixtures and a manifest so the checks can be re-run at any time:

```bash
python3 tests/run_smoke_tests.py          # all checks
python3 tests/run_smoke_tests.py -v       # with the reason for each check
python3 tests/run_smoke_tests.py --only scan-problems
```

`tests/manifest.json` holds the check definitions (script, args, expected exit code,
expected JSON fields and output text); `tests/fixtures/` holds the sample changelog
folders they run against. Add a fixture plus a manifest entry whenever the scripts learn
a new rule.
