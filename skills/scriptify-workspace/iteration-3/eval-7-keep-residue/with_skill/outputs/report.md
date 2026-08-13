## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | listing and version-sorting the files and counting them is a pure function of the directory | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` -> compact summary line per file; full scan JSON to --out (files sorted by version, per-category counts, totals, entry texts), exit 0 scan written / 1 no changelog files found / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex check of the first heading against `## vX.Y.Z — YYYY-MM-DD`; two runs must not differ | `python3 scripts/check_changelogs.py changelogs/ --json` -> findings JSON: bad_heading, missing_heading, invalid_tag, misc, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tallies and totals are arithmetic over parsed entries | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` -> compact summary; counts per category and totals inside the scan JSON, exit 0 scan written / 1 no changelog files found / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the release narrative is prose written for a non-technical reader; two reasonable runs should word the same releases differently, and a script would encode one arbitrary wording | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table rendered from the scan JSON, sorted by version descending | `python3 scripts/render_summary.py scan.json` -> markdown summary table, exit 0 rendered / 1 scan JSON malformed / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | checking tags against the allowed list is mechanical; deciding which category a Misc entry belongs to reads the entry's intent | `python3 scripts/check_changelogs.py changelogs/ --json` -> invalid tags under `invalid_tag`, Misc entries under `misc` for Claude to re-triage, exit 0 clean / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | extracting every entry is mechanical; judging whether a reader finds it confusing is the judgment no script can fake | `python3 scripts/scan_changelogs.py changelogs/ --json` -> every entry with file, category, and text, so the clarity judgment reads the scan instead of the files, exit 0 scan written / 1 no changelog files found / 2 usage |
**What the target's own data already produces** (run against `changelogs/` before any rewrite):

- `v1.2.0.md` trips `no_version_heading` — it opens with `### Added`, so it has no `## vX.Y.Z — YYYY-MM-DD` heading at all. It is the file step 2 exists to catch, and the reason the summary table shows its date as `—`.
- `v1.1.0.md` carries one `Misc` entry, "Corrected typo in settings page label", which is the step 6 judgment call: it reads as `Fixed`.
- Scan totals: 3 files, 8 entries — Added 4, Fixed 2, Changed 1, Removed 0, Misc 1.

## Applied: all 6 SCRIPT/HYBRID rows, residue kept

**Scripts written into `changelog-checker/scripts/`**

| Script | Covers | Contract |
|---|---|---|
| `scan_changelogs.py` | s1, s3, s7 | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` — files sorted by version, per-category counts, totals, every entry text. Exit 0 scan written / 1 `no_changelog_files` / 2 usage |
| `check_changelogs.py` | s2, s6 | `python3 scripts/check_changelogs.py changelogs/ --json` — `violations` (`no_version_heading`, `version_heading_not_first`, `malformed_version_heading`, `invalid_tag`) plus `misc` entries for you to re-triage. Exit 0 clean / 1 findings / 2 usage |
| `render_summary.py` | s5 | `python3 scripts/render_summary.py scan.json` — markdown table sorted by version descending, with an all-versions total row. Exit 0 rendered / 1 `invalid_scan` / 2 usage |

Steps 4 (the release narrative) and 7's judgment half stay prose: the narrative is written for a non-technical reader and should read differently on different runs, and clarity is a reader's call. Step 7 now reads `entries` out of `scan.json` instead of reopening the files. No step was DEAD, so nothing is queued for a `skillit:review` follow-up.

**SKILL.md diff**

```diff
--- SKILL.md.orig
+++ SKILL.md
@@ -9,10 +9,18 @@
 
 ## Workflow
 
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
-2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out scan.json`
+   Exit 0 the scan is written and stdout carries the file count, the entry total, and one line per file, sorted by version; exit 1 the folder holds no `.md` files, so say so and stop; exit 2 usage error.
+2. Run exactly: `python3 scripts/check_changelogs.py changelogs/ --json`
+   Exit 0 clean, 1 findings, 2 usage error. Heading problems arrive under `violations` with codes `no_version_heading`, `version_heading_not_first`, and `malformed_version_heading`. Report every file named there. Keep this JSON; step 6 reads it too.
+3. Per-category counts come from `scan.json`: `counts` per file, `totals` across files.
 4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
-5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
-6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
-7. Verify the entries are clearly written and flag any that a reader would find confusing.
+5. Run exactly: `python3 scripts/render_summary.py scan.json`
+   Exit 0 the markdown table is on stdout, sorted by version descending; exit 1 `invalid_scan`, so re-run step 1.
+6. Read the step 2 findings. Entries under a category outside the allowed list arrive as `invalid_tag`. For each entry under `misc`, judge whether it actually fits `Added`, `Fixed`, `Changed`, or `Removed`, and suggest the move.
+7. Read `entries` in `scan.json` and flag any entry a reader would find confusing.
+
+## Verifying the scripts
+
+Run exactly: `python3 scripts/tests/smoke_test.py scripts/tests/manifest.json`
+Exit 0 every script still meets its contract, 1 a check failed, 2 the manifest is missing or malformed.
```

**Smoke test:** `21/21 checks passed` (exit 0). Every finding code has its own fixture file and its own asserted string: `no_version_heading` (`no-heading.md`), `version_heading_not_first` (`not-first.md`), `malformed_version_heading` (`malformed.md`), `invalid_tag` and the `Misc` triage list (`badtag.md`), `no_changelog_files` (a folder with no `.md`), `invalid_scan` (a scan JSON with no `files` list).

**Residue kept, as you asked.** `keep_residue.py` installed the fixtures, the manifest, and a vendored `smoke_test.py` under `changelog-checker/scripts/tests/`, rewrote 10 fixture paths to the relocatable `{skill}` form, and re-ran the suite twice: `in place: 21/21 checks passed` and `from a relocated copy: 21/21 checks passed`. The second run is the one that matters — it proves the checks still pass after the skill is moved somewhere else, which a stale absolute path would break silently.

Re-run the checks yourself any time from the skill folder:

    python3 scripts/tests/smoke_test.py scripts/tests/manifest.json

**Suggested follow-up:** run `skillit:review` on `changelog-checker` as a final check.
