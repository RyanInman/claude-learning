---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run the checker and read its JSON:

   ```bash
   python3 scripts/check_changelogs.py changelogs
   ```

   It lists the files sorted by version descending, validates each heading against
   `## vX.Y.Z — YYYY-MM-DD`, counts entries per category, totals them, flags categories
   outside the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`), and renders
   the summary table. Do not recount by hand — the script is the single source of the numbers.

2. Print the `table` field verbatim as the summary table.

3. Report `heading_problems` and `unknown_category_uses` as the structural findings. Say
   "no structural problems found" when both are empty.

4. Write a one-paragraph release narrative for a non-technical reader, using `totals` and the
   entry text to describe the overall direction of the changes.

5. For each item in `misc_entries`, judge whether it belongs in `Added`, `Fixed`, `Changed`, or
   `Removed`, and suggest the move with a one-line reason. Leave it in `Misc` when none fits.

6. Read the entries themselves and flag any a reader would find confusing, quoting the entry and
   naming what is unclear.

## Script output

`scripts/check_changelogs.py <changelogs-dir>` prints one JSON object:

| Field | Meaning |
|---|---|
| `file_count`, `total_entries` | Totals across the folder |
| `files[]` | Per file: `version`, `date`, `heading_ok`, `heading_problem`, `counts`, `unknown_categories`, `misc_entries` — sorted by version descending |
| `totals` | Entry count per category across all files |
| `heading_problems[]` | Files whose first line is not a valid version heading |
| `unknown_category_uses[]` | Uses of a category outside the allowed list |
| `misc_entries[]` | Every `Misc` entry, with its file — the input to step 5 |
| `table` | The rendered summary table, ready to print |

## Tests

`tests/manifest.json` lists the fixture cases and the expected JSON for each. Re-run them after
any change to the script:

```bash
python3 tests/run_tests.py
```

Regenerate an expected file only when the change to the script output is intended:

```bash
python3 scripts/check_changelogs.py tests/fixtures/clean > tests/expected/clean.json
```

## Gotchas

- The script exits 2 for a missing or empty folder and 0 for a successful scan even when it finds
  problems, because a findings-based exit code cannot be told apart from a crash.
- The heading check requires an em dash (`—`), not a hyphen, so a hyphenated heading is reported
  as a problem. That is the documented format.
- A file whose heading is missing still gets a version when the filename looks like `v1.2.0.md`,
  so it sorts into place; its `date` stays `null` and shows as `(missing)` in the table.
- The `Other` column appears in the table only when some file uses a category outside the allowed
  list, so the row cells always add up to the `Total` column.
