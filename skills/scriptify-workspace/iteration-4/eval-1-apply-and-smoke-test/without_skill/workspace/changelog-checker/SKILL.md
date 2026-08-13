---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. Run the scan script from the project root:

   ```bash
   python3 scripts/check_changelogs.py changelogs
   ```

   It prints the file inventory, the heading-format violations, the per-category
   entry counts, the version-sorted summary table, the category-tag violations,
   and every entry grouped by version. Pass a different folder path as the
   argument when the changelogs live elsewhere. The script exits non-zero when
   the folder is missing or holds no `.md` files.

2. Write a one-paragraph release narrative for a non-technical reader, using the
   counts and entries the script printed to describe the overall direction of the
   changes.

3. For each entry the script lists under "Misc entries needing a judgment call",
   decide whether it fits `Added`, `Fixed`, `Changed`, or `Removed`, and suggest
   the move. The script cannot make this call because it depends on what the
   entry means, not on how it is tagged.

4. Read the entry text in the script's "All entries" section and flag any entry a
   reader would find confusing.

5. Report the script's output followed by your narrative, your `Misc` reclassifications,
   and your clarity flags.

## Gotchas

- Run the script rather than counting by hand, because a hand count drifts between
  runs and misses files that lack a version heading.
- The script sorts versions numerically, so `v10.0.1` ranks above `v2.0.0`. Do not
  re-sort the table as text.
- A file with no valid heading still appears in the table; the script recovers its
  version from the filename and prints `missing` for the date.
