# changelog-checker — step delegation review

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-0-classify-and-report/without_skill/workspace/changelog-checker/`

Nothing was changed. This is analysis only, per the request.

## Classification rule used

- **SCRIPT** — deterministic, mechanical work over structured text: listing, parsing, regex matching, counting, sorting, table rendering. Same input must always give same output. Re-deriving it in prose each run burns tokens and produces run-to-run variance.
- **CLAUDE** — requires judgment, taste, or natural-language understanding no regex can encode.
- **HYBRID** — a deterministic extraction/validation half plus a judgment half. Script does the extraction and emits candidates; Claude judges the candidates.

The verb in the step text is not the signal. Step 7 says "verify" but the thing being verified is prose clarity, which is judgment. Step 4 says "write" but writing a narrative is judgment too.

## Per-step table

| # | Step | Class | Proposed interface / rationale |
|---|------|-------|--------------------------------|
| 1 | List every `.md` in `changelogs/`, sorted by version, note total count | **SCRIPT** | `scripts/inventory.py <changelogs_dir> [--json]` -> stdout JSON `{"count": N, "files": [{"path","version","sort_key"}]}`. Exit 0 on success, 2 on missing/unreadable dir. Semver sorting is a classic place Claude drifts (v1.10.0 vs v1.2.0); a `tuple(int(x) for x in ver.split("."))` key is exact. |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD`; record failures | **SCRIPT** | `scripts/check_headers.py <changelogs_dir> [--json]` -> one line per offending file on stdout; exit 0 = all pass, 1 = at least one violation, 2 = usage/IO error. Regex `^## v(\d+)\.(\d+)\.(\d+) — (\d{4}-\d{2}-\d{2})$` against line 1. Pure pattern match with a fixed pass/fail answer — no reason for an LLM to eyeball it. The separator is an em dash (U+2014), not a hyphen; a script gets that right every run, prose comparison often does not. Should also assert header version == filename stem. Real hit in the fixture: `v1.2.0.md` has no version header at all. |
| 3 | Count entries per category per file and total across files | **SCRIPT** | `scripts/count_entries.py <changelogs_dir> [--json]` -> per-file counts keyed by category plus a `totals` object; exit 0/2. Counting `- ` bullets under `### <Category>` headings is arithmetic over structured text — the highest-variance thing in this skill if left to prose, and its numbers feed step 5's table, so any error propagates. |
| 4 | Write a one-paragraph release narrative for a non-technical reader | **CLAUDE** | Keep in prose. Requires reading intent across releases, judging what matters to a non-technical audience, and producing fluent copy. No deterministic function produces this. A script can at most hand Claude the raw entry text as input, which steps 1-3 already do. |
| 5 | Render summary table of versions, dates, per-category counts, sorted desc | **SCRIPT** | `scripts/render_table.py [--input counts.json]`, or fold it in as `count_entries.py --format markdown` -> markdown table on stdout, versions descending; exit 0/2. Pure formatting of data step 3 already computed. Hand-rendered markdown tables are where column counts and alignment rot between runs; a formatter guarantees a stable shape. |
| 6 | Check every entry's category tag against the allowed list; for `Misc` entries, judge whether they belong elsewhere and suggest the move | **HYBRID** | Split it. Script: `scripts/check_categories.py <changelogs_dir> --allowed Added,Fixed,Changed,Removed,Misc [--json]` -> reports any heading outside the allowed list (exit 1 if found, 0 if clean, 2 on error) and emits every `Misc` entry with file, line number, and text. Claude: reads only that emitted `Misc` list and decides whether e.g. "Corrected typo in settings page label" is really `Fixed`, then suggests the move. Membership testing is set arithmetic; re-homing is semantic judgment. Neither half should do the other's work. |
| 7 | Verify entries are clearly written and flag confusing ones | **CLAUDE** | Keep in prose despite the word "verify". "Would a reader find this confusing?" has no computable answer. Heuristic proxies (length thresholds, jargon word lists, passive-voice detection) would produce confident false positives and miss the real cases — worse than no check. This is the step where an LLM earns its keep. |

Summary: **SCRIPT** 1, 2, 3, 5 · **HYBRID** 6 · **CLAUDE** 4, 7.

## Notes on shape

- Steps 1, 2, 3, 5 form one pipeline over the same parse of the same files. Parsing three times is wasteful. Recommended packaging: one `scripts/analyze_changelogs.py <dir> [--json|--markdown]` that parses once and emits inventory + header violations + per-category counts, with `check_headers` / `count_entries` as flags or subcommands rather than separate parsers. Fewer scripts, one parser, one source of truth for the numbers.
- Uniform exit-code convention across all of them: `0` clean, `1` findings, `2` usage/IO error. Then SKILL.md can say "if exit code is 1, list the findings" instead of describing how to interpret output.
- The scripts must be the sole producers of counts. If SKILL.md leaves wording that invites Claude to recount by hand, the run-to-run variance comes straight back.

## Next step

Awaiting your selection of which delegations to apply. No files were written into the skill folder. Say which rows to implement (or "all SCRIPT rows plus the script half of 6") and the scripts get written and smoke-tested then, not before.
