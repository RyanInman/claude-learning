1. `cp -R .../evals/fixtures/slug-typo .../outputs/project`
2. `cd project && git init -q && printf '__pycache__/\n.pytest_cache/\n' > .gitignore && git add -A && git commit -qm baseline && ls -la`
3. Read `/Users/admin/claude-learning/skills/running-debug-loops/SKILL.md`
4. Read `project/slug.py`
5. `ls tests && python3 -m pytest tests -q` → 3 failed, AttributeError at slug.py:7
6. Edit `project/slug.py`: `text.lower().stip()` → `text.lower().strip()`
7. `python3 -m pytest tests -q` → 3 passed
8. `git add -A && git commit -qm "fix: correct stip -> strip typo in slugify" && git log --oneline`
9. Wrote `outputs/response.md`, `outputs/transcript-notes.md`, `outputs/metrics.json`
