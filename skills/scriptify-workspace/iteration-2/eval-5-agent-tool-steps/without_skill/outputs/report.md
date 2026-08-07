# research-brief-writer: which steps should become scripts

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-5-agent-tool-steps/without_skill/workspace/research-brief-writer/`
Files inspected: `SKILL.md` (7 workflow steps), `topics.txt` (7 lines, 1 blank, 1 case-variant duplicate, 1 exact duplicate).
Nothing in the target was modified. Report only.

## Classes used

- **SCRIPT** - deterministic, same input gives same output, no judgment and no agent-only tool. Move it wholesale into a script.
- **HYBRID** - the step's core is an agent-only tool call (WebFetch, AskUserQuestion, MCP) or a judgment call, but deterministic work sits on one side of it. Script the prep or the digest; the tool call itself stays in the step.
- **CLAUDE** - the value of the step is the language or the judgment. Leave it in prose.

## Table

| # | Step | Class | What becomes a script | What stays in the step |
|---|------|-------|-----------------------|------------------------|
| 1 | Read `topics.txt`, drop blanks, drop duplicates, slugify | **SCRIPT** | All of it: `scripts/parse_topics.py` | Nothing |
| 2 | WebFetch top source per topic, save to `sources/<slug>.html` | **HYBRID** | Worklist emitter + post-save existence check | The WebFetch call and picking "the top source" |
| 3 | AskUserQuestion which sources to keep | **HYBRID** | Building the option list from what is on disk; recording the answer | The AskUserQuestion call and the user's choice |
| 4 | Count words in each kept source, flag <200 words as thin | **SCRIPT** | All of it: `scripts/word_counts.py` | Nothing |
| 5 | Notion MCP: find "Research Index" page id, append summary block | **HYBRID** | Rendering the summary block before the call | The MCP page lookup and the append |
| 6 | Write a 200-word brief per kept topic in the house voice | **CLAUDE** | Optional length check afterwards only | Writing the prose |
| 7 | Render index table (topic, URL, word count), sorted by count desc | **SCRIPT** | All of it: `scripts/render_index.py` | Nothing |

## Reasoning, step by step

### Step 1 - SCRIPT

Blank-line stripping, duplicate removal, and slug normalization are a fixed transform with one right answer. Re-deriving it in prose every run is exactly the busywork complained about, and it is where run-to-run variance starts: today's run may fold "Retrieval Augmented Generation" into "retrieval augmented generation", tomorrow's may not. `topics.txt` today contains both, plus an exact repeat of "speculative decoding" and a blank line, so the step is load-bearing on real input.

Proposed interface:

```
scripts/parse_topics.py <topics.txt> [--json]
```

- stdout: one `slug<TAB>original-topic` line per unique topic, input order preserved; `--json` emits `[{"slug": ..., "topic": ...}]`.
- exit 0 on success; exit 1 if the file is missing or yields zero topics.
- The slug rule lives once in the script (lowercase, non-alphanumeric runs to `-`, trim), so it stops being reinvented.

Expected output on the current file: 4 topics - `retrieval-augmented-generation`, `speculative-decoding`, `kv-cache-eviction`, `mixture-of-experts-routing`.

### Step 2 - HYBRID, not SCRIPT

The fetch is an agent tool call. A script must not reimplement it with `curl`, `requests`, or `urllib`: that swaps out the harness's fetch path, its permissions, and its page rendering, and "the top source for it" is a selection judgment, not a URL lookup. The deterministic work sits around it:

- Before: `scripts/fetch_plan.py --topics scratch/topics.json --sources sources/` prints only the slugs with no saved file, so a re-run does not refetch what is already on disk. Exit 0 always; empty stdout means nothing to fetch.
- After: `scripts/check_sources.py --topics scratch/topics.json --sources sources/` verifies every expected `sources/<slug>.html` exists and is non-empty; exit 1 listing the missing slugs.

The step keeps: for each slug the plan prints, WebFetch the best source, save it to `sources/<slug>.html`, and record the chosen URL into `scratch/urls.json`.

### Step 3 - HYBRID, not SCRIPT

AskUserQuestion is an agent-only tool and the answer belongs to the user, so this step can never be pure SCRIPT. What is mechanical is assembling the options: listing `sources/*.html`, mapping each back to its topic, attaching a size so the user can judge. `scripts/list_sources.py --sources sources/ --topics scratch/topics.json --json` emits that option list (slug, topic, path, bytes); exit 1 if `sources/` is empty. The ask stays in the step, and the keep-list the user chooses is written to `scratch/kept.txt` so downstream scripts have a defined input.

### Step 4 - SCRIPT

Counting words and comparing against a fixed 200 threshold is arithmetic. Doing it by eye is token-expensive and unreliable across runs.

```
scripts/word_counts.py --sources sources/ [--kept scratch/kept.txt] [--threshold 200] [--json]
```

- stdout: `slug<TAB>words<TAB>THIN|OK` lines, or a JSON array of `{"slug": ..., "words": N, "thin": true|false}` with `--json`.
- Strips script/style/tags before counting so the number reflects prose, not markup - a rule that should live in one place instead of being re-read from prose each run.
- exit 0 normally; exit 1 if a kept source file is missing. Thin sources are reported, not an error.

### Step 5 - HYBRID, not SCRIPT

Both halves - resolving the page id for "Research Index" and appending to it - are `notion` MCP calls. A script has no access to that MCP session, so this is never pure SCRIPT, and no script should try to hit the Notion HTTP API in its place. What can be scripted is the payload: `scripts/render_summary.py --counts scratch/counts.json --kept scratch/kept.txt` prints the exact summary block to append (exit 0; exit 2 on missing inputs). The step then reduces to "query notion for the page id, append the block the script printed", which is short, stable, and stops the block's shape drifting run to run.

### Step 6 - CLAUDE

The 200-word brief in the house voice is the actual product of the skill: plain, concrete, no marketing language. That is a language judgment over source content and cannot be templated without destroying the point. The prose-writing core stays with Claude. The only defensible script here is a check, not a generator - reuse the step 4 counter to assert each brief lands within tolerance of 200 words (`scripts/word_counts.py --sources briefs/ --threshold 180`). It reports; it never rewrites text.

### Step 7 - SCRIPT

Assembling rows and sorting by word count descending is pure formatting. Prose renders markdown tables inconsistently - column order, alignment, tie-breaking - a classic source of run-to-run diff noise.

```
scripts/render_index.py --counts scratch/counts.json --urls scratch/urls.json [--out -]
```

- stdout: the markdown table with columns Topic, Source URL, Word Count, sorted by word count descending, ties broken by slug ascending so output is stable.
- exit 0 on success; exit 2 if a kept topic has no recorded URL, naming it, so a silent blank cell cannot ship.

## Summary

- Pure SCRIPT: steps 1, 4, 7. These are the recurring busywork and the bulk of the run-to-run variance.
- HYBRID: steps 2, 3, 5. The agent tool call (WebFetch, AskUserQuestion, notion MCP) stays in the step; scripts only prepare its input or digest its output. No proposed script re-implements a fetch or an MCP call.
- CLAUDE: step 6. Prose writing stays with Claude; at most a length check is added around it.

Shared file contract if these are built later: `scratch/topics.json` (step 1 out), `scratch/urls.json` (step 2 out), `scratch/kept.txt` (step 3 out), `scratch/counts.json` (step 4 out). One slug vocabulary across all of them, defined by step 1.
