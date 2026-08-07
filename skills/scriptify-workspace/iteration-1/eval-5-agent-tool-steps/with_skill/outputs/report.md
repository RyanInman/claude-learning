# research-brief-writer: which steps should become scripts

Report only. Nothing in `workspace/research-brief-writer/` was changed.

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/with_skill/workspace/research-brief-writer`

## Step 0 - eligibility

- SKILL.md found, writable, user-owned, outside every plugin cache path. Eligible for the full write path.
- `git status` on the target: untracked (`?? .../research-brief-writer/`). Whole folder is new to git, not a dirty edit of a tracked file. No uncommitted-change warning owed.
- Restore point saved: `scratch/.delegation-review/SKILL.md.orig`.

## Step 1 - inventory (deterministic)

    python3 /Users/admin/claude-learning/skills/scriptify/scripts/inventory.py <target> --out .delegation-review/inventory.json

Stdout:

    inventory: .../workspace/research-brief-writer
    steps: 7  existing scripts: 0  references: 0  body: ~243 tokens
      s1 numbered-list L13-14 ~38tok verbs=list tools=-
      s2 numbered-list L15-16 ~27tok verbs=- tools=WebFetch
      s3 numbered-list L17-18 ~32tok verbs=- tools=AskUserQuestion
      s4 numbered-list L19-20 ~21tok verbs=count tools=-
      s5 numbered-list L21-22 ~33tok verbs=- tools=-
      s6 numbered-list L23-24 ~27tok verbs=- tools=-
      s7 numbered-list L25-26 ~24tok verbs=count,sort,render tools=-
    EXIT=0

No existing scripts, so nothing is ALREADY_DELEGATED. The inventory's tool hints missed the `notion` MCP mention in s5; reading the step text caught it.

## Step 3 - rendered report (verbatim from render_report.py, exit 0)

## Delegation review: research-brief-writer

**Verdict:** 7 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~202 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Read the topic list from `topics.txt`, one topic per line. Drop blank lines," (L13-14) | numbered-list | 38 | SCRIPT | pure function of topics.txt: strip blanks, dedupe, slugify. Same input gives same list every run; a unit test can be written today | `python3 scripts/normalize_topics.py topics.txt --json` -> {"topics":[{"raw":"...","slug":"..."}],"dropped":{"blank":N,"duplicate":N}}, exit 0 topics found / 1 no usable topics / 2 usage |
| s2 | "For each topic, fetch the top source for it with WebFetch and save the raw" (L15-16) | numbered-list | 27 | HYBRID | WebFetch is a permission-gated agent runtime tool; a curl reimplementation loses auth and the permission model. Claude keeps the fetch and the choice of top source; the script owns the slug-to-path plan and the post-fetch completeness check | `python3 scripts/fetch_plan.py --topics .work/topics.json --sources sources/ --json   (add --verify after fetching)` -> {"planned":[{"slug":"...","path":"sources/<slug>.html","exists":false}],"missing":[],"empty":[]}, exit 0 plan emitted or verify clean / 1 verify found missing or empty sources / 2 usage |
| s3 | "Ask the user with AskUserQuestion which of the fetched sources to keep for" (L17-18) | numbered-list | 32 | HYBRID | AskUserQuestion is a user interaction no script can perform, and the keep/drop answer is the user's. The option list itself is mechanical: one option per file in sources/ with its word count and thin flag | `python3 scripts/source_stats.py sources/ --json` -> {"sources":[{"slug":"...","path":"...","url":"...","words":N,"thin":false}]}, exit 0 sources found / 1 sources dir empty / 2 usage |
| s4 | "Count the words in each kept source. Record any source under 200 words as" (L19-20) | numbered-list | 21 | SCRIPT | word count against a fixed 200-word threshold. No run should ever differ; same script as s3 with the kept set passed in | `python3 scripts/source_stats.py sources/ --kept <slug,slug,...> --json` -> same records filtered to the kept slugs, each with words and thin (words < 200), exit 0 no thin sources / 1 at least one thin source / 2 usage |
| s5 | "Query the `notion` MCP tool for the id of the page titled "Research Index"," (L21-22) | numbered-list | 33 | HYBRID | the notion MCP page lookup and the append are permission-gated tool calls Claude must make. The summary block's markdown is a fixed template over the stats and belongs in a script | `python3 scripts/render_index.py --stats .work/stats.json --format block` -> the run summary block as markdown, ready to hand to the notion append call, exit 0 rendered / 1 stats empty or missing required fields / 2 usage |
| s6 | "Write a 200-word brief for each kept topic in the house voice: plain," (L23-24) | numbered-list | 27 | HYBRID | writing 200 words in the house voice is synthesis; two good runs should differ. Only the judgment core stays: the length bound and the no-marketing-language rule are mechanical post-checks | `python3 scripts/lint_brief.py briefs/<slug>.md --min 180 --max 220 --json` -> {"words":N,"findings":[{"rule":"length|marketing-phrase","detail":"..."}]}, exit 0 clean / 1 findings / 2 usage |
| s7 | "Render the index table of topic, source URL, and word count, sorted by word" (L25-26) | numbered-list | 24 | SCRIPT | sort and render a fixed three-column table from data already computed. Textbook report rendering; hand-typing it is where run-to-run drift enters | `python3 scripts/render_index.py --stats .work/stats.json --format table` -> markdown table of topic, source URL, word count, sorted by word count descending, exit 0 rendered / 1 stats empty or missing required fields / 2 usage |

## What that means in plain terms

Four scripts cover all seven steps:

| Script | Covers | Kills this busywork |
|---|---|---|
| `normalize_topics.py` | s1 | blank/duplicate stripping and slugging re-derived every run. Your `topics.txt` already holds 1 blank line, 1 exact duplicate ("speculative decoding"), and 1 case-only duplicate ("Retrieval Augmented Generation") - exactly the case where two runs can disagree on whether the title-case twin is the same topic |
| `fetch_plan.py` | s2 | slug-to-path bookkeeping and the "did every fetch actually land" check |
| `source_stats.py` | s3, s4 | word counting and the 200-word thin threshold; also builds the AskUserQuestion option list |
| `render_index.py` | s5, s7 | the Notion summary block and the sorted index table, both fixed templates |
| `lint_brief.py` | s6 | the 200-word bound and the marketing-language check on prose Claude still writes |

Four steps keep a real Claude job that no script can take:

- **s2** - WebFetch is a permission-gated runtime tool, and picking "the top source" is judgment. Reimplementing it as `curl` in a script silently loses auth, the permission model, and rate limiting.
- **s3** - the keep/drop answer is the user's. The script only computes what the options say.
- **s5** - the `notion` MCP page lookup and the append are tool calls, same reasoning as s2.
- **s6** - writing 200 words in the house voice is synthesis. Two good runs should differ here; that is the one place variance is the point.

Those four are HYBRID rather than CLAUDE. The tool call or the judgment stays with Claude, but the mechanical shell around each one (path planning, option building, block rendering, length and voice linting) moves to a script, and that shell is most of the per-run busywork.

## Two things worth fixing that scripts will not fix

1. **Step 5 runs too early.** It appends "this run's summary block" to Notion at step 5, before the briefs are written (step 6) and before the index table is rendered (step 7). Whatever it appends cannot include either. Moving the Notion append after step 7 lets `render_index.py` feed the page and the local table from the same data. Not a delegation issue - a workflow ordering bug. Route it to a `skillit:review` follow-up.
2. **No step defines the "house voice" or where briefs get written.** s6 names a voice the skill never specifies, and gives no output path for the briefs. `lint_brief.py` needs a file to lint, so the step has to say where the brief lands.

No steps classified DEAD. No steps ALREADY_DELEGATED (the skill bundles zero scripts today).

## Gate (Step 4)

Unattended run. Full question text and options recorded in `outputs/gate.md`.

Question 1 answered by the request itself ("Report only for now, don't change anything") -> **"Report only, write nothing."** That overrides the skill's recommended "Apply all 7" default. Question 2 (keep verification residue) is moot when nothing is written.

Run therefore stopped after Step 3. Steps 5-9 not executed.

## Verification that nothing changed

    $ git status --porcelain -- .../workspace/research-brief-writer/
    ?? .../workspace/research-brief-writer/

Same untracked-only state as at Step 0. `SKILL.md` and `topics.txt` are byte-identical to the baseline; all working state lives in `scratch/.delegation-review/`.

## Next step when you want it applied

Re-run the skill and pick "Apply all 7" at the gate. It writes the four scripts into `research-brief-writer/scripts/`, smoke-tests each against fixtures, and only then rewrites SKILL.md in one atomic pass - the target SKILL.md stays pristine until the smoke test is green.
