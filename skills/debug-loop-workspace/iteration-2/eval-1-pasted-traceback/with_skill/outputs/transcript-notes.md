# Transcript notes

1. Bash: `cp -R` fixture `csv-report` → `outputs/project`; `git init -q`; wrote `.gitignore` (`__pycache__/`, `.pytest_cache/`); `git add -A && git commit -qm baseline`; `ls -R`.
2. Read: `/Users/admin/claude-learning/skills/running-debug-loops/SKILL.md`.
3. Read: `project/report.py`; Read: `project/tests/test_report.py`; Bash: `od -c data/sales-2026-08.csv | head -20` + `head -3 tests/data/clean.csv` (parallel).
4. Bash (repro): `python3 report.py data/sales-2026-08.csv` → KeyError, exit 1; `python3 -m pytest tests -q` → 2 passed.
5. Bash (instrument): `python3 -c` printing `list(rows[0].keys())` and `repr` of first key → `'﻿region'`. Hypothesis 1 confirmed.
6. Bash: wrote `tests/data/bom.csv` via `printf '\xef\xbb\xbf...'`; verified bytes with `od -c`.
7. Edit: `tests/test_report.py` — added `test_utf8_bom_header_is_parsed`.
8. Bash: `pytest tests -q` → 1 failed, 2 passed; `git commit -qm "failing test: BOM header"` (df84b43). No impl code touched.
9. Edit: `report.py` — `encoding="utf-8"` → `encoding="utf-8-sig"` in `load()`.
10. Bash (check): `pytest tests -q` → 3 passed; `python3 report.py data/sales-2026-08.csv` → east 30.00 / west 12.50, exit 0.
11. Bash (revert check): `git stash` → 1 failed, 2 passed; `git stash pop` → 3 passed; `git commit -qm "fix: read CSV as utf-8-sig..."` (05dabc5); `git log --oneline`.
12. Write: `outputs/response.md`, `outputs/transcript-notes.md`, `outputs/metrics.json`.
