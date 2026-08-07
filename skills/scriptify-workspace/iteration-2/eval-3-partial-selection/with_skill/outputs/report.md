# Delegation review report — changelog-checker

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-3-partial-selection/with_skill/workspace/changelog-checker`

Eligibility: writable, user-owned, outside every plugin cache path. `git status` shows the
target SKILL.md as untracked (the whole workspace folder is new), not as a modified tracked
file, so no uncommitted-change warning applied. Restore point saved to
`scratch/.delegation-review/SKILL.md.orig`.

Inventory: 7 numbered steps, 0 existing scripts, 0 references, ~242 body tokens.

## Rendered report (verbatim from `render_report.py`)

## Delegation review: changelog-checker

**Verdict:** 7 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~210 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob plus version sort plus count; a function of the folder contents, identical every run | `python3 scripts/list_changelogs.py changelogs/ --json` -> {"count": N, "files": [{"path", "version"}]} version-sorted ascending, exit 0 files found / 1 no .md files found / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex check against `## vX.Y.Z — YYYY-MM-DD`; same verdict on the same files every run | `python3 scripts/check_headings.py changelogs/ --json` -> {"findings": [{"path", "reason"}]}, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tally and totals; pure aggregation with one correct answer | `python3 scripts/count_entries.py changelogs/ --json` -> {"per_file": [{"path", "version", "date", "counts": {...}}], "totals": {...}}, exit 0 counted / 1 no entries found / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | HYBRID | the narrative itself is prose that should vary with the release; only the source material it draws on is mechanical | `python3 scripts/extract_entries.py changelogs/ --json` -> {"entries": [{"path", "version", "date", "category", "text"}]}, exit 0 entries found / 1 none found / 2 usage |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table from the counts, sorted by version descending; rendering from structured data | `python3 scripts/render_summary.py changelogs/ ` -> markdown table of version, date, per-category counts, version-descending, exit 0 rendered / 1 nothing to render / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is mechanical, but whether a Misc entry belongs under another category is contextual classification Claude must re-triage | `python3 scripts/check_tags.py changelogs/ --json` -> {"invalid": [{"path", "category"}], "misc": [{"path", "text"}]}, exit 0 clean / 1 invalid tags or misc entries present / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | "a reader would find this confusing" is judgment that reasonable runs disagree on; enumerating the entries to judge is not | `python3 scripts/extract_entries.py changelogs/ --json` -> {"entries": [{"path", "version", "date", "category", "text"}]}, exit 0 entries found / 1 none found / 2 usage |

## Reasoning per step

- **s1 SCRIPT.** Glob, version sort, count. Two runs should never differ; the unit test is
  writable today (given these files, this ordering and this count). Version sort is also a
  place prose reliably goes wrong — v1.10.0 sorts before v1.2.0 lexicographically.
- **s2 SCRIPT.** A fixed regex against `## vX.Y.Z — YYYY-MM-DD`. Fixed-rule validation with
  one correct verdict per file. Nothing about it varies with context.
- **s3 SCRIPT.** Per-category tallies plus cross-file totals. Pure aggregation.
- **s4 HYBRID, not CLAUDE.** The paragraph itself must vary with the release, so the writing
  stays with Claude. The material it draws on — every entry, its version, date and category —
  is mechanical, so a script gathers it and Claude writes from structured input.
- **s5 SCRIPT.** Render a fixed markdown table from structured counts, sorted descending.
  Report rendering from structured data is the textbook SCRIPT category.
- **s6 HYBRID.** Two halves. Checking each tag against a closed allowed list is mechanical.
  Deciding whether a `Misc` entry really belongs under `Fixed` is contextual classification
  where reasonable runs disagree. The script emits `invalid` and `misc`; Claude re-triages
  only the `misc` residue.
- **s7 HYBRID.** "A reader would find this confusing" is judgment. Enumerating the entries to
  be judged is not, so it shares `extract_entries.py` with s4 (same inventory ids kept, one
  shared `proposed_script.name`).
- No DEAD steps, no ALREADY_DELEGATED steps (the target ships no scripts).

## What was applied

Per the user's explicit instruction, only s1 and s3 were applied. s2, s4, s5, s6 and s7 keep
their prose byte-for-byte; their proposed scripts were not written.

Scripts written into the target:

| Script | Step | Interface |
|---|---|---|
| `scripts/list_changelogs.py` | s1 | `python3 scripts/list_changelogs.py changelogs/ --json` — exit 0 found / 1 none / 2 usage |
| `scripts/count_entries.py` | s3 | `python3 scripts/count_entries.py changelogs/ --json` — exit 0 counted / 1 no entries / 2 usage |

Smoke test (run before the SKILL.md rewrite): `12/12 checks passed`, exit 0.

SKILL.md diff (only lines 12 and 14 changed):

```diff
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
+1. Run exactly: `python3 scripts/list_changelogs.py changelogs/ --json`
+   `files` is version-sorted ascending; `count` is the total. Exit 0 files found, 1 none found, 2 usage error.
 2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+3. Run exactly: `python3 scripts/count_entries.py changelogs/ --json`
+   `per_file[].counts` holds each file's per-category tally, `totals` the cross-file totals. Exit 0 counted, 1 no entries, 2 usage error.
```

## Follow-ups

- s2, s5 (SCRIPT) and s4, s6, s7 (HYBRID) remain undelegated by the user's choice. They are
  the obvious next batch if the user wants the rest.
- No DEAD steps to route to a `skillit:review` follow-up. Running `skillit:review` on the
  target is still the recommended final check.
