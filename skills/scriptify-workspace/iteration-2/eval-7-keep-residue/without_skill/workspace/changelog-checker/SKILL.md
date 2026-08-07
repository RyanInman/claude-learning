---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary. The
mechanical steps run as scripts; only the judgment steps stay prose.

Run every script from the skill folder. `DIR` is the changelog folder, normally
`changelogs/`. Scripts exit `0` when clean, `1` when they found something to
report, `2` on a usage error.

## Workflow

1. **List and count** — `python3 scripts/list_changelogs.py DIR --json`
   Returns `count`, plus `versions` and `files` sorted by version ascending.
2. **Check headings** — `python3 scripts/check_headings.py DIR --json`
   Returns `findings`: files with no `## vX.Y.Z — YYYY-MM-DD` header, and files
   whose header version disagrees with the filename. Report each finding.
3. **Count entries** — `python3 scripts/count_entries.py DIR --json`
   Returns `per_file` counts, cross-file `totals`, and `total_entries`.
4. **Write the release narrative** — prose, no script. Read the entries and
   write one paragraph on the overall direction of the release for a
   non-technical reader. Name the user-visible theme, not the file counts.
5. **Render the table** — `python3 scripts/render_table.py DIR`
   Prints the markdown table, version descending. Paste its stdout unedited.
6. **Check category tags** — `python3 scripts/check_tags.py DIR --json`
   The script returns `invalid` (tags outside Added/Fixed/Changed/Removed/Misc)
   and `misc` (every entry tagged `Misc`). Report `invalid` as-is; then for each
   `misc` entry judge whether it belongs under Added, Fixed, Changed, or Removed
   and suggest the move with a one-line reason.
7. **Judge clarity** — prose, no script. Read every entry and flag any a reader
   would find confusing: unexplained jargon, missing subject, ambiguous scope.
   Quote the entry and give a clearer rewrite.

## Re-running the checks

Fixtures and the manifest live in `scripts/tests/`. Smoke-test every script:

```
python3 scripts/tests/run_smoke.py
```

Exit `0` and `all green` means every script still behaves. The manifest is
`scripts/tests/manifest.json`; it records each script's good, bad-data, and
bad-usage invocations with their expected exit codes and stdout.
