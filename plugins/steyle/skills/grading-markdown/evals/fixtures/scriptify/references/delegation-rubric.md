# Delegation Rubric: SCRIPT, CLAUDE, HYBRID, or DEAD

## Contents

- [The core test](#the-core-test)
- [The four classifications](#the-four-classifications)
- [Commonly delegable (SCRIPT) categories](#commonly-delegable-script-categories)
- [Commonly Claude-needed (CLAUDE) categories](#commonly-claude-needed-claude-categories)
- [Hybrid shapes](#hybrid-shapes)
- [Gotchas](#gotchas)

## The core test

**Every step is SCRIPT until proven CLAUDE.** The question is not "could this
be a script?" but "what exactly stops this from being a script?" — and only a
named judgment, conversation input, or user interaction counts as an answer.

Operational form: **would two different Claude runs produce meaningfully
different output on this step, and SHOULD they?** If runs shouldn't differ —
SCRIPT. If only part of the step should differ — HYBRID: script the rest.
Only when the step's whole point is output that varies with context does it
stay CLAUDE.

A deterministic step re-derived in prose is paid for on every run: tokens to
re-think it, latency to re-generate it, and variance because generation is
stochastic. A script pays that cost once, at authoring time. That is the whole
economics of delegation (see skill-reviewer's `references/token-economics.md`
for the long version).

Secondary test for close calls: **could you write the unit test for this step's
output right now?** If yes, the step is deterministic enough to script. If you
cannot say what the correct output is without seeing the input, the step needs
judgment somewhere — but that means HYBRID before it means CLAUDE.

Tie-breaks: SCRIPT over HYBRID, HYBRID over CLAUDE. The end-state to aim for
is a SKILL.md that reads as an orchestrator: script invocations connected by
the minimum prose needed for routing, judgment, and user interaction.

## The four classifications

**SCRIPT** — the step is a function of its inputs. Fully delegable. The
rewritten step becomes one exact command line ("Run exactly: ..."). Examples:
"check every file starts with a version header", "count entries per category".

**CLAUDE** — judgment, synthesis, or conversation-dependent. Scripting it
would fake determinism: the script would encode one arbitrary answer to a
question that genuinely varies. The step stays prose. Examples: "write the
release narrative", "decide which findings matter to this user". CLAUDE is
the classification of last resort: before assigning it, attempt a HYBRID
decomposition — can a script enumerate candidates, pre-compute facts, validate
the chosen answer, or render the result? Only a step that is judgment all the
way through, with no mechanical shell to strip, is pure CLAUDE.

**HYBRID** — a script prepares (gathers, counts, sorts, filters, structures),
Claude decides. The rewritten step becomes "run X, then apply judgment to its
output". In-repo precedent: skill-reviewer's `audit.py` produces a mechanical
severity guess that the agent re-triages — that is the HYBRID shape.

**DEAD** — the step should not exist: stale, duplicative, or superseded.
Do not force a script onto it. Flag it in the report and route it to a
`skill-reviewer` follow-up; never auto-delete another skill's steps.

Steps already backed by an adequate existing script (the inventory's interface
audit shows `mentioned_in_body`, `has_argparse`, `help_ok`) are classified
**ALREADY_DELEGATED** and skipped.

## Commonly delegable (SCRIPT) categories

- **Parsing/extraction** — frontmatter, JSON, log formats, structured text.
- **Fixed-rule validation** — schema checks, required fields, regex-style
  lint rules ("every heading matches the version pattern").
- **File discovery/inventory** — globbing, "list all X", mentioned-in-body
  cross-checks.
- **Report rendering from structured data** — sorting, tables, fixed markdown
  templates.
- **Diffing** — baseline vs after, set differences.
- **Aggregation/counting/statistics** — per-category tallies, totals, line
  counts, token estimates.
- **Format conversion** — CSV to JSON, one markdown shape to another.

## Commonly Claude-needed (CLAUDE) categories

Each of these keeps only its judgment core — the script-strippable shell
around it (gathering inputs, validating outputs, rendering results) still
goes to a script, making most of these HYBRID in practice:

- **Judgment and trade-offs** — anything where reasonable runs disagree.
  (Scripts still enumerate the options and the facts they're judged on.)
- **Contextual classification** — severity re-triage, intent inference,
  "does this Misc entry really belong under Fixed?". (A script lists the
  entries and applies the mechanical rules first; Claude re-triages only the
  residue.)
- **Prose writing** — summaries, narratives, explanations, descriptions.
  (A script can still gather the source material and lint the result —
  required sections present, length bounds, links resolve.)
- **Design decisions and naming.**
- **Conversation-reading** — a script cannot see pasted text or user answers.
- **User negotiation** — AskUserQuestion steps, approval gates. (A script can
  still compute the options and defaults presented.)
- **Agent-runtime-tool steps** — anything invoking MCP tools, WebFetch,
  AskUserQuestion, subagent/Task dispatch, or other permission-gated tools.
  Never pure SCRIPT: a script reimplementation (e.g. curl instead of an MCP
  call) silently loses auth, the permission model, and rate handling. At most
  HYBRID around the tool call (script prepares input / digests output).

## Hybrid shapes

1. **Extract-then-judge** — script lists candidates, Claude filters or
   interprets. (inventory.py feeding classification is itself this shape.)
2. **Judge-then-render** — Claude produces structured JSON, a script validates
   and renders it. This is the plan-validate-execute pattern; render_report.py
   is the in-skill example.
3. **Script-gates-judgment** — the script's exit code decides whether Claude
   engages at all ("exit 0: nothing to review, stop here").

## Gotchas

- **Mechanical verbs lie.** "Validate the approach with the user" contains
  "validate" and is CLAUDE. The inventory's verb hints are hints, not verdicts.
- **A trivial one-liner needs no bundled script — but it still gets pinned.**
  One `ls` or one `grep` stays inline as an exact verbatim command in the
  rewritten step, not as prose to re-derive. Bundle a script once the command
  is hard to get right on the first try or has more than one moving part.
- **Authoring-time vs run-time.** Don't script a step that runs once when the
  skill is written rather than every time the skill runs.
- **Scripting judgment hides variance behind false authority.** A wrong script
  is worse than prose: it fails silently and looks official.
- **Watch output size.** A delegated step that dumps 40KB into context traded
  token cost for token cost. Large output goes to a file via `--out`; stdout
  carries a compact summary.
- **Failure modes flip.** Prose degrades gracefully; scripts fail hard.
  Meaningful exit codes and verbose error messages are what make hard failure
  a feature instead of a trap.
