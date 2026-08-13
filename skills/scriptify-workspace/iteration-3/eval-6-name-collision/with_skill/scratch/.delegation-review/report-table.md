## Delegation review: docs-linter

**Verdict:** 3 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~67 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file under `docs/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob docs/**/*.md, sort by path, count - same output every run | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: files[] sorted, file_count, h1_violations[], fence counts, exit 0 clean / 1 h1 violations found / 2 usage |
| s2 | "Check that each file starts with a level-1 heading followed by a blank line." (L15-16) | numbered-list | 28 | SCRIPT | fixed regex rule (first line is '# ' and line 2 blank); a unit test is writable now. NOT already delegated: scripts/check_headings.py checks image alt text despite its name | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: h1_violations[] with path and reason, exit 0 clean / 1 h1 violations found / 2 usage |
| s3 | "Count the fenced code blocks in each file and total them across files." (L17-17) | numbered-list | 18 | SCRIPT | counting fenced blocks per file and totalling is pure aggregation | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: per-file fenced_blocks and fenced_blocks_total, exit 0 clean / 1 h1 violations found / 2 usage |
| s4 | "Decide which of the flagged files matter most to fix this sprint, given that" (L18-19) | numbered-list | 30 | CLAUDE | prioritising which flagged files to fix this sprint weighs traffic against effort; reasonable runs should differ, and the script shell around it (the flagged list) is already produced by lint_docs.py | - |
