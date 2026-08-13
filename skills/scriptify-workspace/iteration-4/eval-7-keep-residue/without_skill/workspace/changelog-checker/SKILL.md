---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

### 1. Scan the folder

Run the checker once. It does the whole deterministic pass — file inventory and
version sort, heading-format check, per-category entry counts, the summary
table, and category-tag validation:

```bash
python3 scripts/check_changelogs.py changelogs
```

It prints one JSON report and exits 0. Read these fields:

| Field | Use it for |
|---|---|
| `file_count`, `files_sorted` | the file inventory, sorted by version ascending |
| `heading_violations` | files whose first line is not `## vX.Y.Z — YYYY-MM-DD` |
| `files[].counts`, `totals`, `grand_total` | per-file and cross-file entry counts |
| `table_markdown` | the summary table, sorted by version descending |
| `unknown_tags` | category headings outside the allowed list |
| `misc_entries` | every `Misc` entry, with its file |

Paste `table_markdown` into the report unchanged. Do not recount entries or
re-sort the table by hand, because the script already did it and a second pass
only invites drift.

### 2. Write the release narrative

Write one paragraph for a non-technical reader summarizing the overall
direction of the changes. Use the counts and the entry text from step 1 as
input; the judgment about what the release *means* is yours.

### 3. Re-categorize the Misc entries

For each item in `misc_entries`, judge whether it actually belongs under
`Added`, `Fixed`, `Changed`, or `Removed`, and suggest the move. Report any
`unknown_tags` as tag errors to correct.

### 4. Flag confusing entries

Read the entry text and flag any entry a reader would find unclear or
ambiguous. Quote the entry and say what is missing.

## Re-running the checks

The fixtures and the manifest live inside this skill. From this folder, run:

```bash
python3 scripts/tests/run_tests.py
```

It confirms every fixture path in `scripts/tests/manifest.json` resolves, runs
`check_changelogs.py` against each fixture directory, compares the JSON against
the expected values, and exits 0 when all cases pass.

## Layout

```
scripts/check_changelogs.py      deterministic scan, prints JSON
scripts/tests/run_tests.py       smoke-test runner
scripts/tests/manifest.json      fixture paths + expected values
scripts/tests/fixtures/sample/   three changelogs, one missing its heading
scripts/tests/fixtures/edge/     unknown tag, Removed and Misc entries
```

## Gotchas

- The heading check requires an em dash (`—`), not a hyphen, because that is
  the separator the existing changelogs use.
- Entries under an unrecognized heading (for example `### Security`) are
  reported in `unknown_tags` but excluded from the counts, so `grand_total`
  can be lower than the raw bullet count.
- `manifest.json` stores absolute paths. Moving or renaming this skill folder
  breaks the smoke test until you regenerate the manifest.
