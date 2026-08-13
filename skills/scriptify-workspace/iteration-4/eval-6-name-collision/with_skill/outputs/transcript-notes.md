# Transcript notes — order of work

## Reads (no side effects)

1. `RUN_INSTRUCTIONS_with_skill.md`
2. `/Users/admin/claude-learning/skills/scriptify/SKILL.md`
3. target `workspace/docs-linter/SKILL.md`
4. target `workspace/docs-linter/scripts/check_headings.py`
5. `scriptify/references/delegation-rubric.md` (at Step 2, as instructed)
6. `scriptify/references/applying.md` (after the gate, as instructed)
7. `scriptify/references/script-conventions.md` (before writing the script)

## Commands, in order

| # | Command | Exit |
|---|---|---|
| 1 | `ls` RUN_DIR, `cat prompt.txt`, `ls -R` eval dir | 0 |
| 2 | eligibility: `test -w`, `stat -f %Su`, `git status --porcelain <target>/SKILL.md`, `cat` the three docs files | 0 |
| 3 | `cp SKILL.md scratch/.delegation-review/SKILL.md.orig` | 0 |
| 4 | `python3 scriptify/scripts/inventory.py <target> --out scratch/.delegation-review/inventory.json` | 0 |
| 5 | `python3 scriptify/scripts/sample_target_data.py <target>` | 0 |
| 6 | `sed -n 1,60p render_report.py` (schema header) | 0 |
| 7 | `python3 <target>/scripts/check_headings.py <target>/docs` (interface audit of the existing script) | 1 (expected: api.md has an empty alt text) |
| 8 | `python3 scriptify/scripts/render_report.py classification.json inventory.json --out report-table.md` | 0 |
| 9 | `python3 scriptify/scripts/new_manifest.py --help` | 0 |
| 10 | `python3 scriptify/scripts/new_manifest.py classification.json --target <target> --out manifest.json --fixtures ...` | 0 |
| 11 | fixture restructure into per-code directories, then fill both `TODO:` values plus 4 extra invocations | 0 |
| 12 | `python3 <target>/scripts/lint_docs.py --help` | 0 |
| 13 | `python3 <target>/scripts/lint_docs.py <target>/docs --json` | 1 (expected: 2 heading findings) |
| 14 | `python3 scriptify/scripts/smoke_test.py manifest.json` | 0 (10/10 PASS) |
| 15 | `diff -u SKILL.md.orig <target>/SKILL.md` | 1 (differences, as intended) |
| 16 | `diff -q without_skill/.../check_headings.py with_skill/.../check_headings.py` | 0 (byte-identical) |
| 17 | `python3 scripts/lint_docs.py docs/ --json` run from inside the target, to prove the pinned relative invocation works | 1 (expected) |
| 18 | `rm -rf scratch/.delegation-review` (residue not kept, green run) | 0 |

One command errored on a bad path: an attempted `git show HEAD:...check_headings.py` comparison, because the fixture is untracked. Replaced with the `diff -q` against the pristine `without_skill` copy (row 16).

## Files created or rewritten

Created:
- `workspace/docs-linter/scripts/lint_docs.py` (new script, the only file added to the target)
- `scratch/.delegation-review/SKILL.md.orig` (restore point, later removed with the review dir)
- `scratch/.delegation-review/inventory.json`
- `scratch/.delegation-review/classification.json`
- `scratch/.delegation-review/report-table.md`
- `scratch/.delegation-review/manifest.json`
- `scratch/.delegation-review/fixtures/lint_docs/good/clean.md`, `good/nested/page.md`
- `scratch/.delegation-review/fixtures/lint_docs/bad/first-line-not-h1/prose-first.md`
- `scratch/.delegation-review/fixtures/lint_docs/bad/no-h1-anywhere/no-h1.md`
- `scratch/.delegation-review/fixtures/lint_docs/bad/missing-blank/no-blank.md`
- `outputs/report.md`, `outputs/gate.md`, `outputs/transcript-notes.md`, `outputs/metrics.json`

Rewritten:
- `workspace/docs-linter/SKILL.md` (one atomic pass, after the green smoke test)

Not touched:
- `workspace/docs-linter/scripts/check_headings.py` (verified byte-identical to the pristine copy)
- `workspace/docs-linter/docs/**` (read only)
- `/Users/admin/claude-learning/skills/scriptify/evals/fixtures/` (never read, never written)

Removed at Step 9, per the no-residue pick: `scratch/.delegation-review/`.
