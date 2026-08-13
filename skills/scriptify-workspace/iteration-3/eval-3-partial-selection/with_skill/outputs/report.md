## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob plus version sort plus a count; same output every run | `python3 scripts/scan_changelogs.py changelogs/ --json` -> scan JSON: files sorted by version, file_count, per-file category counts, totals, exit 0 scan produced / 1 no changelog files found / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex against a fixed heading form; v1.2.0.md already fails it | `python3 scripts/check_headings.py changelogs/ --json` -> findings JSON: one entry per file missing the '## vX.Y.Z — YYYY-MM-DD' heading, exit 0 all headings valid / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | tallying entries per category is arithmetic over parsed sections | `python3 scripts/scan_changelogs.py changelogs/ --json` -> scan JSON: files sorted by version, file_count, per-file category counts, totals, exit 0 scan produced / 1 no changelog files found / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative is prose the user reads, pitched at a non-technical reader; reasonable runs should word it differently | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table sorted by version from the scan JSON; no judgment in the layout | `python3 scripts/render_summary.py .changelog-check/scan.json` -> markdown table of version, date, per-category counts, sorted by version descending, exit 0 rendered / 1 scan JSON invalid / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is mechanical; deciding whether v1.1.0's Misc typo entry belongs under Fixed or Changed is judgment | `python3 scripts/check_categories.py changelogs/ --json` -> entries JSON: every entry with file, category, text, and flags for unknown tag and Misc, exit 0 no unknown tags and no Misc / 1 residue for Claude to judge / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | the same entry list is the input; whether wording confuses a reader varies with the reader and should differ between runs | `python3 scripts/check_categories.py changelogs/ --json` -> entries JSON: every entry with file, category, text, and flags for unknown tag and Misc, exit 0 no unknown tags and no Misc / 1 residue for Claude to judge / 2 usage |

### What the skill's own changelogs already show

`sample_target_data.py` flags `v1.2.0.md` as the shape outlier: its first line is `### Added`,
so the file carries no `## vX.Y.Z — YYYY-MM-DD` heading at all. That is the defect step 2
exists to catch, and it is real data sitting in the target today, not a hypothetical. Two
more findings come out of the same three files:

- `v1.1.0.md` uses a `### Misc` heading ("Corrected typo in settings page label"). Step 3's
  four counted categories miss it, and step 6's judgment call is about exactly this entry.
- Across the three files: 8 entries total, Added 4, Fixed 2, Changed 1, Removed 0, plus the
  one Misc. `v1.2.0.md` gets its version from its filename because its heading is missing.

Rows s1 and s3 share one script, `scan_changelogs.py` — one pass over the files produces
both the sorted list with its count and the per-category tallies. Row s5's `render_summary.py`
would consume that same JSON. Rows s6 and s7 share `check_categories.py`: one entry list,
two judgments over it.

## Applied: rows s1 and s3

You asked for the delegations for steps 1 and 3 only, so everything else is untouched.

### Script written

`changelog-checker/scripts/scan_changelogs.py` — lists the changelog files sorted by numeric
version with a total count, and counts entries per category per file plus the totals.
Interface:

    python3 scripts/scan_changelogs.py changelogs/ --json     # full scan JSON to stdout
    python3 scripts/scan_changelogs.py changelogs/ --out F    # JSON to F, summary to stdout
    exit 0 scan produced / 1 no changelog .md files found / 2 usage or unreadable directory

Two decisions worth naming:

- Versions sort numerically, so v1.9.0 precedes v1.10.0. A lexical sort reverses that pair,
  and the smoke test asserts the numeric order on a fixture built from exactly that pair.
- Entries under a category outside the counted four land in `other_categories` instead of
  being dropped, because a discarded entry makes `total_entries` lie. On the target's own
  data that field reports the `Misc` entry in `v1.1.0.md`.

### Smoke test

    PASS  scripts/scan_changelogs.py  exists
    PASS  scripts/scan_changelogs.py  help
    PASS  scripts/scan_changelogs.py  fixture-run[0]
    PASS  scripts/scan_changelogs.py  fixture-run[1]
    PASS  scripts/scan_changelogs.py  fixture-run[2]
    PASS  scripts/scan_changelogs.py  bad-args

    6/6 checks passed

### SKILL.md diff

```diff
@@ -9,9 +9,10 @@

 ## Workflow

-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
+1. Run exactly: `python3 scripts/scan_changelogs.py changelogs/ --json`
+   `files` holds every `.md` file sorted by version and `file_count` is the total. Exit 1 means the folder holds no changelog files — report that and stop. Exit 2 is a usage or read error.
 2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+3. Take the per-category counts from the same scan JSON: `versions[].counts` per file, `totals` across files. Entries under any other category heading are tallied under `other_categories`, so they are counted rather than dropped.
 4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
 5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
 6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
```

### Not applied

Rows s2, s5, s6, and s7 keep their original prose. No DEAD steps were found, so there is
nothing to route to a `skillit:review` follow-up. Verification residue was not kept, so
`.delegation-review/` is removed. Run `skillit:review` on changelog-checker as a final check.

Still on the table whenever you want it: `check_headings.py` for step 2 catches the
`v1.2.0.md` defect on every run, and `render_summary.py` for step 5 renders the table
straight from the scan JSON that step 1 now produces.
