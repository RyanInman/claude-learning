## Delegation review: research-brief-writer

**Verdict:** 3 of 7 steps become pure script invocations, plus 3 HYBRID step(s) that keep their judgment prose. Replacing the 3 SCRIPT step(s) removes ~83 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Read the topic list from `topics.txt`, one topic per line. Drop blank lines," (L13-14) | numbered-list | 38 | SCRIPT | pure function of topics.txt: strip blanks, lowercase-dedupe, slugify. Runs must not differ. The shipped topics.txt already needs all three rules (7 lines, 1 blank, 1 case-variant dup, 1 exact dup, 4 unique slugs). | `python3 scripts/normalize_topics.py topics.txt --out .brief/topics.json` -> counts: lines read, blanks dropped, duplicates dropped, unique slugs, exit 0 at least one topic / 1 no usable topic / 2 usage |
| s2 | "For each topic, fetch the top source for it with WebFetch and save the raw" (L15-16) | numbered-list | 27 | HYBRID | WebFetch is a permission-gated agent tool, so the fetch itself cannot move into a script. The mechanical shell around it can: build the slug-to-path worklist, skip slugs already saved, and verify each saved file after the fetch. | `python3 scripts/fetch_plan.py .brief/topics.json --sources sources/ [--verify] --out .brief/fetch_plan.json` -> one 'slug<TAB>sources/<slug>.html<TAB>PENDING|CACHED' row per topic; with --verify, empty or non-HTML saves listed as FAILED, exit 0 plan complete / 1 verify found empty or missing saves / 2 usage |
| s3 | "Ask the user with AskUserQuestion which of the fetched sources to keep for" (L17-18) | numbered-list | 32 | HYBRID | the user's keep/drop pick is the judgment and AskUserQuestion is an agent tool, but the option rows Claude presents are mechanical: one row per fetched source with word count, thin flag, and fetch status. | `python3 scripts/source_stats.py sources/ --topics .brief/topics.json --out .brief/stats.json` -> per-source table: slug, words, THIN flag, and the AskUserQuestion option label for each, exit 0 stats produced / 1 no sources found / 2 usage |
| s4 | "Count the words in each kept source. Record any source under 200 words as" (L19-20) | numbered-list | 21 | SCRIPT | word count plus a fixed 200-word threshold. A unit test can be written against it today, and two runs counting the same file must agree. | `python3 scripts/source_stats.py sources/ --topics .brief/topics.json --out .brief/stats.json` -> per-source table: slug, words, THIN flag, exit 0 stats produced / 1 no sources found / 2 usage |
| s5 | "Query the `notion` MCP tool for the id of the page titled "Research Index"," (L21-22) | numbered-list | 33 | HYBRID | the notion MCP calls (page-id lookup, append) must stay Claude, because a script reimplementation loses auth and the permission model. The summary block appended to the page is a fixed template over stats.json, so the script renders the exact text Claude posts. | `python3 scripts/render_index.py .brief/stats.json --block --out .brief/summary-block.md` -> the rendered summary block (also written to --out), exit 0 rendered / 1 stats.json empty or malformed / 2 usage |
| s6 | "Write a 200-word brief for each kept topic in the house voice: plain," (L23-24) | numbered-list | 27 | CLAUDE | the 200-word brief in the house voice is the one output that should differ run to run; a script would encode one arbitrary summary. Its checkable bound (word count) is already covered by source_stats.py, so lint the drafts with that rather than scripting the writing. | - |
| s7 | "Render the index table of topic, source URL, and word count, sorted by word" (L25-26) | numbered-list | 24 | SCRIPT | sort stats.json by word count descending and emit a fixed three-column markdown table. No input varies the result. | `python3 scripts/render_index.py .brief/stats.json --table --out .brief/index.md` -> the rendered index table (also written to --out), exit 0 rendered / 1 stats.json empty or malformed / 2 usage |

### 4 scripts cover the 6 delegable rows

| Script | Covers | Job |
|---|---|---|
| `normalize_topics.py` | s1 | parse topics.txt, drop blanks, lowercase-dedupe, slugify |
| `fetch_plan.py` | s2 | build the fetch worklist, skip cached slugs, verify saves after WebFetch |
| `source_stats.py` | s3, s4 | word count, 200-word THIN flag, AskUserQuestion option rows |
| `render_index.py` | s5, s7 | render the Notion summary block and the sorted index table |

s3 and s4 share `source_stats.py` because the option rows s3 presents are the
same per-source facts s4 counts. s5 and s7 share `render_index.py` because both
render the same stats.json through a fixed template.

### What your own topics.txt already proves

`topics.txt` holds 7 lines and yields 4 unique slugs. It exercises all three of
s1's rules at once:

- 1 blank line (line 3)
- 1 case-variant duplicate — `Retrieval Augmented Generation` collides with
  `retrieval augmented generation` only after the lowercase step
- 1 exact duplicate — `speculative decoding` appears twice

That case-variant row is the one a hand-written run drops or keeps
inconsistently, and it is the fixture `normalize_topics.py` must be tested
against.

### The three agent-tool steps stay part-Claude

s2 (WebFetch), s3 (AskUserQuestion), and s5 (notion MCP) are never pure script.
A script reimplementation — curl in place of WebFetch, an HTTP call in place of
the MCP tool — silently loses auth, the permission model, and rate limiting.
Each keeps its tool call in prose; the script takes only the shell around it,
preparing the input or digesting the output.

### The one step that stays fully Claude

s6 writes the 200-word brief in the house voice. That output should differ run
to run, so a script there would encode one arbitrary summary as if it were the
answer. Its checkable bound is the word count, which `source_stats.py` already
computes, so lint the drafts with that script instead of scripting the writing.

### Not applied

You asked for the report only, so nothing was written into
`research-brief-writer/`. The classification and inventory sit in
`scratch/.delegation-review/` if you want to apply a subset later.
