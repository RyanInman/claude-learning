# Transcript notes — eval 7, without_skill

Skill folder under work (called SKILL below):
`/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-7-keep-residue/without_skill/workspace/changelog-checker`

No skill from the skill list was invoked; this is the without_skill arm. Nothing
under `/Users/admin/claude-learning/skills/scriptify/` was read or written.

## 1. Survey

- Ran `find` over the run dir → 4 files: `eval_metadata.json`,
  `workspace/changelog-checker/SKILL.md`, three files in `changelogs/`.
- Read `eval_metadata.json`, `SKILL.md`, and all three changelog files
  (`v1.0.0.md`, `v1.1.0.md`, `v1.2.0.md`) via one `cat` batch.
- Observed in the source data: `v1.2.0.md` has no `## vX.Y.Z — YYYY-MM-DD`
  header, and `v1.1.0.md` carries a `### Misc` section. Both shaped the fixtures.

## 2. Classification

Read the 7 workflow steps in SKILL.md and classified each (full reasoning in
report.md): 1, 2, 3, 5 → script; 6 → hybrid; 4, 7 → prose.

## 3. Manifest format

- Ran `find /Users/admin/claude-learning/skills/scriptify-workspace -name "manifest*.json"`
  to learn the manifest schema an existing smoke runner consumes.
- Read `iteration-1/eval-7-keep-residue/with_skill/workspace/changelog-checker/scripts/tests/manifest.json`
  (inside scriptify-workspace, not inside the off-limits scriptify skill) and
  matched its schema: `target_skill`, `scripts[].path`, `invocations[]` with
  `argv` / `expect_exit` / `expect_stdout_json` / `expect_stdout_contains`, plus
  `bad_data_invocation` and `bad_invocation`.
- Decision: reuse that exact schema so the manifest is runnable by an external
  smoke runner as well as by the runner shipped in the skill.

## 4. Scripts written (all via Write)

- `SKILL/scripts/changelog_lib.py` — shared parser: `HEADER_RE`, `SECTION_RE`,
  `ENTRY_RE`, semver `version_key`, `require_dir` (exit 2 on usage error),
  `parse_dir`. Written once so five scripts share one parse, rather than five
  copies of the same regexes.
- `SKILL/scripts/list_changelogs.py` — step 1. `DIR [--json]` → `count`,
  `versions`, `files`. Exit 1 on an empty folder.
- `SKILL/scripts/check_headings.py` — step 2. → `findings` with
  `missing_version_header` and `version_mismatch`. Exit 1 on any finding.
- `SKILL/scripts/count_entries.py` — step 3. → `per_file`, `totals`,
  `total_entries`. Exit 1 when nothing counted.
- `SKILL/scripts/render_table.py` — step 5. Markdown table, version descending,
  columns Version/Date/Added/Fixed/Changed/Removed/Misc/Total. Exit 1 if any row
  is `unknown`.
- `SKILL/scripts/check_tags.py` — step 6 mechanical half. → `invalid` + `misc`.
  Exit 1 if either is non-empty.

Uniform exit contract chosen: 0 clean, 1 findings/empty, 2 usage error.

## 5. Fixtures

Written by one bash heredoc batch, directly into their final home
`SKILL/scripts/tests/fixtures/<script>/changelogs-{good,bad,empty,misc}/`.
Deliberate choice: no `.delegation-review/` or scratch staging directory was used
at any point, so no fixture path ever pointed anywhere but its final location and
no path rewrite was necessary.

Fixture set (17 files):
- `list_changelogs/changelogs-good` — v1.0.0, v1.9.0, v1.10.0 (pins semver sort)
- `list_changelogs/changelogs-empty` — `notes.txt` only
- `check_headings/changelogs-good` — two valid headers
- `check_headings/changelogs-bad` — one file with no header, one whose header
  version (v1.4.0) disagrees with its filename (v1.3.0)
- `count_entries/changelogs-good` — 5 entries across 2 files
- `count_entries/changelogs-empty` — header, no entries
- `render_table/changelogs-good` — 2 files with dates
- `render_table/changelogs-bad` — headerless file → `unknown` row
- `check_tags/changelogs-good` — Added + Removed
- `check_tags/changelogs-misc` — one `Misc` entry
- `check_tags/changelogs-bad` — a `Security` section (tag outside the list)

## 6. Observed behaviour before pinning expectations

