## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob, version sort, and count are a function of the folder contents; two runs must not differ | `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` -> compact summary: file count, heading failures, per-category totals, non-standard tags, exit 0 clean / 1 findings / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex check of the first line against `## vX.Y.Z — YYYY-MM-DD`; the correct output is a function of the file. On the shipped data it must flag v1.2.0.md, which opens with `### Added` and carries no version heading or date | `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` -> compact summary: file count, heading failures, per-category totals, non-standard tags, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tallies and totals are pure aggregation over the same parse the heading check already performs | `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` -> compact summary: file count, heading failures, per-category totals, non-standard tags, exit 0 clean / 1 findings / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the whole output is a narrative the user reads, pitched at a non-technical reader; reasonable runs should word it differently. A script could only re-gather the entries Claude must read anyway. Lint the one-paragraph bound afterwards, but keep the step CLAUDE | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | rendering a sorted markdown table from the scan JSON is a fixed template over structured data; hand-typing it invites arithmetic drift from step 3's counts | `python3 scripts/render_summary.py .changelog-scan.json` -> markdown table of version, date, per-category counts, sorted by version descending, exit 0 rendered / 2 usage or unreadable scan JSON |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | membership in the allowed tag list is a mechanical set check the script owns; deciding that v1.1.0.md's Misc entry `Corrected typo in settings page label` belongs under Fixed is contextual classification only Claude makes. Script lists every Misc and unknown-tag entry with its text, Claude re-triages that residue | `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` -> compact summary: file count, heading failures, per-category totals, non-standard tags, exit 0 clean / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | judging that an entry reads confusingly varies with context and stays Claude's, but enumerating every entry with its file, category, and text is mechanical and the scan already does it; Claude reads the entry list instead of the changelog tree | `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` -> compact summary: file count, heading failures, per-category totals, non-standard tags, exit 0 clean / 1 findings / 2 usage |

### Findings from the target's own data

`sample_target_data.py` digested `changelogs/` (3 files) and named one outlier. Both defects below come from the shipped files, not from a hypothetical fixture:

- `v1.2.0.md` opens with `### Added`, so it has no `## vX.Y.Z — YYYY-MM-DD` heading and no date at all. Step 2 exists to catch this, and step 5's table has no date to print for that version. The scan script must treat a missing heading as a finding, not as a crash.
- `v1.1.0.md` carries a `### Misc` section holding `Corrected typo in settings page label`, which reads as `Fixed`. That is exactly the residue step 6 hands to judgment after the script has done the allowed-list check.

### Proposed scripts

Two scripts cover the six mechanical rows:

- `scan_changelogs.py` — one parse pass over `changelogs/` produces every mechanical fact steps 1, 2, 3, 6, and 7 need: the version-sorted file list and count, per-file heading validity, per-category entry counts and totals, and every entry with its file, tag, and text. Full data to `--out`, compact summary on stdout, exit 1 when it finds anything.
- `render_summary.py` — renders the version-descending markdown table from the scan JSON, so the table never disagrees with the counts.

Step 4 stays yours: the release narrative is prose whose wording should vary. Steps 6 and 7 stay half yours: the script lists the `Misc` and unknown-tag entries and every entry's text, and you judge the recategorization and the clarity flags.

You asked for the review only, so nothing has been written into `changelog-checker/`. Say the word and I will apply the delegations.
