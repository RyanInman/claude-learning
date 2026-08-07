---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run exactly: `python3 scripts/docs_stats.py docs/`
   Stdout JSON carries `files`, sorted by path, and `file_count`. Exit 0 stats
   emitted, 2 unreadable directory. Big tree → add `--out stats.json` and read
   the file.
2. Run exactly: `python3 scripts/check_h1.py docs/`
   Exit 0 clean, 1 findings (JSON on stdout), 2 usage error. Every entry under
   `missing_h1` names the file and the reason it failed.
3. Step 1's JSON already holds the code-block counts: `code_blocks` per file
   and `total_code_blocks` across files. Re-run
   `python3 scripts/docs_stats.py docs/` if that output is gone.
4. Step 2 exit 0 → nothing flagged, stop here. Otherwise decide which of the
   files under `missing_h1` matter most to fix this sprint, given that the
   tutorial pages get the most traffic.
