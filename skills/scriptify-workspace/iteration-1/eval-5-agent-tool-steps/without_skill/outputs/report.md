# research-brief-writer — which steps should become scripts

Report only. Nothing under `workspace/` was modified.

Skill: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/without_skill/workspace/research-brief-writer`
Files present: `SKILL.md`, `topics.txt`. No `scripts/`, no `sources/`, no reference files.

## Verdict

| # | Step | Verdict | Why |
|---|------|---------|-----|
| 1 | Parse topics, drop blanks/dupes, slugify | **Script (full)** | Pure string work. Currently ambiguous and produces a filename collision. |
| 2 | Fetch top source per topic to `sources/<slug>.html` | **Hybrid** — agent keeps `WebFetch`, script owns the plan + manifest | The network call is tool-gated. Choosing which URL and recording it is not. |
| 3 | Ask which sources to keep | **Hybrid** — agent keeps `AskUserQuestion`, script builds the options | The prompt is tool-gated. Enumerating and labeling the candidates is mechanical. |
| 4 | Count words, flag <200 as thin | **Script (full)** | Deterministic — and today the verdict flips depending on how you count. |
| 5 | Notion: find page id, append summary | **Hybrid** — agent keeps the MCP calls, script renders the payload | The MCP call is tool-gated. The markdown block is a pure render. |
| 6 | Write the 200-word brief in house voice | **Prose (keep)** | The only genuine judgment step in the skill. |
| 7 | Render index table sorted by word count desc | **Script (full)** | Pure render + sort. Cannot currently run — see Defect 3. |

Three steps become scripts outright, three keep a one-line tool call with the
work around it scripted, one stays prose.

## The rule that decides steps 2, 3, and 5

These three look unscriptable because they name a tool only the agent can call —
`WebFetch`, `AskUserQuestion`, `notion` MCP. That is true of the *call*, not of
the step. Each one is a scriptable prepare stage, a one-line tool call, and a
scriptable consume stage. Today the prepare and consume halves are re-derived in
prose every run, which is exactly the busywork you want gone.

- **Step 2** — the agent must issue `WebFetch`. But building the work list
  (slug, target path, skip-if-already-fetched) and writing the chosen URL into a
  manifest is file work. Script it, and step 7 finally has a URL to print.
- **Step 3** — the agent must issue `AskUserQuestion`. But "offer one option per
  fetched source" means scanning `sources/`, pulling each `<title>`, attaching the
  word count, and emitting the option list. Script emits the list, agent passes it
  straight to the tool, script consumes the returned selection.
- **Step 5** — the agent must issue the two MCP calls. But the summary block is a
  deterministic render of data steps 1-4 already produced.

## Defects found while checking determinism

Two probe scripts under `scratch/` (not part of the skill).

### Defect 1 — step 1 is ambiguous, and one reading clobbers a file

"Drop duplicates, and normalize each remaining topic to a lowercase slug" orders
dedupe *before* normalize. `topics.txt` contains both `retrieval augmented
generation` and `Retrieval Augmented Generation`, which are distinct raw strings.
Running both readings on the real file:

```
non-blank      : 6
A dedupe->slug : 5 ['retrieval-augmented-generation', 'speculative-decoding', 'retrieval-augmented-generation', 'kv-cache-eviction', 'mixture-of-experts-routing']
B slug->dedupe : 4 ['retrieval-augmented-generation', 'speculative-decoding', 'kv-cache-eviction', 'mixture-of-experts-routing']
agree          : False
```

Reading A — the literal one — yields 5 topics including `retrieval-augmented-generation`
twice. Step 2 then writes `sources/retrieval-augmented-generation.html` twice and the
second fetch silently overwrites the first. Whether this run briefs 4 topics or 5
depends on how the model reads the sentence that day. This is the single clearest
argument for scripting step 1.

### Defect 2 — "under 200 words" has no stable answer on raw HTML

Step 2 saves raw HTML. Step 4 counts words in it. On one synthetic page whose
article body is 195 real words, four defensible counting methods:

```
naive split on raw HTML       226 words -> ok
regex strip tags              232 words -> ok
parse, drop script/style      210 words -> ok
article body only             197 words -> THIN
```

Same file, same threshold, verdict flips. Markup, `<script>`/`<style>` bodies, and
nav/footer chrome all leak into the count unless something strips them the same way
every time. A script pins one method; prose cannot.

### Defect 3 — step 7 asks for a column no step produces

The index table wants "topic, source URL, and word count". Nothing in steps 1-6
ever records a URL. Step 2 saves the page body to disk and discards where it came
from. As written, step 7 cannot be completed from the run's own artifacts — the
agent has to recall URLs from context, which is precisely the kind of thing that
drifts. The step 2 manifest fixes this.

### Defect 4 — step 5 runs before its own input exists

Step 5 appends "this run's summary block" to Notion, but the briefs (step 6) and
the index table (step 7) do not exist yet. Either the summary is written from
incomplete data or the steps are out of order. Recommend moving the Notion append
after step 7 when the scripts land.

## Proposed scripts

Four small scripts. Names and contracts, for when you decide to apply them.

**`scripts/parse_topics.py`** — covers step 1, feeds step 2
Reads `topics.txt`, emits JSON: `[{topic, slug, path}]`. Drops blanks, normalizes
then dedupes (see Gate), and hard-fails on a slug collision instead of overwriting.
Also emits the fetch plan so step 2 is a loop over rows rather than a re-derivation.

**`scripts/record_source.py`** — covers the consume half of step 2
Called once per `WebFetch`, writes `sources/manifest.json` mapping slug to URL,
fetch time, and byte size. Makes step 7's URL column real and makes re-runs
skippable.

**`scripts/measure_sources.py`** — covers step 4, feeds step 3
Parses each `sources/*.html` with one fixed extraction method, emits
`{slug, title, url, words, thin}`. Two outputs from one pass: the `AskUserQuestion`
option list for step 3 (title + word count per source) and the thin flags for step 4.

**`scripts/render_index.py`** — covers step 7 and the payload half of step 5
Takes the measurements plus the kept-slug selection, emits the index table sorted
by word count descending and the Notion summary block. Agent pastes the block into
the MCP append call.

Optional: **`scripts/check_briefs.py`** — verifies each step 6 brief is near 200
words. Checks the writing, does not do the writing.

## What stays prose

Step 6 only. House voice — plain, concrete, no marketing language — is the reason
this skill uses a model at all. Everything else in the workflow is bookkeeping
around it.

## Estimated effect

- Run-to-run variance on topic count drops to zero (Defect 1 closed).
- Thin-source flags become reproducible (Defect 2 closed).
- Step 7 becomes executable (Defect 3 closed).
- Steps 1, 4, and 7 stop consuming reasoning tokens entirely; the agent reads a
  JSON blob instead of re-deriving slugs, counts, and sort order each run.

## Gate — two decisions needed before scripts are written

Recorded in `outputs/gate.md`. Defaults chosen for this report:

1. **Dedupe order** — chose normalize-then-dedupe (reading B, 4 topics). It
   collapses the case-variant pair and eliminates the filename collision.
2. **Word-count method** — chose parse HTML, drop `<script>`/`<style>`, count
   whitespace-separated tokens over the remaining text. Main-content extraction
   would be more accurate but needs a readability dependency; this is the honest
   middle without adding one.
