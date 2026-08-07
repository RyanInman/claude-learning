---
name: release-notes
description: Assembles release notes from the merged pull request titles in notes/ and writes a summary paragraph. Use when the user asks to build or draft release notes.
---

# Release Notes

Assemble the release notes for the current milestone.

## Workflow

1. Run exactly: `python3 scripts/scan_notes.py notes/ --json`
   Stdout carries the total count and the filenames sorted by filename, the
   files whose first line is not of the form `PR #<number>:` under `invalid`,
   and the per-type (`feat`, `fix`, `chore`) grouping and tallies under
   `groups` and `counts`. Exit 0 clean, 1 findings, 2 usage error.
   Exit 1 → show the user every entry under `invalid` and `unknown_type`
   before going on; each names the file and the reason.
2. Write a two-sentence summary of the release for the customer-facing
   changelog, from the `counts` and `groups` of step 1. Save it to
   `summary.txt` in the working directory, then run exactly:
   `python3 scripts/check_summary.py summary.txt --json`
   Exit 1 → revise the draft for every code under `findings`, then re-run.
3. Run exactly:
   `python3 scripts/render_notes.py notes/ --summary-file summary.txt`
   Stdout is the final notes: a markdown list grouped by type, sorted by PR
   number ascending. Exit 1 → no valid entries; return to step 1's findings.
