Reviewed `research-brief-writer` for steps to delegate to scripts. Report only -
nothing was written into the skill.

## Delegation review: research-brief-writer

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~175 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Read the topic list from `topics.txt`, one topic per line. Drop blank lines," (L13-14) | numbered-list | 38 | SCRIPT | pure function of topics.txt: same blanks dropped, same dedupe, same slug every run. topics.txt already contains a blank line, an exact duplicate, and a case-variant duplicate, so the answer depends on doing normalize-then-dedupe in that order | `python3 scripts/normalize_topics.py topics.txt --out .brief/topics.json` -> count kept plus counts dropped as blank and duplicate, exit 0 topics kept / 1 no usable topics / 2 usage |
| s2 | "For each topic, fetch the top source for it with WebFetch and save the raw" (L15-16) | numbered-list | 27 | HYBRID | WebFetch is a permission-gated agent runtime tool, so the fetch itself cannot move into a script; the slug-to-path plan and the after-fetch completeness check around it are mechanical | `python3 scripts/plan_fetch.py .brief/topics.json --sources sources/ --json` -> JSON list of slug plus destination path still missing, and a done count, exit 0 every source present / 1 fetches still outstanding / 2 usage |
| s3 | "Ask the user with AskUserQuestion which of the fetched sources to keep for" (L17-18) | numbered-list | 32 | HYBRID | the user picks which sources to keep, and AskUserQuestion cannot be reimplemented in a script; building the option list from what actually landed in sources/ is mechanical | `python3 scripts/source_stats.py sources/ --thin-under 200 --out .brief/stats.json` -> per-source slug, title, url, word count, thin flag, plus over_option_cap when more than 4 sources exist, exit 0 sources found / 1 sources/ missing or empty / 2 usage |
| s4 | "Count the words in each kept source. Record any source under 200 words as" (L19-20) | numbered-list | 21 | SCRIPT | strip HTML tags, count words, compare against a fixed 200-word threshold; two runs must not disagree on a word count, and hand-counting raw HTML markup is exactly where prose re-derivation drifts | `python3 scripts/source_stats.py sources/ --thin-under 200 --out .brief/stats.json` -> per-source slug, title, url, word count, thin flag, plus over_option_cap when more than 4 sources exist, exit 0 sources found / 1 sources/ missing or empty / 2 usage |
| s5 | "Query the `notion` MCP tool for the id of the page titled "Research Index"," (L21-22) | numbered-list | 33 | HYBRID | the notion MCP page lookup and append carry auth and the permission model, so they stay agent-side; rendering the summary block that gets appended is a fixed template over the run data | `python3 scripts/render_index.py .brief/stats.json --format notion-block --out .brief/summary-block.md` -> path written plus line count, exit 0 rendered / 1 no kept sources to render / 2 usage |
| s6 | "Write a 200-word brief for each kept topic in the house voice: plain," (L23-24) | numbered-list | 27 | CLAUDE | a 200-word brief in the house voice is prose the user reads, and reasonable runs should differ here; a script could only re-emit source text Claude must read in full anyway | - |
| s7 | "Render the index table of topic, source URL, and word count, sorted by word" (L25-26) | numbered-list | 24 | SCRIPT | sort by word count descending and render a fixed three-column table from structured data; the sort order is the kind of thing prose silently gets wrong when two sources tie | `python3 scripts/render_index.py .brief/stats.json --format table --sort words-desc` -> the markdown index table, exit 0 rendered / 1 no kept sources to render / 2 usage |

## Four scripts cover six steps

- `normalize_topics.py` - s1
- `plan_fetch.py` - s2
- `source_stats.py` - s3 and s4 (the option list and the word counts come from
  one pass over `sources/`)
- `render_index.py` - s5 and s7 (`--format notion-block` and `--format table`
  render the same run data two ways)

## What your own topics.txt already proves

`topics.txt` holds 7 lines: 6 topics, 1 blank, and it collapses to 4 unique
slugs.

    retrieval augmented generation
    speculative decoding
    <blank>
    Retrieval Augmented Generation      <- duplicate of line 1, different case
    kv cache eviction
    speculative decoding                <- exact duplicate of line 2
    mixture of experts routing

Step 1 tells Claude to "drop duplicates, and normalize each remaining topic to
a lowercase slug" - in that order. Run it literally and
`Retrieval Augmented Generation` survives the dedupe, because it is not yet a
duplicate of anything at the moment the dedupe runs. It only becomes one after
the lowercasing that the step performs afterwards. You then fetch and brief the
same topic twice. `normalize_topics.py` fixes the order once: slug first,
dedupe on the slug.

That collapse also decides step 3. Four unique slugs means four fetched
sources, which is exactly the AskUserQuestion option cap. Add one topic to
`topics.txt` and the step as written can no longer offer "one option per
fetched source". `source_stats.py` reports `over_option_cap` so the skill
switches to a subset prompt instead of silently dropping a source.

## Two things I did not propose scripting

**s6, the briefs, stays Claude.** Its whole output is prose you read, and a
script there would only hand back source text Claude has to read in full
anyway - a dependency that removes no tokens and no variance. The one checkable
part is the 200-word bound, and that needs no new row: point the same word
counter at the finished briefs, `python3 scripts/source_stats.py briefs/
--thin-under 180 --json`, and let it flag any brief that came out short.

**The WebFetch and MCP calls themselves stay agent-side.** A script that
reimplements them with `curl` loses auth, the permission model, and rate
limiting, and it fails silently while looking official. s2 and s5 are HYBRID
for that reason: the script owns the plan and the render around the call, never
the call.

## One ordering bug I noticed

Step 5 appends to the Notion index before step 6 writes the briefs and step 7
renders the index, so the summary block gets published from data that does not
exist yet. That is a workflow ordering bug rather than a delegation question,
so I left the classification alone - but moving step 5 after step 7 is worth
doing whether or not you script anything.

## Next

Nothing has been written. Say the word and I will write the four scripts into
`research-brief-writer/scripts/`, rewrite the SKILL.md steps to invoke them,
and smoke-test each one. After that, run `skillit:review` on the target as a
final check.
