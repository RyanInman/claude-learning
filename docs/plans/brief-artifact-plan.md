# brief-artifact skill plan

## Context

`resources/human-level-ai-review.md` argues that comprehension, not generation, is the bottleneck when reviewing AI output. The fix it recommends is re-presentation: layered summaries, chunking to ~200 LOC / working-memory size, risk tiering, self-stated "least confident" sections, and claim extraction with source pointers. No skill in `skills/` does this today (closest: `session-review`, review family). This plan creates `skills/brief-artifact`, a skill that reads a large prose or code artifact and writes a layered brief. Success: a reader gets a TL;DR, structure map, per-chunk summaries, claims with anchors and status, ranked risks, and a least-confident block, in a file beside the artifact and in the terminal.

## Decisions (approved in brainstorm)

- Input: prose docs, code files/dirs, and git diffs.
- Output: layered brief, written to `<artifact>.brief.md` and printed.
- Reading: pick by size. Under 4 chunks → sequential in main context. 4+ chunks → one fresh subagent per chunk.
- Verification: flag only. Claim status is `verified` (stated with evidence in artifact), `unverified`, or `contradicted` (two anchors in same artifact disagree). No external lookups.
- Name: `brief-artifact`.

## Layout (match `skills/rule-audit/`)

```
skills/brief-artifact/
  SKILL.md
  scripts/chunk_artifact.py    inventory + split, deterministic
  scripts/render_brief.py      merge chunk JSON → brief.md, validates schema
  references/chunk-schema.md   chunk JSON fields
  references/chunk-prompt.md   fixed reader prompt for sequential and subagent paths
  references/brief-template.md brief section order
  evals/                       produced by skillit:create
```

## Components

### chunk_artifact.py
- Args: path (file or dir) or `--diff <ref>`. Refuse binary files.
- Detect type: unified diff → hunks; code by extension → ~200 LOC at function/blank-line boundaries; else prose → ~1500 words at heading boundaries.
- Emit `inventory.json` to scratchpad: `chunks[] {id, type, anchor (file:line-line or heading), text_path, risk_tier}`; totals.
- `risk_tier`: `high` when code chunk touches auth, DB, IO, or dependency files (regex list in script), else `low`. Prose always `low`.

### Chunk JSON (chunk-schema.md)
`summary` ≤120 words; `claims[] {text, anchor, status}`; `risks[] {kind, anchor, note}` where kind ∈ hallucinated-api, duplicate-logic, missing-edge-case, uncited-number, unsupported-claim; `least_confident` one line.

### render_brief.py
- Reads inventory + chunk JSONs. Rejects invalid JSON with chunk id, exit 1, because the agent must re-run that chunk rather than ship a hole.
- Writes brief in template order: TL;DR (≤5 bullets, synthesized from chunk summaries by agent, passed via `--tldr` file) → structure map → per-chunk summaries, high tier first → claims table → risks ranked → least-confident block.

### SKILL.md workflow
- Step 0 Resolve target. One target given → no questions.
- Step 1 Run chunker. Report count, type, size.
- Step 2 Read. <4 chunks: main agent reads each, writes JSON per chunk using `chunk-prompt.md`. ≥4: fan out subagents, same prompt, same schema. Reason: fresh readers avoid author bias (paper, Google SRE isolation).
- Step 3 Agent writes TL;DR from summaries.
- Step 4 Run renderer, write `<artifact>.brief.md`, print it.
- Gotchas: never summarize unread chunk; `contradicted` needs two anchors; no external verification; skip skill for files under 1500 words.

### Description triggers
"summarize this doc/PR/diff", "brief me on", "TL;DR this file", "too long to read", "what does this change do". Do NOT: short files, adversarial review (`debate-review`), rule checks (`rule-audit`).

## Implementation steps

1. Invoke `skillit:create` with this plan → verify: folder scaffolded with layout above.
2. Write `chunk_artifact.py` → verify: run on `resources/human-level-ai-review.md` gives 2-3 prose chunks; on a ~600 LOC diff gives ≥3 code chunks with a `high` tier present.
3. Write `references/*.md` → verify: schema and template agree on field names.
4. Write `render_brief.py` → verify: invalid chunk JSON exits 1 with chunk id; valid set renders all sections.
5. Write SKILL.md → verify: `steyle:grading-markdown` grade A; `skillit:review` no high-priority findings.
6. Evals via `skillit:create`, 3 fixtures: (a) the review paper, sequential path; (b) synthetic 6-section doc with one planted contradiction, fan-out path, must flag `contradicted`; (c) repo diff ~600 LOC, code path. Grader: every claim has anchor, contradiction caught, brief ≤1/5 source length.

## Out of scope
External citation or package verification, PDFs, non-git diffs, adversarial pass on the brief.
