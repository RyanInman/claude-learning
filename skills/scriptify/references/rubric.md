# Delegation rubric

## Contents

- [The core test](#the-core-test)
- [The classifications](#the-classifications)
- [Over-scripting signals](#over-scripting-signals)
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

Tie-breaks: HOOK over VALIDATOR when the rule must hold on every run, VALIDATOR
over SCRIPT when the step is a pass-or-fail gate, SCRIPT over HYBRID, HYBRID
over CLAUDE. Apply the tests in that order and stop at the first match. Then
adjust one notch for blast radius: a step that is catastrophic when wrong
(migration, deletion, publish) tightens one notch toward HOOK. A step whose
inputs vary widely and resist a schema loosens one notch toward CLAUDE.

## The classifications

**HOOK** — the step demands a guarantee on every run regardless of what the
model remembers: "never push to main", "run tests after every edit". A prose
rule cannot enforce itself, because attention decays as context fills. A hook
bound to a Claude Code event (`PreToolUse`, `PostToolUse`, `Stop`,
`SessionStart`, `UserPromptSubmit`) fires outside the model. Treat an all-caps
"MUST", "NEVER", or "ALWAYS" line as a HOOK candidate first, because caps mark
enforcement intent, not computation. The inventory lists these under
`enforcement_hints`. Every HOOK entry carries a `proposed_hook` with five
fields: `event`, `matcher` (tool name or pattern such as `Edit|Write`; empty for `Stop`,
`SessionStart`, and `UserPromptSubmit`, which match no tool),
`command` (what runs, and what a non-zero exit blocks), `scope` (user
settings, project settings, or the skill's own `hooks` frontmatter, narrowest
that covers every guarded path), and `false_positive_cost` (one sentence on
the legitimate work the hook could block). Never leave the cost empty, because
a hook that blocks too broadly is worse than the prose it replaces. A HOOK
whose command is a new script also carries a `proposed_script`, so Steps 5-7
build and smoke-test it.

**VALIDATOR** — the step states a success criterion a program can check: a
count under a limit, a schema, a lint, a required section present. The script
returns pass or fail plus exact locations. The criterion must be
machine-checkable before you assign this class. "The brief is complete" is not
one until it reads "the brief has all four labeled fields". Write the
sharpened criterion in `why`, because a validator built on a vague criterion
returns a false pass silently. A VALIDATOR rewrites to one exact command line,
the same as SCRIPT.

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
**ALREADY_DELEGATED** with `proposed_script: null`, and propose nothing for
it. The row stays, because render_report.py rejects an omitted id. The inventory's `scripts` audit
records `mentioned_in_body`, `has_argparse`, and `help_ok` per script. Each
step lists the scripts it names under `mentions_existing_script`.

A bundled script with `mentioned_in_body: false` is dead weight. The report
lists it under "wire or delete". Do not classify it; route the choice to the
user, because the target's owner decides whether the script still earns its
place.

## Over-scripting signals

Keep the step CLAUDE when any of these hold, because a script here fails on
the first input the author did not anticipate:

- The step's inputs are free text with no stable shape.
- The correct output depends on user intent stated elsewhere in the
  conversation.
- Two reasonable authors would write different scripts for it.
- The step runs once per invocation and costs under ten tokens of prose.
- The script would need the model's judgment as an input on every call. That
  is prose with extra steps.

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
