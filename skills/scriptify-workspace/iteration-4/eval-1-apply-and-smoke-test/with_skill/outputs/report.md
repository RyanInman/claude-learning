# scriptify run on `changelog-checker`

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-1-apply-and-smoke-test/with_skill/workspace/changelog-checker`
Eligible to write: yes (user-owned, writable, outside every plugin cache). `git status` shows the
file untracked rather than dirty, so there was no uncommitted change to warn about.

## Delegation review: changelog-checker

**Verdict:** 4 of 7 steps become pure script invocations, plus 1 HYBRID step(s) that keep their judgment prose. Replacing the 4 SCRIPT step(s) removes ~105 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | globbing changelogs/, sorting by semver, and counting files is a pure function of the directory; two runs must not differ | `python3 scripts/scan_changelogs.py changelogs/ [--json]` -> version-sorted summary table (versions, dates, per-category counts, totals) plus a header-violation list; --json emits the same data structured, exit 0 clean / 1 structural findings / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | a fixed regex check for '## vX.Y.Z - YYYY-MM-DD' on line 1; the target's own v1.2.0.md already fails it, so the finding is testable | `python3 scripts/scan_changelogs.py changelogs/ [--json]` -> version-sorted summary table (versions, dates, per-category counts, totals) plus a header-violation list; --json emits the same data structured, exit 0 clean / 1 structural findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | counting '- ' bullets under each '### Category' heading and totalling them is mechanical aggregation | `python3 scripts/scan_changelogs.py changelogs/ [--json]` -> version-sorted summary table (versions, dates, per-category counts, totals) plus a header-violation list; --json emits the same data structured, exit 0 clean / 1 structural findings / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the whole output is a narrative written for a non-technical reader; reasonable runs should word the direction of a release differently, and a script would only re-gather entries Claude must read anyway | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | a fixed markdown table rendered from the counts s1-s3 already produce, sorted descending by version; hand-rendering it costs tokens and risks arithmetic drift | `python3 scripts/scan_changelogs.py changelogs/ [--json]` -> version-sorted summary table (versions, dates, per-category counts, totals) plus a header-violation list; --json emits the same data structured, exit 0 clean / 1 structural findings / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is a fixed set membership test the script decides outright; only the residue - does this Misc entry really belong under Fixed? - needs Claude, and the script hands it the exact entry text to judge | `python3 scripts/check_categories.py changelogs/ --json` -> JSON: entries whose category tag is outside the allowed list, plus every Misc entry with its file and text for re-triage, exit 0 clean / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | CLAUDE | clarity is a reader judgment with no checkable rule, and a script listing the entries buys nothing because Claude must read all of them regardless | - |

## What the target's own data already produces

I ran both scripts against `changelogs/` before reporting, so these are real findings, not fixtures:

- `v1.2.0.md` opens with `### Added`. It carries no `## vX.Y.Z — YYYY-MM-DD` heading anywhere, so
  step 1 reports it twice, under `first_line_not_version_heading` and under `version_heading_missing`.
  Its version falls back to the filename and its date column reads `(none)`.
- `v1.1.0.md` tags "Corrected typo in settings page label" as `Misc`. Step 3 hands that entry back
  under `misc` for re-triage; it reads as a `Fixed`.
- Totals across the 3 files: Added 4, Fixed 2, Changed 1, Removed 0, Other 1, total 8 entries.

## Scripts written

Both live in `changelog-checker/scripts/`, both stdlib-only, argv-only, with `--help`, `--json`,
`--out`, and the house exit contract (0 clean / 1 findings / 2 usage or unreadable input).

| Script | Replaces | Finding codes |
|---|---|---|
| `scan_changelogs.py` | s1, s2, s3, s5 | `no_changelog_files`, `first_line_not_version_heading`, `version_heading_missing`, `malformed_version_heading` |
| `check_categories.py` | s6 (mechanical half) | `unknown_category`, `misc_needs_triage` |

`first_line_not_version_heading` and `version_heading_missing` stay separate codes because a file can
carry a correct heading on line 3 — that is a placement problem, not a missing heading, and one code
for both would publish the wrong label.

## Smoke test

    python3 <scriptify>/scripts/smoke_test.py .delegation-review/manifest.json

    17/17 checks passed

Nine checks for `scan_changelogs.py` and eight for `check_categories.py`: `exists`, `help`, one
fixture run per finding code, `bad-data`, `bad-args`, and `codes-distinct`. Every finding code has
its own fixture and its own asserted string, including a fixture whose version heading sits on line 3
rather than line 1, which is what separates the two heading codes.

## SKILL.md diff

```diff
--- scratch/.delegation-review/SKILL.md.orig	2026-08-12 11:31:17
+++ workspace/changelog-checker/SKILL.md	2026-08-12 11:35:31
@@ -9,10 +9,21 @@
 
 ## Workflow
 
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
-2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
-4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
-5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
-6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
-7. Verify the entries are clearly written and flag any that a reader would find confusing.
+1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/`
+   It lists every `.md` file sorted by version with the total count, checks each
+   file's `## vX.Y.Z — YYYY-MM-DD` heading, counts entries per category, and
+   prints the summary table of versions, dates, and per-category counts sorted
+   by version descending. Add `--json` for the same data structured, and
+   `--out FILE` when the table runs long.
+   Exit 0 clean, 1 findings, 2 usage error or missing folder.
+   Exit 1 → report every finding under its code: `no_changelog_files`,
+   `first_line_not_version_heading`, `version_heading_missing`,
+   `malformed_version_heading`.
+2. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
+3. Run exactly: `python3 scripts/check_categories.py changelogs/ --json`
+   Entries tagged outside the allowed list (`Added`, `Fixed`, `Changed`,
+   `Removed`, `Misc`) come back under `invalid` with code `unknown_category`.
+   For each entry under `misc`, judge whether it actually fits one of the other
+   categories and suggest the move.
+   Exit 0 clean, 1 findings, 2 usage error or missing folder.
+4. Verify the entries are clearly written and flag any that a reader would find confusing.
```

Seven steps became four. Steps 1, 2, 3, and 5 collapse into one invocation. Step 6 keeps its judgment
sentence and loses the allowed-list check the script now decides. Steps 4 and 7 are unchanged
verbatim.

## Left as CLAUDE

- **s4, the release narrative.** Its whole output is prose a person reads, and reasonable runs should
  word it differently. A script would only re-gather entries Claude reads anyway.
- **s7, entry clarity.** Clarity has no checkable rule, and listing the entries changes no decision
  because Claude must read all of them regardless.

No DEAD steps, so there is nothing to route to a `skillit:review` follow-up.

## Next

Run `skillit:review` on `changelog-checker` as a final check.
