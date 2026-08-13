# `changelog-checker` — which workflow steps belong in scripts

I read `SKILL.md` and the three files in `changelogs/`. Nothing was changed.

The test I applied to each step: **does the step have exactly one correct answer that a
parser can compute?** If yes, a script should produce it, because prose re-derivation gives
a different answer on different runs. If the step needs judgment about meaning, tone, or
audience, Claude keeps it. If it needs both, split it.

## Classification

| # | Step | Class | Why | Proposed script interface |
|---|------|-------|-----|---------------------------|
| 1 | List every `.md` in `changelogs/`, sort by version, note the count | **SCRIPT** | Directory listing plus semver sort plus a count. Zero judgment, and Claude sorts `v1.10.0` before `v1.2.0` if it sorts as text. | `scripts/scan_changelogs.py <changelogs_dir>` → JSON on stdout: `{"total_files": N, "files": [{"path","version","date","header_ok","counts":{...},"entries":[{"category","text","line"}]}], "totals":{...}}`. Files sorted by parsed semver tuple. Exit `0` scan succeeded, `2` directory missing or unreadable. |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD`; record failures | **SCRIPT** | A regex match against a fixed format. The answer is a set of filenames, identical every run. This is the step most likely to be silently wrong when eyeballed, because the em dash and the zero-padded date are easy to skim past. | `scripts/scan_changelogs.py <changelogs_dir> --check-headers` → prints one offending path per line to stdout (empty when all pass). Exit `0` all headers valid, `1` at least one file failed, `2` usage or I/O error. Regex: `^## v\d+\.\d+\.\d+ — \d{4}-\d{2}-\d{2}$` on line 1. |
| 3 | Count entries per category per file, and total across files | **SCRIPT** | Counting list items. Claude miscounts long lists and cannot show its work; the counts also feed step 5, so an error here propagates. | Already covered by step 1's scan: the `counts` object per file and the top-level `totals` object. No second script needed. |
| 4 | Write a one-paragraph release narrative for a non-technical reader | **CLAUDE** | Requires reading what the changes mean, inferring product direction, and choosing register for a stated audience. No parser produces prose. | — (Claude reads the scan JSON for facts, then writes the paragraph.) |
| 5 | Render the summary table: versions, dates, per-category counts, sorted by version descending | **SCRIPT** | Pure formatting over data step 1 already produced. Hand-rendered markdown tables drift in column count and sort order between runs. | `scripts/render_table.py` — reads the scan JSON on stdin, writes a markdown table to stdout, rows sorted by semver descending. Exit `0` rendered, `2` malformed input JSON. Usage: `scripts/scan_changelogs.py changelogs/ \| scripts/render_table.py`. |
| 6 | Check every category tag against the allowed list; for `Misc` entries, judge whether they fit another category and suggest the move | **HYBRID** | Two jobs fused in one sentence. Membership in a fixed five-item list is a set operation. Deciding that "Corrected typo in settings page label" is really a `Fixed` is a semantic call about what the entry describes. | Script half: `scripts/check_categories.py <changelogs_dir>` → prints `path:line: <tag>` for every tag outside `{Added,Fixed,Changed,Removed,Misc}`, then a `MISC:` block listing each `Misc` entry as `path:line: <entry text>`. Exit `0` no disallowed tags, `1` disallowed tags found, `2` I/O error. Claude half: read the `MISC:` block and propose a target category per entry, or say it genuinely belongs in `Misc`. |
| 7 | Verify the entries are clearly written; flag any a reader would find confusing | **CLAUDE** | The verb "verify" reads mechanical, but the predicate is "a reader would find confusing" — that is a judgment about a human's comprehension, with no ground truth to compare against. A readability score would be a proxy that answers a different question, so shipping one here would be worse than leaving the step with Claude. | — |

**Totals: 4 SCRIPT (1, 2, 3, 5), 1 HYBRID (6), 2 CLAUDE (4, 7).**

## Consolidation

Steps 1, 2, 3, and 5 all read the same files and want the same parse. Write **one** parser
(`scan_changelogs.py`) that emits JSON, and let step 2 and step 5 be flags and a
downstream renderer over that JSON. Three separate scripts each re-parsing `changelogs/`
would be three places for the parse to disagree with itself. `check_categories.py` for
step 6 can either stay separate or become a third mode of the same scanner; separate is
fine, since it is the only script whose exit code the user acts on differently.

The workflow after the split reads: run the scan, run the category check, then Claude
writes step 4's narrative, judges the `Misc` entries from step 6's output, and does step 7.

## One thing I noticed while reading the fixture

`changelogs/v1.2.0.md` has no version header at all — it opens directly with `### Added`.
That is exactly the step-2 failure the script would catch on exit code `1`. I mention it as
evidence the step is mechanical, not as a fix; you asked me not to change anything.

## Not done

Nothing was written or modified. No scripts were created. Say which steps you want
scripted and I will write them.
