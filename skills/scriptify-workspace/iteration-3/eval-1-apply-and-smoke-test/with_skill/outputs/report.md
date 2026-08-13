## Delegation review: changelog-checker

**Verdict:** 5 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~159 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob plus semver sort plus a count; identical output every run | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> compact summary: file count, header failures, category totals, unknown/Misc tag count, exit 0 no structural findings / 1 findings / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | one fixed regex on line 1 of each file; v1.2.0.md already fails it | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> compact summary: file count, header failures, category totals, unknown/Misc tag count, exit 0 no structural findings / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | counting bullets under each category heading and summing them is arithmetic | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> compact summary: file count, header failures, category totals, unknown/Misc tag count, exit 0 no structural findings / 1 findings / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative's whole output is prose a non-technical reader judges; two runs should word it differently | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table from the scan data, sorted by version descending | `python3 scripts/render_summary.py .changelog-scan.json` -> markdown summary table, versions descending, exit 0 rendered / 2 usage or unreadable scan file |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | matching tags against the allowed list is mechanical; deciding whether a Misc entry belongs under Fixed is judgment | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> compact summary: file count, header failures, category totals, unknown/Misc tag count, exit 0 no structural findings / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | CLAUDE | "a reader would find this confusing" varies with the reader and the entry; reasonable runs should disagree | - |

### What the target's own data already proves

`sample_target_data.py` named `changelogs/v1.2.0.md` a first-line outlier, and reading it
confirms the defect step 2 exists to catch: the file opens with `### Added`, so it carries no
`## vX.Y.Z — YYYY-MM-DD` header at all. `changelogs/v1.1.0.md` carries the second planted case —
a `Misc` entry, "Corrected typo in settings page label", which is the judgment residue step 6
hands to Claude. Both drove the contract: `header_not_first` is a separate finding code from
`header_malformed`, because v1.2.0.md has no header rather than a broken one, and a single
`missing_header` code would have mislabeled a file whose header is merely mistyped.

### Applied: 5 rows (s1, s2, s3, s5, s6), residue not kept

**Scripts written into `changelog-checker/scripts/`**

- `scan_changelogs.py` — one pass over `changelogs/*.md`: file list sorted by version, header
  validation, per-category entry counts and cross-file totals, category tags checked against
  `Added`/`Fixed`/`Changed`/`Removed`/`Misc`, and every `Misc` entry collected for judgment.
  `--out FILE` writes the full JSON; stdout stays one summary line plus one line per finding.
  Exit 0 clean, 1 findings, 2 the folder is missing, unreadable, or holds no `.md`.
  Finding codes: `header_not_first`, `header_malformed`, `unknown_tag`, `entry_outside_category`.
  A `Misc` entry does not raise the exit code, because re-filing one is a judgment call.
- `render_summary.py` — reads the scan JSON, prints the markdown table (Version, Date, the five
  categories, Total) sorted by version descending, plus a totals row. Exit 0 rendered, 2 the scan
  file is missing, unparseable, or not a scan file.

**SKILL.md diff**

```diff
--- .delegation-review/SKILL.md.orig
+++ changelog-checker/SKILL.md
@@ -9,10 +9,34 @@

 ## Workflow

-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
-2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
-4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
-5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
-6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
-7. Verify the entries are clearly written and flag any that a reader would find confusing.
+1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json`
+   One pass lists every `.md` file sorted by version, checks each file starts with
+   `## vX.Y.Z — YYYY-MM-DD`, and counts the entries per category (`Added`, `Fixed`,
+   `Changed`, `Removed`, `Misc`) with totals across files.
+   Exit 0 no findings, 1 findings, 2 the folder is missing, unreadable, or holds no `.md`.
+   Exit 2 → stop and name the path that failed. Exit 1 → pass every finding line
+   through to the user verbatim; each reads `<code> <file>: <detail>`.
+
+2. Write a one-paragraph release narrative summarizing the overall direction of the changes
+   for a non-technical reader. Source it from `.changelog-scan.json`.
+
+3. Run exactly: `python3 scripts/render_summary.py .changelog-scan.json`
+   It renders the versions, dates, and per-category entry counts sorted by version
+   descending. Show its table to the user.
+
+4. Step 1 already flagged every category tag outside the allowed list as an `unknown_tag`
+   finding. For each entry under `misc_entries` in `.changelog-scan.json`, judge whether it
+   actually fits `Added`, `Fixed`, `Changed`, or `Removed`, and suggest the move.
+
+5. Verify the entries are clearly written and flag any that a reader would find confusing.
+
+## Scripts
+
+| Script (run, do not reimplement) | Does |
+|---|---|
+| `scripts/scan_changelogs.py <dir> --out F` | file list, header check, per-category counts, tag validation, Misc collection. Exit 0, 1, or 2 |
+| `scripts/render_summary.py <scan.json>` | markdown summary table, versions descending. Exit 0 or 2 |
+
+Finding codes from `scan_changelogs.py`: `header_not_first`, `header_malformed`,
+`unknown_tag`, `entry_outside_category`. A `Misc` entry is not a finding, because
+re-filing one is a judgment call left to step 4.
```

Original steps 1-3 collapse into one invocation because one pass over the files produces all
three answers. The judgment prose from steps 4, 6, and 7 survives verbatim as steps 2, 4, and 5.

**Smoke test**

```
PASS  scripts/scan_changelogs.py  exists
PASS  scripts/scan_changelogs.py  help
PASS  scripts/scan_changelogs.py  fixture-run[0]
PASS  scripts/scan_changelogs.py  fixture-run[1]
PASS  scripts/scan_changelogs.py  fixture-run[2]
PASS  scripts/scan_changelogs.py  fixture-run[3]
PASS  scripts/scan_changelogs.py  bad-data
PASS  scripts/scan_changelogs.py  bad-args
PASS  scripts/scan_changelogs.py  codes-distinct
PASS  scripts/render_summary.py  exists
PASS  scripts/render_summary.py  help
PASS  scripts/render_summary.py  fixture-run[0]
PASS  scripts/render_summary.py  bad-args

13/13 checks passed
```

Each of the four finding codes got its own fixture and its own asserted string, so no code is a
claim nothing checks.

**Verified against the target's real data**

```
$ python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json
scan: 3 files, 8 entries, 1 findings, 1 misc (changelogs)
  header_not_first v1.2.0.md: first non-empty line is "### Added", not a "## v" heading
  misc v1.1.0.md: Corrected typo in settings page label
exit 1

$ python3 scripts/render_summary.py .changelog-scan.json
| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 | unknown | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |
| **Total** | unknown | 4 | 2 | 1 | 0 | 1 | 8 |
exit 0
```

The scripts catch the planted defect and surface the one `Misc` entry for step 4's judgment. The
`.changelog-scan.json` this check produced was deleted afterward, so the target holds only its
two new scripts and the rewritten SKILL.md.

**DEAD steps:** none. Nothing to route to a `skillit:review` follow-up on that count.

**Residue:** not kept, so `.delegation-review/` is gone. Re-run this skill to regenerate the
fixtures and manifest.

**Next:** run `skillit:review` on `changelog-checker` as a final check.