First attempt to exercise the scripts failed on shell quoting (the whole
`script + args` string was passed as one argv element; python reported
`can't open file '...list_changelogs.py /...changelogs-good --json'`, exit 2).
Fixed by using a `run(){ python3 "$@"; }` helper with proper word splitting, then
re-ran all 11 invocations plus 2 no-arg usage cases from `cwd=SKILL`.

Recorded actual results, then wrote the manifest to match them (expectations were
copied from observed output, not guessed):
- list_changelogs good → exit 0, `"count": 3`, versions `1.0.0, 1.9.0, 1.10.0`
- list_changelogs empty → exit 1, `"count": 0`
- check_headings good → exit 0, `"findings": []`
- check_headings bad → exit 1, `missing_version_header` + `version_mismatch`
- count_entries good → exit 0, `"total_entries": 5`, `"Added": 3`
- count_entries empty → exit 1, `"total_entries": 0`
- render_table good → exit 0, rows `1.1.0` then `1.0.0`
- render_table bad → exit 1, `unknown | unknown` row
- check_tags good → exit 0, `"invalid": []`
- check_tags misc → exit 1, lists the typo entry
- check_tags bad → exit 1, `"tag": "Security"`
- both no-arg cases → exit 2 usage error

## 7. Manifest and runner

- Wrote `SKILL/scripts/tests/manifest.json`: 5 script entries, 18 cases total,
  every fixture path absolute under `SKILL/scripts/tests/fixtures/`.
- Wrote `SKILL/scripts/tests/run_smoke.py`: reads the manifest, runs each argv
  with `cwd = manifest.target_skill`, asserts `expect_exit` /
  `expect_exit_nonzero` / `expect_stdout_json` / `expect_stdout_contains`, and
  additionally asserts every absolute path appearing in any argv exists on disk
  (this is the guard against a stale fixture path).

## 8. Smoke run

```
cd SKILL && python3 scripts/tests/run_smoke.py
```
Output: `ran 18 cases from .../scripts/tests/manifest.json` / `all green`, exit 0.

## 9. SKILL.md rewrite

Rewrote `SKILL/SKILL.md` (Write, full replace). Frontmatter `name`/`description`
unchanged. Body now:
- states the exit-code contract once, up front;
- steps 1, 2, 3, 5, 6 each open with the exact `python3 scripts/<name>.py DIR`
  command and say what to do with the output;
- step 4 and step 7 are marked "prose, no script" with instructions on what to
  judge — no script is offered for either;
- step 5 says to paste the script's stdout unedited;
- step 6 splits explicitly: report `invalid` as-is, judge each `misc` entry;
- a closing "Re-running the checks" section carries the smoke-test command
  `python3 scripts/tests/run_smoke.py` and points at
  `scripts/tests/manifest.json`.

## 10. End-to-end and cleanup

- Ran all five scripts against the real `changelogs/` folder. Results:
  check_headings exit 1 (`v1.2.0.md` missing header); count_entries 8 entries
  (Added 4, Fixed 2, Changed 1, Misc 1); render_table exit 1 with one `unknown`
  row; check_tags exit 1 with one `Misc` entry, no invalid tags. All matched
  expectations from reading the source files.
- `grep -rl "delegation-review" SKILL` → no matches.
- Removed `SKILL/scripts/__pycache__/` created by the test runs.
- Final skill contents verified with `find`: SKILL.md, 6 scripts, run_smoke.py,
  manifest.json, 17 fixture files, 3 original changelogs. No stray files.

## Files read
- `.../without_skill/eval_metadata.json`
- `.../without_skill/workspace/changelog-checker/SKILL.md` (original)
- `.../without_skill/workspace/changelog-checker/changelogs/v1.0.0.md`, `v1.1.0.md`, `v1.2.0.md`
- `.../iteration-1/eval-7-keep-residue/with_skill/workspace/changelog-checker/scripts/tests/manifest.json` (schema reference only)

## Files written
- `SKILL/SKILL.md` (rewritten)
- `SKILL/scripts/changelog_lib.py`, `list_changelogs.py`, `check_headings.py`,
  `count_entries.py`, `render_table.py`, `check_tags.py`
- `SKILL/scripts/tests/manifest.json`, `SKILL/scripts/tests/run_smoke.py`
- 17 fixture files under `SKILL/scripts/tests/fixtures/`
- `outputs/report.md`, `outputs/gate.md`, `outputs/transcript-notes.md`

`scratch/` was created but not needed; no transient working files were produced.
