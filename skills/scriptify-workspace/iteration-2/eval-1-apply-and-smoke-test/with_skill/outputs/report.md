# Delegation review report — changelog-checker

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-1-apply-and-smoke-test/with_skill/workspace/changelog-checker`
Eligibility: writable, user-owned, outside every plugin cache path. Untracked in git (whole workspace folder is new), so no uncommitted-change warning applied. Restore point saved to `.delegation-review/SKILL.md.orig` before any write.

Inventory: 7 steps, 0 existing scripts, 0 references, ~242 tokens of body. Origin of every anchor: `numbered-list`.

## Rendered report (verbatim from `render_report.py`)

## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob, version sort, and count are a pure function of the folder; two runs must not differ | `python3 scripts/scan_changelogs.py changelogs/ --json` -> JSON: files sorted by version, file_count, per-file per-category counts, totals, entry texts, exit 0 scanned / 1 no changelog files found / 2 usage or unreadable dir |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex check of the version header on every file; unit-testable, same answer every run | `python3 scripts/check_headings.py changelogs/ --json` -> JSON findings list; each finding names the file and missing_version_header, exit 0 clean / 1 findings / 2 usage or unreadable dir |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tallies and cross-file totals are arithmetic; same script output as s1 | `python3 scripts/scan_changelogs.py changelogs/ --json` -> JSON: per-file counts under files[].counts and cross-file totals under totals, exit 0 scanned / 1 no changelog files found / 2 usage or unreadable dir |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative is prose aimed at a non-technical reader; reasonable runs should word the overall direction differently, and a script would encode one arbitrary phrasing. Mechanical shell already stripped: scan_changelogs.py supplies the source material and render_summary.py renders the table, leaving only the writing | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | sorting rows and filling a fixed markdown table from structured data; never hand-typed | `python3 scripts/render_summary.py changelogs/` -> markdown table of version, date, per-category counts, sorted by version descending, plus a totals row, exit 0 rendered / 1 no changelog files found / 2 usage or unreadable dir |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | membership of a tag in the allowed list is mechanical; whether a Misc entry actually belongs under Fixed is contextual re-triage a script would fake | `python3 scripts/check_tags.py changelogs/ --json` -> JSON: invalid (tags outside the allowed list) and misc (every Misc entry, with file and text) for Claude to re-triage, exit 0 no invalid tags / 1 invalid tags found / 2 usage or unreadable dir |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | enumerating every entry is mechanical; judging whether a reader would find the wording confusing varies with context and stays with Claude | `python3 scripts/scan_changelogs.py changelogs/ --json` -> every entry text under files[].entries, so Claude judges clarity over an enumerated list instead of re-reading the files, exit 0 scanned / 1 no changelog files found / 2 usage or unreadable dir |

## Reasoning per step

**s1 — "List every `.md` file in `changelogs/`, sorted by version, and note the total count." → SCRIPT**
Glob, version sort, count. Pure function of the folder contents; the unit test writes itself. Nothing here varies with context, so two runs must not differ. Delegated to `scan_changelogs.py`, which also carries s3 and s7's data.

**s2 — "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." → SCRIPT**
Textbook fixed-rule validation (rubric: "every heading matches the version pattern"). Regex over the first non-empty line, same answer every run. Delegated to `check_headings.py`, exit 1 on findings so the caller branches on the exit code.

**s3 — "Count the entries in each file per category and total them across files." → SCRIPT**
Aggregation and counting. Arithmetic, no judgment. Deliberately given the same `proposed_script.name` as s1 (`scan_changelogs.py`): one parse of the folder answers both, and the SKILL.md wording tells step 3 to read step 1's output rather than re-scan.

**s4 — "Write a one-paragraph release narrative … for a non-technical reader." → CLAUDE**
The only step where reasonable runs should differ, and should. The named judgment: choosing what the release is *about* and how to phrase it for a non-technical audience. A script would encode one arbitrary phrasing and present it with false authority. HYBRID decomposition was tried and the mechanical shell is already gone: `scan_changelogs.py` supplies the source entries and `render_summary.py` renders the table, leaving nothing but the writing. This matches the rubric's own canonical CLAUDE example.

**s5 — "Render a summary table … sorted by version descending." → SCRIPT**
Report rendering from structured data: sort rows, fill a fixed markdown template. Rubric names this outright. Delegated to `render_summary.py` so the table is never hand-typed (and never silently mis-sorted).

**s6 — "Check every entry's category tag against the allowed list …; for entries tagged `Misc`, judge whether they actually fit one of the other categories." → HYBRID**
Two halves with a clean seam. Set membership against a fixed allow-list is mechanical → script, exit 1 on an invalid tag. Whether "Corrected typo in settings page label" really belongs under `Fixed` is contextual re-triage a script would fake. `check_tags.py` enumerates every `Misc` entry with its file and text; Claude decides. Classic extract-then-judge.

**s7 — "Verify the entries are clearly written and flag any that a reader would find confusing." → HYBRID**
Not CLAUDE: the enumeration half is mechanical. `scan_changelogs.py` already emits every entry under `files[].entries`, so Claude judges clarity over a structured list instead of re-reading three files. Judging "confusing to a reader" is context-dependent and stays with Claude. Tie-break applied: in doubt between HYBRID and CLAUDE → HYBRID.

No DEAD steps. No ALREADY_DELEGATED steps (the target shipped no scripts).

## Applied

All 6 SCRIPT/HYBRID rows applied. Four scripts written into `workspace/changelog-checker/scripts/`, plus the shared parser `_changelog.py` they import (no CLI, not a step script):

| Script | Steps | Interface |
|---|---|---|
| `scan_changelogs.py` | s1, s3, s7 | `python3 scripts/scan_changelogs.py changelogs/ --json` |
| `check_headings.py` | s2 | `python3 scripts/check_headings.py changelogs/ --json` |
| `render_summary.py` | s5 | `python3 scripts/render_summary.py changelogs/` |
| `check_tags.py` | s6 | `python3 scripts/check_tags.py changelogs/ --json` |

Smoke test: **24/24 checks passed, exit 0** (`smoke_test.py .delegation-review/manifest.json`). Green on the first run; no expectation was changed.

Follow-up: run `skillit:review` on the target as the final check.
