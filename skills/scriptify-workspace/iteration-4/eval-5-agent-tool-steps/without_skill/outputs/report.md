# research-brief-writer: which steps should become scripts

## The test I applied

A step earns a script when all three hold:

1. It is deterministic. Same input, same output, every run.
2. It needs no judgment. No taste, no voice, no reading comprehension.
3. It needs no agent-only tool. A script cannot call WebFetch, AskUserQuestion, or an MCP server.

Rule 3 is the one that decides this skill. Four of your seven steps are agent-tool steps or
judgment steps, so they stay in the SKILL.md prose. The busywork you are paying for on every run
sits in steps 1, 4, and 7.

## Step-by-step verdict

| # | Step | Verdict | Why |
|---|------|---------|-----|
| 1 | Parse topics.txt, drop blanks, dedupe, slugify | **Script** | Pure string work, and it silently goes wrong |
| 2 | WebFetch each topic to sources/<slug>.html | Keep in agent | WebFetch is a harness tool, unreachable from a script |
| 3 | AskUserQuestion which sources to keep | Keep in agent | Interactive, agent-only |
| 4 | Count words, flag sources under 200 as thin | **Script** | Counting is the model's weakest deterministic skill |
| 5 | Notion page-id lookup, append summary block | Split | MCP calls stay; the block's text is rendering |
| 6 | Write the 200-word brief in house voice | Keep in agent | Judgment. This is the step the skill exists for |
| 7 | Render the index table sorted by word count | **Script** | Rendering plus a numeric sort |

## The three that should move, and why each one bites

### Step 1: topic normalization

I ran your actual `topics.txt` through the normalization the step describes. Seven lines collapse
to four topics:

```
retrieval-augmented-generation
speculative-decoding
kv-cache-eviction
mixture-of-experts-routing
```

The file hides three separate traps in seven lines: a blank line, an exact duplicate
(`speculative decoding` appears on lines 2 and 6), and a case-variant duplicate
(`Retrieval Augmented Generation` on line 4 collapses onto line 1). A run that misses either
duplicate does a wasted WebFetch, writes a redundant brief, and puts a doubled row in the index.
Nothing errors. You just get a slightly wrong brief set, differently wrong each run.

This is the highest-value script in the skill: cheapest to write, and the only failure mode that
is invisible in the output.

### Step 4: word counting and the thin flag

"Under 200 words" is a hard numeric cutoff applied to HTML you just downloaded. The model has to
strip tags, then count, then compare. It approximates all three. Two runs over the same page will
disagree about whether it is thin, and the flag drives what you keep.

Stripping markup and splitting on whitespace is four lines of Python that returns the same integer
forever.

### Step 7: the index table

Sorting rows by a numeric column descending, then rendering fixed-format markdown, is exactly the
work a script does for free. Hand-sorting is a common silent-error spot once you have more than
about five rows.

## What I would build: two scripts, not three

Steps 4, 5's summary block, and 7 all consume the same word-count pass, so splitting them into
separate scripts means counting the same files twice. Fold them into one.

**`scripts/normalize_topics.py`**

- Input: path to `topics.txt` (default `topics.txt`).
- Output: JSON on stdout, one record per topic: `{"topic": <first-seen original spelling>, "slug": <slug>}`, plus the count of lines dropped.
- Rules: strip whitespace, drop empty lines, lowercase, collapse each run of non-alphanumeric characters to a single hyphen, trim leading and trailing hyphens, keep first-occurrence order.
- Exits non-zero when zero topics survive, so the agent stops instead of fetching nothing.

This also hands step 3 its option list for free, so the agent never re-derives the topic set a
second time to build the AskUserQuestion menu.

**`scripts/index_report.py`**

- Input: `--sources-dir sources/`, `--keep <slug,slug,...>` from the step 3 answer.
- Work: extract text from each kept HTML file, count words, flag under 200 as thin, sort descending by count.
- Output: the markdown index table for step 7, and the summary block text for step 5, and the same data as JSON so the agent can act on the thin flags.

The Notion page-id lookup and the append call stay with the agent. Only the text being appended
gets rendered by the script.

## Why one end-to-end script is impossible here

The steps interleave. Deterministic work, then an agent tool, then deterministic work:

```
normalize_topics.py  →  WebFetch loop  →  AskUserQuestion  →  index_report.py  →  write briefs  →  notion append
   (script)              (agent)           (agent)             (script)           (agent)         (agent)
```

Two script boundaries is the maximum this workflow allows. Anyone proposing a single
`run_briefs.py` is proposing to drop the fetch and the human checkpoint.

## One gap the scripting exposes

Step 7 renders a source URL column, but no earlier step records the URL anywhere. Step 2 saves
`sources/<slug>.html` and throws the URL away. Today the model papers over this by remembering the
URL from its own context; a script cannot, and neither can a resumed session.

Fix it in step 2: have the agent write `sources/<slug>.json` containing `{"url": "..."}` beside
each HTML file. Then `index_report.py` can fill the column. Worth doing regardless of whether you
script anything, because the current skill loses data.

## Gotchas to settle before writing the code

- **Define "word" once.** Extract text, drop `script` and `style` contents, split on whitespace. If the script counts extracted words and a human spot-checks raw HTML, the thin flag will look broken.
- **"Under 200" means `< 200`, not `<= 200`.** Pin it in the code so it stops being re-decided.
- **Keep the first-seen spelling, not the slug, for display.** Brief headings should read "Retrieval Augmented Generation", not "retrieval-augmented-generation".
- **Do not swap WebFetch for `curl` to make step 2 scriptable.** Different redirect, JavaScript, and paywall behavior. That is a rewrite of the step disguised as an optimization.
- **Do not template step 6.** House voice is judgment. A script that fills in a 200-word skeleton produces exactly the marketing-flavored prose the step forbids.

## Bottom line

Script steps 1, 4, and 7 as two files. Leave 2, 3, and 6 in prose because they need tools or
judgment a script cannot have. Split step 5: script the text, keep the MCP calls. Then fix the
dropped URL in step 2.
