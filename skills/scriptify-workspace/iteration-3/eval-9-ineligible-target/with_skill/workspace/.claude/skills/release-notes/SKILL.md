---
name: release-notes
description: Assembles release notes from the merged pull request titles in notes/ and writes a summary paragraph. Use when the user asks to build or draft release notes.
---

# Release Notes

Assemble the release notes for the current milestone.

## Workflow

1. Run exactly: `python3 scripts/scan_notes.py notes/ --json`
   One run covers steps 1 to 3: `files` and `total` are the sorted listing and
   the count, `findings` holds every header and `type:` problem, and `counts`
   holds the per-type tallies. Exit 0 clean, 1 findings, 2 usage error.
2. Findings present (exit 1) → report each one by file and code before going
   on. `bad_header` means the first line is not `PR #<number>: <title>`;
   `missing_type` means the file carries no `type:` line. A flagged file is
   left out of the grouped list in step 4.
3. Write a two-sentence summary of the release for the customer-facing
   changelog, using the `counts` and `entries` from step 1.
4. Run exactly: `python3 scripts/render_notes.py notes/`
   It prints the markdown list, grouped by type and sorted by PR number
   ascending, with flagged files under "Needs attention". Same exit codes as
   step 1.
