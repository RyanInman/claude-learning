---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run exactly: `python3 scripts/scan_docs.py docs/ --json`
   Exit 0, `files` (sorted paths) and `file_count` on stdout. Exit 2 usage
   error.
2. Run exactly: `python3 scripts/check_h1_headings.py docs/ --json`
   Exit 0 clean, 1 findings (`findings[].path` and `.issue` on stdout,
   `missing_h1` or `missing_blank_after_h1`), 2 usage error.
3. Read `code_blocks` (per file) and `total_code_blocks` from the step 1 output.
   No second scan needed.
4. If step 2 exited 0 → nothing to prioritize, report clean and stop. Otherwise
   decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic.

## Scripts

| Script | Does |
|---|---|
| `scripts/scan_docs.py <docs-dir> --json` | file list, count, fenced-code-block counts and total. Exit 0 or 2 |
| `scripts/check_h1_headings.py <docs-dir> --json` | flags files missing an H1 + blank line. Exit 0, 1, or 2 |
| `scripts/check_headings.py <docs-dir>` | unrelated to this workflow: checks image alt text. Kept for the release pipeline |
