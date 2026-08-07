Report only. Nothing in the target skill was changed.

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-5-agent-tool-steps/with_skill/workspace/research-brief-writer/`

## Rendered report (verbatim from `render_report.py`)

## Delegation review: research-brief-writer

**Verdict:** 7 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~202 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Read the topic list from `topics.txt`, one topic per line. Drop blank lines," (L13-14) | numbered-list | 38 | SCRIPT | pure function of topics.txt: strip blanks, dedupe, lowercase slug. No run should differ | `python3 scripts/normalize_topics.py topics.txt --json` -> {"slugs":[...],"dropped_blank":N,"dropped_dup":N}, exit 0 ok / 1 empty list after normalize / 2 usage |
| s2 | "For each topic, fetch the top source for it with WebFetch and save the raw" (L15-16) | numbered-list | 27 | HYBRID | WebFetch is a permission-gated agent tool; a curl reimplementation loses auth and the permission model. Only the fetch stays with Claude | `python3 scripts/fetch_plan.py --slugs .work/slugs.json --sources sources/ --json` -> {"todo":[{"slug":..,"path":"sources/<slug>.html"}],"present":[..],"missing_after":[..]}, exit 0 nothing left to fetch / 1 fetches outstanding / 2 usage |
| s3 | "Ask the user with AskUserQuestion which of the fetched sources to keep for" (L17-18) | numbered-list | 32 | HYBRID | AskUserQuestion is an agent tool and the keep/drop answer is the user's; a script only builds the option list and defaults | `python3 scripts/source_stats.py sources/ --json` -> per-source {slug,path,url,words,thin} array plus totals; feeds the option labels, exit 0 ok / 1 no sources found / 2 usage |
| s4 | "Count the words in each kept source. Record any source under 200 words as" (L19-20) | numbered-list | 21 | SCRIPT | word count and a fixed 200-word threshold; the correct output is computable from the files alone | `python3 scripts/source_stats.py sources/ --keep .work/kept.json --json` -> same array filtered to kept sources; thin=true under 200 words, exit 0 ok / 1 thin sources present / 2 usage |
| s5 | "Query the `notion` MCP tool for the id of the page titled "Research Index"," (L21-22) | numbered-list | 33 | HYBRID | the notion MCP query and append are permission-gated tool calls Claude must make; only the summary block body is mechanical | `python3 scripts/render_summary_block.py .work/stats.json --out .work/summary-block.md` -> path written plus line count; block body goes to the file, exit 0 written / 1 empty stats / 2 usage |
| s6 | "Write a 200-word brief for each kept topic in the house voice: plain," (L23-24) | numbered-list | 27 | HYBRID | writing 200 words in the house voice is prose judgment two runs should differ on; the length bound and the marketing-language ban are fixed rules a linter checks | `python3 scripts/lint_brief.py briefs/ --min 180 --max 220 --json` -> {"findings":[{"file":..,"words":..,"banned":[..]}]}, exit 0 clean / 1 findings / 2 usage |
| s7 | "Render the index table of topic, source URL, and word count, sorted by word" (L25-26) | numbered-list | 24 | SCRIPT | fixed table columns and a fixed sort key; rendering from structured data, no judgment left | `python3 scripts/render_index.py .work/stats.json --out index.md` -> row count and output path, exit 0 rendered / 1 no rows / 2 usage |

## Reasoning per step

Rubric applied: every step is SCRIPT until proven CLAUDE. Ties break SCRIPT over
HYBRID, HYBRID over CLAUDE. No step earned pure CLAUDE, and none is DEAD.

### s1 — normalize the topic list — SCRIPT
`topics.txt` in, slug list out. Blank-drop, dedupe, and lowercase-slug are fixed
rules with one correct answer per input; the unit test is writable right now.
The live file proves the work is real busywork: 6 lines, 1 blank, and
"Retrieval Augmented Generation" duplicating "retrieval augmented generation"
only after case folding, plus "speculative decoding" duplicated outright. Claude
re-derives that dedupe every run and can silently miss the case-folded pair.

### s2 — fetch each source with WebFetch — HYBRID
WebFetch is a permission-gated agent runtime tool. Replacing it with curl inside
a script loses auth, the permission model, and rate limiting, so the fetch never
becomes SCRIPT. Everything around it is mechanical: deciding which slugs still
need a fetch, computing the `sources/<slug>.html` path, and verifying after the
fetches that every slug landed a file. `fetch_plan.py` owns that shell and
gates the step by exit code (0 = nothing outstanding, skip the fetch loop).

### s3 — ask which sources to keep — HYBRID
AskUserQuestion is an agent tool, and the keep/drop answer is the user's, so the
decision cannot be scripted. Enumerating the fetched sources and attaching the
facts the user judges on (word count, thin flag, path, URL) is pure inventory.
`source_stats.py` builds the option list; Claude presents it and records the pick.

### s4 — count words, flag under 200 as thin — SCRIPT
Counting and a fixed threshold. Two runs must not disagree, and a hand-counted
word total on an HTML page is exactly the kind of number prose gets wrong.
Reuses `source_stats.py` from s3 with `--keep` so one counting implementation
serves both steps and the s7 table.

### s5 — Notion page lookup and append — HYBRID
The `notion` MCP query and the append are permission-gated tool calls; a script
reimplementation would lose the MCP auth path. What is mechanical is the body
being appended: the summary block is a fixed template over the run's stats.
`render_summary_block.py` writes it to a file (`--out`, not stdout, so the block
never costs context twice), and Claude passes the file content to the MCP call.

### s6 — write the 200-word briefs — HYBRID
The prose itself is genuine judgment: reasonable runs should word a brief
differently, and scripting it would encode one arbitrary answer. But the step
carries two fixed rules around that core — the 200-word target and the
"no marketing language" ban. `lint_brief.py` checks length bounds and a banned
term list after Claude writes, turning a soft instruction into a verified one.
This is why the step is not CLAUDE: there is a mechanical shell to strip.

### s7 — render the index table — SCRIPT
Fixed columns (topic, source URL, word count) and a fixed sort key (word count
descending). Report rendering from structured data with no judgment left. Sorting
by hand is the classic step that drifts run to run.

## Script consolidation

Six proposed scripts, not seven: s3 and s4 share `source_stats.py`, which is the
single word-counting implementation and also feeds s5 and s7 their stats input.

| Script | Serves |
|---|---|
| `normalize_topics.py` | s1 |
| `fetch_plan.py` | s2 |
| `source_stats.py` | s3, s4 |
| `render_summary_block.py` | s5 |
| `lint_brief.py` | s6 |
| `render_index.py` | s7 |

## Notes for a later apply run

- The rewritten SKILL.md becomes a thin orchestrator: three agent-tool steps
  (WebFetch, AskUserQuestion, notion MCP) and one prose-writing step, each
  wrapped in an exact script invocation before and/or after.
- s2 and s7 both need the source URL, which only the WebFetch step knows. The
  apply run must have the fetch step record `{slug, url, path}` into
  `.work/fetched.json` so `source_stats.py` can carry the URL through to the
  table. Flag this as the one interface detail the current SKILL.md leaves
  implicit.
- The target SKILL.md is untracked in git (`?? .../SKILL.md`). A restore point
  was taken at `scratch/.delegation-review/SKILL.md.orig` before any work.
