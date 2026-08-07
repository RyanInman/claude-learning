---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

All mechanical parsing, counting, checking, and table rendering is done by the
scripts in `scripts/`. Run them; do not re-derive their output by reading the
files yourself. Every script takes the changelog directory as its one positional
argument and supports `--help`.

## Workflow

1. List the changelog files, sorted by version, with a total count:

   ```bash
   python3 scripts/list_changelogs.py changelogs/
   ```

2. Check every file starts with `## vX.Y.Z — YYYY-MM-DD`:

   ```bash
   python3 scripts/check_headers.py changelogs/
   ```

   Exits 1 and prints one `FAIL <file>: <problem>` line per violation. Report
   those files verbatim.

3. Count entries per category per file, plus totals across files:

   ```bash
   python3 scripts/count_entries.py changelogs/
   ```

4. Write a one-paragraph release narrative summarizing the overall direction of
   the changes for a non-technical reader. This is yours to write — read the
   entry text and judge what the release is actually about. Do not just restate
   the counts.

5. Render the summary table (versions, dates, per-category counts, version
   descending):

   ```bash
   python3 scripts/render_table.py changelogs/
   ```

   Add `--include-misc` when step 6 found `Misc` entries. Paste the output as-is.

6. Check every entry's category tag against the allowed list:

   ```bash
   python3 scripts/check_categories.py changelogs/
   ```

   Exits 1 on any tag outside `Added`, `Fixed`, `Changed`, `Removed`, `Misc`.
   For each `MISC` line it prints, judge whether the entry actually fits one of
   the other four categories and suggest the move, with a one-line reason. That
   judgment is yours; the script only finds the candidates.

7. Verify the entries are clearly written and flag any that a reader would find
   confusing. Read the entry text and judge; there is no script for this.

## Scripts

`scripts/manifest.json` lists each script, the step it serves, and its known-good
and bad-data invocations. `scripts/changelog_lib.py` is the shared parser the
CLIs import — it is not a CLI itself.
