# Scriptify review: `changelog-checker`

I reviewed all 7 workflow steps, split them into deterministic work and judgment
work, wrote the scripts, smoke-tested them, and rewrote `SKILL.md`. The fixtures
and the manifest stay inside the skill so you can re-run the checks yourself.

## Step classification

| # | Original step | Verdict | Where it went |
|---|---|---|---|
| 1 | List every `.md` file sorted by version, note the count | script | `check_changelogs.py` → `file_count`, `files_sorted` |
| 2 | Check the `## vX.Y.Z — YYYY-MM-DD` heading | script | `check_changelogs.py` → `heading_violations` |
| 3 | Count entries per category and total them | script | `check_changelogs.py` → `files[].counts`, `totals`, `grand_total` |
| 4 | Write a release narrative for a non-technical reader | **prose** | stays with the model — no script |
| 5 | Render the summary table, version descending | script | `check_changelogs.py` → `table_markdown` |
| 6 | Validate category tags; judge whether `Misc` entries fit elsewhere | **split** | tag validation → script (`unknown_tags`, `misc_entries`); the re-categorization judgment stays prose |
| 7 | Flag entries a reader would find confusing | **prose** | stays with the model — no script |

Steps 4 and 7 are judgment about meaning and readability. No parser decides
whether a sentence is confusing or what a release means to a non-technical
reader, so scripting them would only produce a rule that is wrong in new cases.

Step 6 is the only mixed one. Whether a heading is on the allowed list is a set
membership test; whether "Corrected typo in settings page label" is really a
`Fixed` is a judgment. The script does the first half and hands you the list.

Steps 1, 2, 3, 5 and 6a all read the same files, so they are one script and one
pass, not five scripts.

## What I wrote

```
scripts/check_changelogs.py      deterministic scan, prints one JSON report
scripts/tests/run_tests.py       smoke-test runner
scripts/tests/manifest.json      fixture paths + expected values
scripts/tests/fixtures/sample/   v1.0.0, v1.1.0, v1.2.0 (v1.2.0 has no heading)
scripts/tests/fixtures/edge/     v2.0.0 with an unknown `Security` tag
```

`check_changelogs.py <changelogs_dir>` prints JSON and exits 0; it exits 2 on
bad usage or an unreadable directory.

## Smoke test

Run from the skill folder:

```bash
python3 scripts/tests/run_tests.py
```

Current result:

```
ran case sample on .../scripts/tests/fixtures/sample
ran case edge on .../scripts/tests/fixtures/edge
PASS 2 cases
```

Exit code 0. The runner first confirms every fixture path recorded in
`manifest.json` resolves on disk, then runs the checker against each fixture
directory and compares `file_count`, `files_sorted`, `heading_violations`,
`totals`, `grand_total`, `unknown_tags`, `misc_entries`, and the first data row
of the table (which locks the descending sort).

The `sample` fixtures are copies of your real `changelogs/`, so the expected
values encode the real findings: 3 files, 8 counted entries, `v1.2.0.md`
missing its heading, one `Misc` entry.

## Live run against `changelogs/`

```
| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 | missing | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |
```

- Heading violation: `v1.2.0.md` starts with `### Added`. It has no version
  heading and therefore no date.
- `Misc` entry to re-categorize: "Corrected typo in settings page label" in
  `v1.1.0.md` is a `Fixed`.
- No unknown category tags.

## Two things to know

- `manifest.json` stores absolute paths. Move or rename the skill folder and
  the smoke test fails until you regenerate it.
- Entries under an unrecognized heading are listed in `unknown_tags` but left
  out of the counts, so `grand_total` can be below the raw bullet count.
