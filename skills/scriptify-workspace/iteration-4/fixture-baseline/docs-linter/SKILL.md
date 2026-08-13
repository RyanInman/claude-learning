---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. List every `.md` file under `docs/`, sorted by path, and note the total
   count.
2. Check that each file starts with a level-1 heading followed by a blank line.
   Record every file that does not.
3. Count the fenced code blocks in each file and total them across files.
4. Decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic.
