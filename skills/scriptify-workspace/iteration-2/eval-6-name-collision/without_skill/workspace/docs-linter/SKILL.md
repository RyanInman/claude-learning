---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Inventory the docs tree:

   ```bash
   python3 scripts/list_docs.py docs
   ```

   Prints every `.md` file sorted by path plus the total count. Add `--json`
   for machine-readable output.

2. Check level-1 heading structure:

   ```bash
   python3 scripts/check_h1_structure.py docs
   ```

   Flags every file that does not start with a level-1 heading followed by a
   blank line, with the reason per file. Exit code 1 means at least one file
   was flagged; 0 means clean.

   Note: `scripts/check_headings.py` is a different, pre-existing script that
   checks image alt text. Do not confuse the two, and do not replace it.

3. Count fenced code blocks:

   ```bash
   python3 scripts/count_code_blocks.py docs
   ```

   Prints the per-file count and the total across files.

4. Decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic. This is a judgement call — weigh the
   step 2 flags against page traffic and sprint priorities, and say which files
   to fix now and which can wait. No script decides this.
