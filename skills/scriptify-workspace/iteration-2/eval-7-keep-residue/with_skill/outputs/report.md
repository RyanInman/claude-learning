## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | glob plus version sort plus count; identical output for identical input every run | `python3 scripts/parse_changelogs.py changelogs/ --json --out .changelog-check/parsed.json` -> compact summary with --out; full parse JSON (file_count, files sorted by version, per-file counts, entries, totals) without it, exit 0 parsed / 1 no changelog files found / 2 usage or unreadable dir |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex against a fixed heading form; a unit test can be written for the output today | `python3 scripts/check_headings.py changelogs/ --json` -> findings JSON, each with file and reason (missing_version_header / malformed_version_header), exit 0 clean / 1 findings / 2 usage or unreadable dir |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tally and cross-file totals; pure aggregation over the parsed entries | `python3 scripts/parse_changelogs.py changelogs/ --json --out .changelog-check/parsed.json` -> per-file counts under files[].counts and cross-file totals under totals, exit 0 parsed / 1 no changelog files found / 2 usage or unreadable dir |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative names the release's overall direction for a non-technical reader; two reasonable runs should word and frame that differently, and the counts it draws on are already produced by parse_changelogs.py, so no mechanical shell is left to strip | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | fixed markdown table from structured data with a fixed sort; report rendering, no judgment | `python3 scripts/render_summary_table.py .changelog-check/parsed.json` -> markdown table of version, date, per-category counts, sorted by version descending, exit 0 rendered / 1 parsed JSON holds no files / 2 usage or unreadable/invalid JSON |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | checking a tag against the allowed list is a fixed set membership test; deciding whether a Misc entry really belongs under Fixed reads the entry's intent and genuinely varies | `python3 scripts/check_tags.py changelogs/ --json` -> JSON with invalid (tags outside the allowed list) and misc (every Misc entry, with file and text) for Claude to re-triage, exit 0 no invalid tags and no Misc entries / 1 findings / 2 usage or unreadable dir |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | whether a reader finds an entry confusing is judgment no fixed rule captures, but enumerating every entry to judge is mechanical, so the script hands Claude the list and Claude flags | `python3 scripts/parse_changelogs.py changelogs/ --entries` -> flat JSON list of every entry with file, category, and text, exit 0 parsed / 1 no changelog files found / 2 usage or unreadable dir |

## Reasoning per step

Rubric applied: `references/delegation-rubric.md`. Core test — every step is
SCRIPT until proven CLAUDE; the proof must name a judgment, a conversation
input, or a user interaction. Tie-breaks: SCRIPT over HYBRID, HYBRID over
CLAUDE.

**s1 — list files sorted by version, note the count → SCRIPT.**
Glob plus a version sort plus a count. A unit test for its output can be
written today. Nothing in it varies with context. Folded into
`parse_changelogs.py` because s3 and s7 need the same parse.

**s2 — check the `## vX.Y.Z — YYYY-MM-DD` heading → SCRIPT.**
Fixed-rule validation against a fixed regex. Its own script,
`check_headings.py`, because a validation step wants its own exit-code
contract (0 clean / 1 findings) that the caller can branch on.

**s3 — count entries per category and total across files → SCRIPT.**
Pure aggregation. Same inventory id keeps its own row, but it shares
`parse_changelogs.py` with s1: one parse of the folder feeds both, so the
rewritten step reads the counts out of the JSON instead of recounting.

**s4 — write the release narrative → CLAUDE.**
The only CLAUDE row. HYBRID decomposition was tried first, as the rubric
requires, and there is nothing mechanical left to strip: the source material
(counts, totals, entry text) is already produced by `parse_changelogs.py` in
step 1, so a further script would only re-hand Claude the same JSON. What
remains is framing a release's direction for a non-technical reader, and two
reasonable runs should word that differently. That is the rubric's own named
example of CLAUDE.

**s5 — render the summary table sorted by version descending → SCRIPT.**
Report rendering from structured data with a fixed sort and a fixed template.
`render_summary_table.py` consumes step 1's JSON, so the table is never
hand-typed and never re-sorted by hand.

**s6 — check category tags, re-triage `Misc` → HYBRID.**
Two halves. Checking a tag against a closed allowed list is set membership,
fully mechanical. Deciding whether "Corrected typo in settings page label"
really belongs under `Fixed` reads the entry's intent and genuinely varies.
`check_tags.py` covers the mechanical half completely: `invalid` holds tags
outside the list, `misc` holds every `Misc` entry with its text. Claude's
remaining job is the narrow re-triage call on the `misc` list, and the prose
for that stayed verbatim in the rewritten step.

**s7 — flag confusingly written entries → HYBRID.**
Whether a reader finds an entry confusing is judgment no fixed rule captures,
and a heuristic here would be the rubric's "scripting judgment hides variance
behind false authority" failure. But enumerating every entry to judge is
mechanical, so `parse_changelogs.py --entries` hands Claude a flat list of
file, category, and text. Extract-then-judge, the rubric's hybrid shape 1.

No step was classified DEAD or ALREADY_DELEGATED. The target shipped no
`scripts/` folder and no references, so the inventory's interface audit found
nothing to reuse.

## Scripts written

All four live in `workspace/changelog-checker/scripts/`, plus a private
import-only helper.

| Script | Covers | Exit codes |
|---|---|---|
| `parse_changelogs.py` | s1, s3, s7 | 0 parsed / 1 no changelog files / 2 usage |
| `check_headings.py` | s2 | 0 clean / 1 findings / 2 usage |
| `render_summary_table.py` | s5 | 0 rendered / 1 no files in JSON / 2 usage |
| `check_tags.py` | s6 | 0 no findings / 1 findings / 2 usage |
| `_changelog.py` | shared parse helpers, no CLI | n/a |

## Smoke test

    22/22 checks passed

Run twice: once against `.delegation-review/manifest.json` before the rewrite,
once against the moved `scripts/tests/manifest.json` after. Both green.
