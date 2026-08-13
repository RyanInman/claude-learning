# Delegation Rubric: SCRIPT, CLAUDE, HYBRID, or DEAD

## Contents

- [The core test](#the-core-test)
- [The four classifications](#the-four-classifications)
- [Commonly delegable (SCRIPT) categories](#commonly-delegable-script-categories)
- [Commonly Claude-needed (CLAUDE) categories](#commonly-claude-needed-claude-categories)
- [Hybrid shapes](#hybrid-shapes)
- [Gotchas](#gotchas)

## The core test

**Every step is SCRIPT until proven CLAUDE.** Do not ask "could this be a
script?". Ask "what exactly stops this from being a script?". Only a named
judgment, a conversation input, or a user interaction answers that question.

Operational form: **do two Claude runs produce different output on this step,
and must they?** If runs must not differ → SCRIPT. If only part of the step
must differ → HYBRID, and script the rest.
A step stays CLAUDE only when its whole point is output that varies with
context.

The `skillit:review` skill's token-economics reference carries the long
version of the delegation economics.

Secondary test for close calls: **could you write the unit test for this
step's output right now?** If yes, the step is deterministic enough to script.
If you cannot say what the correct output is without seeing the input, the
step needs judgment somewhere. That still means HYBRID before it means CLAUDE.

Tie-breaks: SCRIPT over HYBRID, HYBRID over CLAUDE. Aim for a SKILL.md that
reads as an orchestrator: script invocations connected by the minimum prose
needed for routing, judgment, and user interaction.

## The four classifications

**SCRIPT** — the step is a function of its inputs. Fully delegable. The
rewritten step becomes one exact command line ("Run exactly: ..."). Examples:
"check every file starts with a version header", "count entries per category".

**CLAUDE** — judgment, synthesis, or conversation-dependent. A script here
would fake determinism. It would encode one arbitrary answer to a
question that genuinely varies. The step stays prose. Examples: "write the
release narrative", "decide which findings matter to this user". Treat CLAUDE
as the classification of last resort.

Before you assign it, try a HYBRID
decomposition. Ask whether a script can enumerate candidates, pre-compute
facts, validate the chosen answer, or render the result. A step is pure CLAUDE
only when it is judgment all the way through, with no mechanical shell to
strip.

**HYBRID** — a script prepares the inputs (gathers, counts, sorts, filters,
structures), then Claude decides. The rewritten step becomes "run X, then
apply judgment to its output". Precedent: `audit.py` in `skillit:review`
produces a mechanical severity guess that Claude re-triages. That is the
HYBRID shape.

The HYBRID test: **the script must produce a fact the judgment consumes.** If
its only output is the set of items Claude has to read anyway, the step is
CLAUDE, not HYBRID. A script that wraps a read adds an invocation and removes
no reasoning. Step 8 keeps the judgment prose either way, so the run pays for a
script that buys nothing. "Check every entry reads clearly" is the canonical
trap. A script can list the entries. Claude must read every one regardless, so
the list changes no decision.

**DEAD** — the step must not exist, because it is stale, duplicative, or
superseded. Do not force a script onto it. Flag it in the report. Route it to
a `skillit:review` follow-up. Never auto-delete another skill's steps, because
the user owns the target's workflow.

Classify a step already backed by an adequate existing script as
**ALREADY_DELEGATED**, then skip it. The inventory's interface audit marks
those steps `mentioned_in_body`, `has_argparse`, and `help_ok`.

## Commonly delegable (SCRIPT) categories

- **Parsing and extraction** — frontmatter, JSON, log formats, structured text.
- **Fixed-rule validation** — schema checks, required fields, regex-style
  lint rules ("every heading matches the version pattern").
- **File discovery and inventory** — globbing, "list all X", mentioned-in-body
  cross-checks.
- **Report rendering from structured data** — sorting, tables, fixed markdown
  templates.
- **Diffing** — baseline against after, set differences.
- **Aggregation, counting, and statistics** — per-category tallies, totals,
  line counts, token estimates.
- **Format conversion** — CSV to JSON, one markdown shape to another.

## Commonly Claude-needed (CLAUDE) categories

Each category below keeps only its judgment core. The script-strippable shell
around that core still goes to a script: gathering inputs, validating outputs,
rendering results. Most of these categories are HYBRID in practice.

- **Judgment and trade-offs** — anything where reasonable runs disagree. A
  script still enumerates the options and the facts Claude judges them on.
- **Contextual classification** — severity re-triage, intent inference, "does
  this Misc entry really belong under Fixed?". A script lists the entries and
  applies the mechanical rules first. Claude re-triages only the residue.
- **Prose writing** — summaries, narratives, explanations, descriptions. A
  script still gathers the source material and lints the result: required
  sections present, length within bounds, links resolve.
- **Design decisions and naming.**
- **Conversation-reading** — a script cannot see pasted text or user answers.
- **User negotiation** — AskUserQuestion steps, approval gates. A script still
  computes the options and defaults Claude presents.
- **Agent-runtime-tool steps** — any step invoking MCP tools, WebFetch,
  AskUserQuestion, subagent dispatch, or another permission-gated tool. Never
  classify these pure SCRIPT. A curl call in place of an MCP call silently
  loses auth, the permission model, and rate limiting. Script
  at most the shell around the tool call, where the script prepares the input
  or digests the output.

## Hybrid shapes

1. **Extract-then-judge** — a script lists candidates, then Claude filters or
   interprets them. inventory.py feeding classification is itself this shape.
2. **Judge-then-render** — Claude produces structured JSON, then a script
   validates and renders it. This is the plan-validate-execute pattern, and
   render_report.py is the in-skill example.
3. **Script-gates-judgment** — the script's exit code decides whether Claude
   engages at all, as in "exit 0: nothing to review, stop here".

## Gotchas

- **Mechanical verbs lie.** "Validate the approach with the user" contains
  "validate" and is CLAUDE. The inventory's verb hints are hints, not verdicts.
- **Pin a trivial one-liner even though it needs no bundled script.**
  One `ls` or one `grep` stays inline as an exact verbatim command in the
  rewritten step, never as prose to re-derive. Bundle a script once the
  command has more than one moving part, or once it is hard to get right on
  the first try.
- **Authoring-time steps differ from run-time steps.** Do not script a step
  that runs once when the author writes the skill, because the cost it saves
  never repeats.
- **Scripting judgment hides variance behind false authority.** A wrong script
  is worse than prose, because it fails silently and looks official.
- **Cap output size.** A delegated step that dumps 40KB into context trades
  token cost for token cost. Send large output to a file with `--out`. Keep a
  compact summary on stdout.
- **Failure modes flip.** Prose degrades gracefully. Scripts fail hard.
  Meaningful exit codes and verbose error messages turn hard failure into a
  feature instead of a trap.
