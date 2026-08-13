# Which steps of `research-brief-writer` should become scripts

I read `SKILL.md` (26 lines, 7 workflow steps) and `topics.txt` (7 lines). I changed nothing.

## Verdict

Three of the seven steps are pure derivation and should move into scripts. Three depend on a tool
only the agent can call and must stay in the workflow. One is generative and must stay with the
model.

| # | Step | Verdict | Why |
|---|------|---------|-----|
| 1 | Read topics, drop blanks, dedupe, slugify | **Script** | Fixed input, fixed rules, one correct answer |
| 2 | WebFetch top source, save to `sources/<slug>.html` | Keep (agent) | WebFetch is an agent tool; picking the top source is judgment |
| 3 | AskUserQuestion which sources to keep | Keep (agent) | Interactive; a script cannot ask |
| 4 | Count words per kept source, flag under 200 | **Script** | Counting is arithmetic, and the threshold is a fixed number |
| 5 | Query `notion` MCP for page id, append summary block | Split | The MCP call stays; the summary block it appends is rendered by script |
| 6 | Write the 200-word brief in house voice | Keep (model) | Prose judgment; the only step that needs a model |
| 7 | Render index table sorted by word count desc | **Script** | Sorting and table formatting have one correct output |

## The three steps to scriptify

### Step 1 gives a different answer on different runs

Step 1 asks the model to dedupe and slugify by reading. On this exact `topics.txt` that is a trap.
The file has 7 lines and only 4 distinct topics:

- Line 3 is blank.
- Line 4, `Retrieval Augmented Generation`, collides with line 1 only after lowercasing.
- Line 6, `speculative decoding`, is an exact repeat of line 2.

The case-differing duplicate is the failure that matters. A model scanning the list sees two
visually distinct strings and can carry both forward, which then costs a wasted WebFetch, a wasted
source file, and a duplicate row in the final table. A script applies `lower()` before the
comparison every time.

I ran the rule as a script against the fixture to confirm the target output. It yields exactly four
slugs: `retrieval-augmented-generation`, `speculative-decoding`, `kv-cache-eviction`,
`mixture-of-experts-routing`.

### Step 4 is the expensive one

Step 4 is the highest-value conversion, and not because counting is hard. To count words by reading,
the agent has to pull every fetched page back through the context window. Those are raw HTML files
saved in step 2, so the agent pays for markup, scripts, and navigation chrome to produce one integer
per file. Then it counts prose in a tag soup, where "under 200 words" depends on whether it counted
the markup.

A script reads the files off disk, strips tags, counts, and returns four numbers. No HTML enters the
context. The thin-source threshold becomes a comparison rather than an estimate.

### Step 7 is where sort order drifts

Sorting four rows by word count descending is the kind of step a model usually gets right and
occasionally does not, and nothing in the output reveals the error. The row count and the numbers
look correct either way. Since the script from step 4 already holds the counts, rendering the table
is a few more lines in the same script rather than a new one.

## The nuance on step 5

Step 5 reads as one step but is two jobs. Getting the "Research Index" page id requires the `notion`
MCP tool, which only the agent can call. Building the summary block that gets appended is string
assembly over data the scripts already produced.

Script the payload, not the call. The render script emits the summary block to stdout or a file, and
the agent passes that text to the MCP append. This keeps the block's shape identical across runs,
which matters more here than elsewhere because the output lands on a shared team page where drift
accumulates visibly.

The same split applies to step 3: the AskUserQuestion call stays, but the options no longer need to
be re-derived by listing `sources/`. They come from the topics JSON that step 1's script already
wrote.

## Proposed scripts

Two files, not three. Steps 4 and 7 share the counts, so splitting them means computing twice.

**`scripts/parse_topics.py`** (step 1)

```
Usage:  parse_topics.py topics.txt
Output: JSON array to stdout, one object per unique topic: {slug, topic, line}
Rules:  skip blank lines; lowercase; non-alphanumeric runs to "-"; strip
        leading/trailing "-"; first occurrence wins
```

**`scripts/index_report.py`** (steps 4, 7, and step 5's payload)

```
Usage:  index_report.py --sources sources/ --kept kept.json [--thin 200]
Output: JSON to stdout: per-slug {slug, url, words, thin} plus a rendered
        markdown table sorted by words descending, plus the summary block
Rules:  strip HTML tags before counting; thin = words < 200
```

Both take an explicit input path and write to stdout, so they are testable without the rest of the
workflow running.

## Rewritten workflow

The step count stays at seven. What changes is who does each one.

1. Run `scripts/parse_topics.py topics.txt` and use its slugs.
2. For each slug, WebFetch the top source and save to `sources/<slug>.html`. (unchanged)
3. AskUserQuestion, offering one option per topic from step 1's JSON.
4. Run `scripts/index_report.py`. It returns word counts, thin flags, the index table, and the
   summary block.
5. Query the `notion` MCP tool for the "Research Index" page id, then append the summary block from
   step 4.
6. Write a 200-word brief per kept topic in the house voice. (unchanged)
7. Output the index table from step 4.

## What this buys

- Removes roughly four `Read` calls per run and keeps every raw HTML page out of the context window.
- Makes the dedup result reproducible, which stops the duplicate WebFetch this fixture would
  otherwise trigger.
- Turns "under 200 words" into a real comparison instead of an eyeball estimate.
- Leaves all three tool-dependent steps and the one writing step exactly where they are.

## What I would not script

Do not try to script step 2 with `curl`. It looks scriptable because the filename is deterministic,
but choosing the top source for a topic is a judgment call, and network access from a bundled script
is not something the skill should depend on. The slug half of that step is already covered by
step 1's script.

Do not script step 6. A 200-word brief in a house voice is the reason this skill uses a model.
