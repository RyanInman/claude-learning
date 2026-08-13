---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run the scan. It returns the file list, the files missing a level-1 heading,
   and the fenced code block counts in one pass:

   ```bash
   python3 scripts/lint_docs.py docs
   ```

   The JSON on stdout carries `file_count`, `files`, `missing_h1` (each entry
   with a `reason`), `code_blocks` per file, and `total_code_blocks`. Exit code
   2 means the directory is missing; findings never change the exit code.

2. Decide which of the `missing_h1` files matter most to fix this sprint, given
   that the tutorial pages get the most traffic. This is the judgment call the
   script does not make.

3. Report the file count, the flagged files with their reasons, the total code
   block count, and your fix order.

## Gotchas

- Do not rename or reuse `scripts/check_headings.py`. Despite its name it checks
  image alt text, not headings, and the release pipeline calls it by that exact
  path. The heading check lives in `scripts/lint_docs.py`.
- Read the counts from the script rather than re-deriving them by reading files,
  because a manual count drifts on every run and the script does not.
