---
name: brief-artifact
description: >-
  Reads a large prose document, code file, directory, or git diff and writes a layered brief:
  TL;DR, structure map, per-chunk summaries, claims with source anchors and a verified/unverified/
  contradicted mark, ranked risks, and a "least confident" block. The brief is saved beside the
  artifact and printed. Use whenever the user says "summarize this doc/PR/diff", "brief me on",
  "TL;DR this file", "this is too long to read", "what does this change do", "give me the gist of",
  "digest this", or points at a long report, spec, transcript, paper, PR, or diff and wants to
  understand it without reading all of it, even if they never say "summary". Do NOT use for files
  under about 1500 words or 200 lines (read them directly), for adversarial critique of a plan
  (use debate-review), or for rule compliance checks (use rule-audit).
---

# Brief Artifact

Turn a large artifact into a layered brief that a reader can absorb top-down. The research behind this
skill ("Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load") shows that reviewers lose defects past about
200 LOC per sitting and over-trust fluent AI output. So the skill chunks to that size, reads each chunk
with a fixed prompt, marks every claim with an anchor and a status, and surfaces what the reader was
least sure about.

Two scripts do the deterministic work. `scripts/chunk_artifact.py` splits and tiers. `scripts/render_brief.py`
validates chunk JSON and renders the brief. Never hand-write the inventory or the brief, because the
scripts give the same chunk boundaries and layout every run and prose does not.

## Workflow

### Step 0: Before starting

Confirm the target from the conversation: one file path, one directory, or one git ref for `--diff`.
Ask only when none is named, because a wrong target redoes the whole run. When the user named one
target, pass without asking.

### Step 1: Chunk

Run exactly one of:

```bash
python3 scripts/chunk_artifact.py <path> --out <scratch>/brief-work
python3 scripts/chunk_artifact.py --diff <ref> --out <scratch>/brief-work
```

Use the session scratchpad for `<scratch>`. The script prints one line per chunk and the mode
(`sequential` or `fan-out`). Report chunk count, type, and mode to the user in one line. If the script
refuses (binary file, empty diff, missing path), stop and tell the user why.

The script drops generated paths by default (`*-workspace/`, `outputs/`, lock files) and stops past 40
chunks. On that stop, narrow the target with a subdirectory, a tighter diff range, or `--exclude REGEX`,
and tell the user what you excluded. Pass `--allow-large` only when the user asks for the whole thing,
because a brief over 40 chunks runs longer than most readers will finish.

### Step 2: Read each chunk

The chunker wrote one `chunk-NN.prompt.txt` per chunk: the fixed reader prompt with paths filled in.
`references/chunk-prompt.md` documents that prompt and `references/chunk-schema.md` the JSON it targets;
read them only when a chunk JSON fails validation and you need the rule behind the error.

- Mode `sequential` (under 4 chunks): read each `chunk-NN.prompt.txt` yourself in order and follow it,
  writing `chunk-NN.json`.
- Mode `fan-out` (4 or more chunks): spawn one fresh subagent per chunk whose whole prompt is
  "Read and follow `<work>/chunk-NN.prompt.txt`". Launch at most 15 per message and wait for that batch before the next, because the
  harness caps concurrent subagents at 20 and refused launches leave silent holes. Fresh subagents keep
  each reader blind to the other chunks and to your own expectations, which is the isolation the paper
  recommends against reviewer bias.

Do not write a JSON for a chunk you did not read. An empty `claims` list is valid; a guessed one is not.

### Step 3: Reconcile claims, then write the TL;DR

Read every `chunk-NN.json`. Compare claims across chunks. Chunk readers see one chunk each, so a
contradiction between two chunks is visible only here. When two claims disagree, set both to
`contradicted` with anchor `A vs B` (both locations), editing the JSON files in place. Leave every other
status as the reader wrote it, because the main agent did not read the chunk text and must not upgrade
an `unverified` mark on memory.

Then write 1 to 5 bullets, each 35 words or fewer, to `<scratch>/tldr.md`. Lead with what the
artifact does or argues, then the strongest contradicted or high-risk finding if one exists. Do not
restate the chunk list.

### Step 4: Render

```bash
python3 scripts/render_brief.py --work <scratch>/brief-work --tldr <scratch>/tldr.md --out <brief-path>
```

`<brief-path>` follows `references/brief-template.md`: `X.brief.md` for a file, `D/BRIEF.md` for a
directory, `./diff-<ref>.brief.md` for a diff. On exit 1 the script names each invalid chunk. Re-run
Step 2 for those chunks only, then render again. On success the script prints the brief; that printout
is the reply to the user, followed by the brief path.

## Example

Input: `brief me on resources/human-level-ai-review.md, I don't have time to read the whole thing`

Step 1 output:

```
chunk-01  prose  low    1269 words  Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43)
chunk-02  prose  low    1439 words  Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86)
chunk-03  prose  low     584 words  Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118)

3 chunks -> .../brief-work/inventory.json
mode: sequential
```

Brief excerpt written to `resources/human-level-ai-review.md.brief.md`:

```markdown
## TL;DR
- The report argues that reviewing AI code as a raw diff fails; reviewers should read re-presentations instead (spec before code, AI self-explanation with a "least-confident" section, tests as specs, risk-tiered ~200 LOC chunks, layered summaries and diagrams, adversarial second-model back-translation) and name one human accountable per merge.
- Package hallucination is a live supply-chain risk: 19.7% fictitious packages across 16 LLMs (USENIX 2025), frontier models still at ~4.6-6.1% in 2026; validate package existence in CI before raising agent autonomy.
- One internal inconsistency: the EASE 2026 direct-review share of human comments on AI PRs is given as both 64.53% and 65.53% in the same paragraph.

## Claims
| status | claim | anchor |
| contradicted | 64.53% of human comments on AI-authored PRs were direct human review; 28.37% agent steering; 7.10% CI (EASE 2026, AIDev >932k PRs) | L84 '64.53% were direct human review' vs L84 '65.53% direct review' |
| verified | Defect detection is highest under 200 LOC per review and falls off past 400 LOC; 200-400 LOC over 60-90 minutes yields 70-90% defect discovery | Key Findings > 2 (L12) |
```

## Gotchas

- Mark `contradicted` only with two anchors joined by ` vs `. The renderer rejects anything else,
  because a contradiction the reader cannot locate on both sides is noise.
- Default to `unverified` when unsure. A false `verified` hides the exact spot the reader must check.
- Do not verify against outside sources. This skill flags; it does not fact-check, because external
  lookups belong to a separate pass with its own tools.
- Do not raise `--code-lines` or `--prose-words` to get fewer chunks. The defaults match the review
  size limits the paper reports, and bigger chunks lower recall.
- The risk tier is a regex over paths and text. Treat `high` as "look first", not "bug present".
- After launching a fan-out batch, block until its JSON files exist: run a Monitor (or a Bash
  until-loop with a 10 minute timeout) on `ls <work>/chunk-*.json | wc -l`. Do not end your turn to
  wait for notifications, because a turn that ends before render leaves the user with no brief.
- Keep claims to the 6 per chunk the renderer allows. The first run without a cap produced 79 claims
  and a brief longer than the source, which no reader finishes.
