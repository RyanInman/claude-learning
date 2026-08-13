---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run exactly: `python3 scripts/lint_docs.py docs/ --json`

   One pass over the tree carries the file inventory, the heading rule, and the
   fence tally. Exit 0 every file passes, 1 findings, 2 usage error.

   - `files` (sorted by path) and `file_count` — the docs inventory.
   - `findings` — one entry per file that does not start with a level-1
     heading followed by a blank line, coded `empty_file`, `no_h1`,
     `h1_not_first`, or `missing_blank_after_h1`.
   - `fenced_blocks` per file and `fenced_blocks_total`.

   Exit 0 → report the counts and stop, because nothing needs fixing.
   Large tree → add `--out findings.json` and read the file instead.

2. Decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic.
