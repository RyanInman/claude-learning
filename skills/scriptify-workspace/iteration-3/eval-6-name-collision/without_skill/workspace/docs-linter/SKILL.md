---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run the structural scan:

   ```bash
   python3 scripts/lint_docs_structure.py docs
   ```

   It lists every `.md` file under `docs/` sorted by path with the total count,
   flags each file that does not start with a level-1 heading followed by a
   blank line, and counts the fenced code blocks per file and in total. Add
   `--json` when you want to post-process the result. It exits 1 when any file
   is flagged, so read the report rather than the exit code alone.

2. Decide which of the flagged files matter most to fix this sprint, given that
   the tutorial pages get the most traffic.

## Gotchas

- `scripts/check_headings.py` does not check headings. It checks image alt text
  and the release pipeline calls it at that exact path, so leave its name and
  behaviour alone. The heading and code-block checks live in
  `scripts/lint_docs_structure.py`.
