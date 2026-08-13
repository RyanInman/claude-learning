## Delegation review: changelog-checker

**Verdict:** 4 of 7 steps become pure script invocations, plus 1 HYBRID step(s) that keep their judgment prose. Replacing the 4 SCRIPT step(s) removes ~105 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob plus version sort plus a count; identical output every run | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> counts plus one line per finding; full structured scan to --out, exit 0 clean / 1 findings / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | one fixed regex over each first line; unit-testable now (v1.2.0.md fails it) | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> counts plus one line per finding; full structured scan to --out, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tally and totals; pure aggregation over parsed headings | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> counts plus one line per finding; full structured scan to --out, exit 0 clean / 1 findings / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the whole output is the paragraph the user reads; a script would only re-hand Claude text it must read in full, and reasonable runs should word the narrative differently | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table sorted descending from the scan data; no input varies the layout | `python3 scripts/render_summary.py .changelog-scan.json` -> markdown summary table, versions descending, exit 0 rendered / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is mechanical and the script hands Claude one fact it cannot compute itself - the short residue list of Misc entries (1 of 8 entries here) - so Claude judges only that residue instead of every entry | `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` -> counts plus one line per finding; full structured scan to --out, exit 0 clean / 1 findings / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | CLAUDE | clarity is the canonical no-script trap: a script can list entries but Claude must read all 8 anyway, so listing them changes no decision | - |

**Findings from the target's own changelog data (3 files, 8 entries):**

- `changelogs/v1.2.0.md` starts with `### Added`, not `## v1.2.0 — YYYY-MM-DD`. It is
  the only file breaking the shape the other two share, so step 2's script must exit 1
  on it and step 1 has no date to report for that version.
- `changelogs/v1.1.0.md` carries one `### Misc` entry, "Corrected typo in settings page
  label". `Misc` is on the allowed list, so the mechanical half of step 6 passes it; the
  judgment half must decide whether it belongs under `Fixed`. That single entry out of 8
  is the whole residue step 6's script would hand back to Claude.

**Reading the table:**

- Steps 1, 2, 3, and 6 all parse the same three files, so they share one script,
  `scan_changelogs.py`. One parse pass produces the file list, the heading verdicts, the
  per-category counts, and the tag audit.
- Step 5 renders that scan as the table, so it is a second script, `render_summary.py`,
  and not more prose.
- Step 4 stays Claude. The step's entire output is the paragraph the user reads. A script
  could only gather text Claude must read in full anyway.
- Step 7 stays Claude for the same reason, and it is the canonical trap: a script can list
  the entries, but Claude reads all 8 regardless, so listing them changes no decision.
- No step is DEAD, and the target ships no scripts, so nothing is ALREADY_DELEGATED.

**Next step:** you asked for the review only, so I stopped here and wrote nothing into
`changelog-checker/`. Say the word and I will write the two scripts, rewrite the SKILL.md
steps to invoke them, and smoke-test both against these fixtures.
