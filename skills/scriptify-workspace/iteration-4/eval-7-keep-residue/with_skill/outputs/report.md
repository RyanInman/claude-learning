## Delegation review: changelog-checker

**Verdict:** 4 of 7 steps become pure script invocations, plus 1 HYBRID step(s) that keep their judgment prose. Replacing the 4 SCRIPT step(s) removes ~105 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | globbing plus a version sort plus a count is a pure function of the folder | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` -> compact per-file summary; full scan JSON to --out, exit 0 scanned / 2 usage or unreadable input |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | one fixed regex on the first line every run; v1.2.0.md already fails it | `python3 scripts/check_headings.py changelogs/ --json` -> findings JSON keyed by code, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tallies and totals are arithmetic; runs must not differ | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` -> compact per-file summary; full scan JSON to --out, exit 0 scanned / 2 usage or unreadable input |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative's audience framing and emphasis should differ between reasonable runs; a script would encode one arbitrary paragraph | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table from the scan JSON, sorted descending; unit-testable exactly | `python3 scripts/render_summary.py changelogs/` -> markdown summary table, exit 0 rendered / 2 usage or unreadable input |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is mechanical; only the Misc re-triage needs judgment, and the script hands Claude just the Misc entries plus their surrounding context instead of the whole tree | `python3 scripts/check_tags.py changelogs/ --json` -> JSON with invalid[] and misc[], exit 0 clean / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | CLAUDE | clarity is a reader judgment with no fixed rule, and a script listing the entries changes no decision because Claude must read every entry anyway | - |

### What the target's own data already produces

`sample_target_data.py` flagged `changelogs/v1.2.0.md` as the first-line outlier: it opens with `### Added`, not with a version heading. The generated scripts catch it and one more real defect:

- `check_headings.py changelogs/ --json` → exit 1, one finding
  `no_h2_first_line` on `v1.2.0.md` — `first line is '### Added'; expected "## v1.2.0 - YYYY-MM-DD"`.
- `check_tags.py changelogs/ --json` → exit 1, one finding
  `misc_needs_triage` on `v1.1.0.md` — "Corrected typo in settings page label", which reads as `Fixed`.

Both fixtures for the failing runs are modelled on these two files, so the smoke test exercises the defects the target actually ships.

### DEAD steps

None. Every step earns its place; steps 4 and 7 stay prose.

---

## Applied: all 5 rows, residue kept

### Scripts written into `changelog-checker/scripts/`

| Script | Covers | Contract |
|---|---|---|
| `scan_changelogs.py` | s1, s3 | `python3 scripts/scan_changelogs.py changelogs/ --out scan.json` — full scan JSON to the file, compact per-file summary on stdout. Exit 0 / 2. Also the shared parser the other three import. |
| `check_headings.py` | s2 | `python3 scripts/check_headings.py changelogs/ --json` — findings under `findings`. Exit 0 clean / 1 findings / 2 usage. |
| `render_summary.py` | s5 | `python3 scripts/render_summary.py changelogs/` — markdown table, version descending. Exit 0 / 2. |
| `check_tags.py` | s6 | `python3 scripts/check_tags.py changelogs/ --json` — `invalid[]` and `misc[]`. Exit 0 clean / 1 findings / 2 usage. |

`check_headings.py` splits the heading failure into three codes rather than one, because a file that *has* an H2 and a file that has none are different defects and the rewritten step publishes the code to whoever reads the findings:

- `no_h2_first_line` — the first non-empty line is not an H2 at all
- `h2_not_version_dated` — an H2 is there but it is not `vX.Y.Z — YYYY-MM-DD`
- `version_filename_mismatch` — the heading version disagrees with the filename

`check_tags.py` keeps `invalid[]` and `misc[]` in two fields because they route differently: `unknown_category` is decided by a fixed rule, `misc_needs_triage` is handed to Claude with a `candidates` list.

### Diff of `changelog-checker/SKILL.md`

```diff
--- a/SKILL.md
+++ b/SKILL.md
@@ -9,10 +9,34 @@

 ## Workflow

-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
-2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
-4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
-5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
-6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
-7. Verify the entries are clearly written and flag any that a reader would find confusing.
+1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --out scan.json`
+   Stdout carries the file count, the entry total, and one line per file, sorted
+   by version. `scan.json` holds the per-file, per-category counts. Exit 0
+   scanned, 2 the folder is missing or unreadable.
+2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
+   Exit 0 clean, 1 findings on stdout under `findings`, 2 usage error. Each
+   finding names its condition: `no_h2_first_line`, `h2_not_version_dated`, or
+   `version_filename_mismatch`. Report every finding with its file.
+3. Covered by step 1. Per-category counts are in `scan.json` under
+   `files[].counts`, and the cross-file totals under `totals`.
+4. Write a one-paragraph release narrative summarizing the overall direction of
+   the changes for a non-technical reader.
+5. Run exactly: `python3 scripts/render_summary.py changelogs/`
+   Stdout is the finished markdown table, sorted by version descending. Paste it
+   verbatim. Exit 0 rendered, 2 the folder is missing or unreadable.
+6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
+   Exit 0 clean, 1 findings, 2 usage error. Tags outside the allowed list come
+   back under `invalid` as `unknown_category`. For each entry under `misc`,
+   judge whether it actually fits one of the categories in its `candidates` list
+   and suggest the move.
+7. Verify the entries are clearly written and flag any that a reader would find
+   confusing.
+
+## Re-running the checks
+
+The bundled scripts ship with their fixtures and a manifest. To verify them
+after editing one, run exactly:
+
+    python3 scripts/tests/smoke_test.py scripts/tests/manifest.json
+
+Exit 0 every check passed, 1 a check failed, 2 the manifest is unusable.
```

Steps 4 and 7 are untouched, verbatim. Step 3 is now a pointer into step 1's output rather than a second scan.

### Smoke test

```
20/20 checks passed
```

Every script passed `exists`, `help`, `fixture-run`, and `bad-args`; the two check scripts also passed `bad-data` and `codes-distinct`.

### Residue kept, as you asked

```
residue -> workspace/changelog-checker/scripts/tests  (6 fixture paths rewritten)
in place: 20/20 checks passed
from a relocated copy: 20/20 checks passed
```

`changelog-checker/scripts/tests/` now holds `manifest.json`, `smoke_test.py`, and `fixtures/` for all four scripts. Every fixture path in the manifest is stored in `{skill}/…` form, so the suite still passes after the skill folder is moved — the relocated-copy run above is the proof. Re-run it yourself any time from the skill folder:

    python3 scripts/tests/smoke_test.py scripts/tests/manifest.json

### Follow-up

Run `skillit:review` on `changelog-checker/` as a final check.
