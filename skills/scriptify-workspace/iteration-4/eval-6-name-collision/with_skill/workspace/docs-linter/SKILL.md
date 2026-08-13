---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run exactly: `python3 scripts/lint_docs.py docs/ --json`
   One pass covers the file inventory, the level-1 heading rule, and the
   fenced-block counts. Exit 0 no heading findings, 1 findings, 2 usage error.
   Read `files` and `file_count` for the sorted inventory, `h1_findings` for
   the flagged files, and `fence_counts` with `fence_total` for the block
   counts. Finding codes: `first_line_not_h1`, `no_h1_anywhere`,
   `h1_missing_blank_line`.
2. Decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic.
