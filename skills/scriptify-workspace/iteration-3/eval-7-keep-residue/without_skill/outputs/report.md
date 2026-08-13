# changelog-checker: script extraction

Moved every deterministic step of the workflow into one bundled script and left the judgment
steps as prose. The skill went from 7 hand-executed steps to 1 script call plus 5 steps that
read its output.

## Step classification

| # | Original step | Verdict | Where it lives now |
|---|---|---|---|
| 1 | List `.md` files sorted by version, note the count | Deterministic | `scripts/check_changelogs.py` -> `files[]`, `file_count` |
| 2 | Check each heading matches `## vX.Y.Z — YYYY-MM-DD` | Deterministic | script -> `heading_problems[]` |
| 3 | Count entries per category and total them | Deterministic | script -> `files[].counts`, `totals`, `total_entries` |
| 4 | Write a release narrative for a non-technical reader | Judgment | stays prose (step 4) |
| 5 | Render the summary table sorted by version descending | Deterministic | script -> `table` |
| 6 | Validate category tags, then judge whether `Misc` entries fit elsewhere | Split | validation -> script (`unknown_category_uses[]`, `misc_entries[]`); the judgment stays prose (step 5) |
| 7 | Flag entries a reader would find confusing | Judgment | stays prose (step 6) |

Step 6 was the only one that mixed the two. Checking a tag against a fixed list of five strings
is a set membership test; deciding whether "Corrected typo in settings page label" is really a
`Fixed` needs a reader. The script now surfaces every `Misc` entry with its file, so the
judgment step gets its input handed to it instead of re-scanning the files.

## What I built

`scripts/check_changelogs.py <changelogs-dir>` prints one JSON object and exits 0 on a
successful scan, 2 on a missing or empty folder. Fields: `file_count`, `total_entries`,
`files[]` (per file `version`, `date`, `heading_ok`, `heading_problem`, `counts`,
`unknown_categories`, `misc_entries`, sorted by version descending), `totals`,
`heading_problems[]`, `unknown_category_uses[]`, `misc_entries[]`, and `table` — the rendered
summary table, ready to print verbatim.

Three details worth knowing:

- The exit code reports whether the scan ran, not whether it found problems, because a
  findings-based non-zero exit is indistinguishable from a crash.
- A file with a missing heading still gets its version from a filename like `v1.2.0.md`, so it
  sorts into position; its date shows as `(missing)`.
- The table grows an `Other` column only when some file uses a category outside the allowed
  list, so the row cells always sum to the `Total` column.

`SKILL.md` now opens with the script call and an instruction not to recount by hand, then a
field table for the JSON, a Tests section, and four gotchas.

## Tests kept in the skill

You asked to keep the fixtures and the manifest so you can re-run the checks. They are in
`tests/`:

```
tests/manifest.json          two cases, each fixture + expected file + expected exit code
tests/run_tests.py           runs every case, prints PASS/FAIL, exits 1 on any failure
tests/fixtures/clean/        v1.0.0.md, v2.0.0.md - valid headings, no Misc, no unknown categories
tests/fixtures/messy/        v1.1.0.md (Misc entry), v1.2.0.md (missing heading, Deprecated category)
tests/expected/clean.json    expected script output
tests/expected/messy.json    expected script output
```

Re-run them with:

```bash
python3 tests/run_tests.py
```

Current result:

```
PASS clean
PASS messy
2 case(s), 0 failure(s)
```

The `messy` fixture deliberately covers all three failure modes at once: a version recovered
from a filename, a `Misc` entry surfaced for judgment, and an unknown category counted in the
`Other` column. Regenerate an expected file only when a script output change is intended:

```bash
python3 scripts/check_changelogs.py tests/fixtures/clean > tests/expected/clean.json
```

## Checker output on your real changelogs

The script found one structural problem in `changelogs/`: `v1.2.0.md` has no version heading -
its first line is `### Added`. `v1.0.0.md` and `v1.1.0.md` are fine. No categories outside the
allowed list. One `Misc` entry to judge: "Corrected typo in settings page label" in `v1.1.0.md`,
which reads as a `Fixed`.

| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 | (missing) | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |

## Files

```
changelog-checker/
  SKILL.md                        rewritten: 1 script call + 5 judgment steps
  scripts/check_changelogs.py     new
  tests/manifest.json             new
  tests/run_tests.py              new
  tests/fixtures/clean/*.md       new (2 files)
  tests/fixtures/messy/*.md       new (2 files)
  tests/expected/*.json           new (2 files)
  changelogs/*.md                 untouched
```
