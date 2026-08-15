# Transcript notes

1. `mkdir -p .../outputs` + `cp -R .../fixtures/csv-report .../outputs/project`; `git init -q`, wrote `.gitignore` (`__pycache__/`, `.pytest_cache/`), `git add -A && git commit -qm baseline`; `find` to list files.
2. Read `project/report.py` and `project/tests/test_report.py` (parallel).
3. `od -c data/sales-2026-08.csv` and `od -c tests/data/clean.csv` — export file starts `357 273 277` (UTF-8 BOM), fixture does not. Root cause identified.
4. Reproduced: `python3 report.py data/sales-2026-08.csv` → `KeyError: 'region'`, exit 1. `python3 -m pytest -q` → 2 passed (confirms green suite).
5. Edited `project/report.py`: `encoding="utf-8"` → `encoding="utf-8-sig"` in `load()`.
6. Created `project/tests/data/bom.csv` via `printf '\xef\xbb\xbf...'`; verified BOM with `od -c`.
7. Edited `project/tests/test_report.py`: added `test_utf8_bom_header_is_parsed`.
8. Verified: script prints `east 30.00 / west 12.50`, exit 0; `pytest -q` → 3 passed.
9. Verified test is meaningful: `git stash push -q report.py`, ran the new test alone → FAILED with `KeyError: 'region'`; `git stash pop -q`, `pytest -q` → 3 passed.
10. Wrote `response.md`, `transcript-notes.md`, `metrics.json` in outputs dir.
