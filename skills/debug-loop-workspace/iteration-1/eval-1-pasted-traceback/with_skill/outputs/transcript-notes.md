# Transcript notes

1. `mkdir -p .../outputs` + `cp -R .../fixtures/csv-report .../outputs/project`; `git init -q && git add -A && git commit -qm baseline` (76faed8); `find` to list project files.
2. Read `/Users/admin/claude-learning/skills/running-debug-loops/SKILL.md`.
3. Read `project/report.py` and `project/tests/test_report.py`.
4. `od -c` on `data/sales-2026-08.csv` and `tests/data/clean.csv` → export starts `357 273 277` (EF BB BF, UTF-8 BOM); fixture does not.
5. Repro: `python3 report.py data/sales-2026-08.csv` → `KeyError: 'region'`, exit=1. `python3 -m pytest -q` → `2 passed`.
6. Instrument: `python3 -c "import report; print keys of first row"` → `["'\\ufeffregion'", "'amount'"]`. Hypothesis 1 confirmed; 2 and 3 dead.
7. Created `tests/data/bom.csv` via `printf '\xef\xbb\xbf...'`; verified bytes with `od -c`.
8. Edited `tests/test_report.py` — added `test_utf8_bom_header_is_not_part_of_first_column_name`.
9. `pytest -q` → `1 failed, 2 passed` (red as intended). Committed test only: `6abab5c` "test: failing test for UTF-8 BOM in CSV header (no fix yet)". No impl code changed.
10. Edited `report.py`: `encoding="utf-8"` → `encoding="utf-8-sig"` (one line).
11. `pytest -q` → `3 passed`; `python3 report.py data/sales-2026-08.csv` → `east 30.00 / west 12.50`, exit=0.
12. Causality check: `git stash` → `pytest -q` = `1 failed, 2 passed`. `git stash pop` blocked by tracked `__pycache__/*.pyc` (error). `git checkout -- __pycache__` then `git stash pop` succeeded → `3 passed`.
13. Wrote `.gitignore` (`__pycache__/`, `.pytest_cache/`); committed fix `c214906`.
14. `git rm -r --cached __pycache__ tests/__pycache__ .pytest_cache` failed (`.pytest_cache` not tracked); re-ran without it, committed "chore: untrack bytecode cache". `git status --short` clean.
15. `git diff --stat 76faed8 HEAD -- report.py tests/` → report.py 1 line, tests/data/bom.csv new, tests/test_report.py +5.
16. Wrote `response.md`, `transcript-notes.md`, `metrics.json`, `user_notes.md` in outputs dir.
