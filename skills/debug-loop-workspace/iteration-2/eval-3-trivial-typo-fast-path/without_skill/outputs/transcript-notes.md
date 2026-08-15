# Transcript notes

1. Bash: `cp -R .../fixtures/slug-typo .../outputs/project && cd project && git init -q && printf '__pycache__/\n.pytest_cache/\n' > .gitignore && git add -A && git commit -qm baseline && ls -la`
2. Read: `project/slug.py` (9 lines) — saw `text.lower().stip()` on line 7.
3. Edit: `project/slug.py` — `text.lower().stip()` → `text.lower().strip()`
4. Bash: `python3 -m pytest -q` in project → `3 passed in 0.00s`
5. Write: `outputs/response.md`
6. Write: `outputs/transcript-notes.md`
7. Write: `outputs/metrics.json`
