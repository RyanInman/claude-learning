---
name: scriptify
description: >-
  Slash-only: invoked explicitly via /scriptify, never auto-triggered.
  Reviews a target skill folder for workflow steps to delegate to pre-written
  deterministic scripts, then, after the user picks delegations, writes the
  scripts into the target skill, rewrites its SKILL.md steps to invoke them,
  and smoke-tests every generated script. Operating principle: script-first —
  every step is SCRIPT until proven CLAUDE; end-state is SKILL.md as a thin
  orchestrator over deterministic scripts. Not for a general skill quality or
  triggering review with no intent to add scripts (use skill-reviewer), and
  not for authoring a brand-new skill from scratch (use smart-skill-creator).
disable-model-invocation: true
---

# Delegating Skill Steps to Scripts

Convert a skill's workflow steps into pre-written scripts. Principle:
**script-first — every step is SCRIPT until proven CLAUDE.** Any step whose
output could be deterministic gets a script; the burden of proof is on keeping
prose, never on adding a script. A deterministic step re-derived in prose
costs tokens, latency, and variance on every run; a script pays once.

Target end-state: the rewritten SKILL.md reads as a **thin orchestrator** — a
control flow of exact script invocations, where Claude's role shrinks to
routing between scripts, judging their structured output at genuine decision
points, and talking to the user. Script as much as possible first; connect the
remaining gaps with prose.

Scripts live in `scripts/`. **Run them; don't reimplement them.**

This skill CHANGES the target skill. For a read-only quality review use the
sibling `skill-reviewer` — and running it on the target after this skill
finishes is a good final check.

Below, `<skill>` = this skill's folder; "target" = the skill under review.
Transient files live in `.delegation-review/` in the working directory.

## Step 0 — Locate the target and check eligibility

Find the folder containing the target SKILL.md. If the user pasted SKILL.md
content, save it to a scratch folder first. No SKILL.md at all → this skill
reviews skills, not arbitrary markdown; say so and stop.

Eligibility: the target must be writable, user-owned, and OUTSIDE plugin/cache
paths (anything under a plugins cache such as `~/.claude/plugins/` or
`.claude-personal/plugins/cache/`) — scripts written into a plugin cache are
silently clobbered on the next plugin update. Ineligible target → run
report-only (steps 1-4), then offer to copy the skill into the project.

Check `git status` for the target SKILL.md. If it has uncommitted changes,
warn the user and copy it to `.delegation-review/SKILL.md.orig` before
anything else — that copy is the restore point.

## Step 1 — Inventory (deterministic)

    mkdir -p .delegation-review
    python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json

Stdout is counts and hints only. The inventory extracts candidates — it does
NOT classify, and its verb/tool hints are hints, not verdicts. Now read the
target SKILL.md itself: the inventory is the map, not the territory.

## Step 2 — Classify (judgment)

Read `references/delegation-rubric.md`, then classify every inventoried step:
SCRIPT, CLAUDE, HYBRID, DEAD, or ALREADY_DELEGATED.

Classify aggressively. Tie-break rules:

- In doubt between SCRIPT and HYBRID → SCRIPT.
- In doubt between HYBRID and CLAUDE → HYBRID.
- Before writing CLAUDE, attempt a HYBRID decomposition: can a script
  enumerate the candidates, pre-compute the facts, validate the answer, or
  render the result, leaving Claude only the narrow decision? If yes, HYBRID.
- A step mixing mechanical and judgment work is HYBRID, never CLAUDE: the
  proposed script covers every mechanical part (keep the one inventory id —
  the validator rejects invented ids), leaving a minimal judgment core.
- Every CLAUDE entry needs a `why` naming the specific judgment, conversation
  input, or user interaction no script can replace. "Requires thinking" is
  not a reason; "reasonable runs should differ here" is.

Write the decisions to
`.delegation-review/classification.json` — terse: reference inventory step ids,
never duplicate step text. Schema (full version in render_report.py's header):

    {"target": "<abs path>", "steps": [
      {"id": "s2", "class": "SCRIPT", "why": "same regex check every run",
       "proposed_script": {"name": "check_headings.py",
         "interface": "python3 scripts/check_headings.py changelogs/ --json",
         "stdout": "findings JSON", "exit": "0 clean / 1 findings / 2 usage"}}]}

SCRIPT and HYBRID entries need a full proposed_script; the rest set it null.

## Step 3 — Render the report

    python3 <skill>/scripts/render_report.py .delegation-review/classification.json .delegation-review/inventory.json

Exit 1 means the classification is invalid — fix classification.json per the
stderr messages and re-run. Paste the rendered report to the user verbatim.

## Step 4 — Gate: the user picks

Ask with AskUserQuestion (multiSelect): one option per SCRIPT/HYBRID row, with
every row preselected in the recommendation — the default posture is "apply
all"; the gate exists so the user can drop rows, not so they must opt in. More
than 4 candidates → present the top 4 by the inventory's per-step
`approx_tokens` (highest first), mark them "(Recommended)", and say in the
question text that Other accepts row ids or "all" (and that "all" is the
recommended answer). Include a final option: keep verification residue
(fixtures + manifest) in the target's `scripts/tests/` afterward (default off).

No pick → stop after the report. Never write into the target without an
explicit pick.

## Step 5 — Contract first (before any script exists)

For each chosen row, derive the test expectations from the step's SEMANTICS —
what the prose says the step must catch — not from any script output:

1. Create fixtures under `.delegation-review/fixtures/<script-name>/`. Every
   validation/check script gets at least one passing AND one failing example.
2. Append the entry to `.delegation-review/manifest.json` (schema in
   smoke_test.py's header): happy-path invocation(s), a `bad_data_invocation`
   against the failing fixture asserting the finding, and a `bad_invocation`
   with broken args. Fixture paths in the manifest must be absolute — the
   smoke tester runs scripts from the target skill dir, not the workdir.

Re-read `.delegation-review/classification.json` from disk here — work from
the recorded decisions, not chat memory.

## Step 6 — Implement the scripts

Write each script into `<target>/scripts/`, built to pass the manifest you
already wrote. Follow `references/script-conventions.md` (argv-only, exit
codes 0/1/2, JSON to stdout, --help, header docstring). Name collision with an
existing file → ask the user; never silently overwrite. Do NOT touch the
target SKILL.md in this step.

## Step 7 — Smoke test

    python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json

On FAIL: fix the script, not the expectation (unless the expectation misread
the step's semantics — say so if you change one), and re-run until exit 0.
Red run → stop here; the target SKILL.md is still pristine and
`.delegation-review/` is preserved for resumption. Never claim done on red.

## Step 8 — Rewrite the target SKILL.md (atomic, last)

Only after green. Rewrite all chosen steps in ONE pass. Lossless rule: replace
only the mechanical instruction with the exact invocation ("Run exactly:
`python3 scripts/check_headings.py changelogs/ --json`"); keep rationale,
branching, and gotcha sentences verbatim. HYBRID steps become "run the script,
then apply judgment to its output" — the judgment prose stays.

Shape the result as an orchestrator: each rewritten step opens with its exact
invocation, branching keys off script exit codes or stdout fields wherever the
script exposes them ("exit 1 → …", "if `findings` is empty → …"), and the
surviving prose is only the judgment, user interaction, and routing that
scripts cannot do. Mechanical prose the scripts now cover does not survive the
rewrite. Show the user the unified diff of the SKILL.md change.

## Step 9 — Wrap up

Summarize: scripts written, the diff already shown, the smoke PASS line, and
any DEAD steps flagged for a skill-reviewer follow-up. If the user chose to
keep residue, move `.delegation-review/fixtures/` and `manifest.json` to
`<target>/scripts/tests/` and note the smoke command in the target's body
(future runs can re-verify instead of regenerating). Otherwise remove
`.delegation-review/` — but only after a fully green run.

## Gotchas

The Gotchas section of `references/delegation-rubric.md` (read at Step 2)
stays binding through Steps 5-8. The three that bite at implementation time:
agent-runtime-tool steps (MCP, WebFetch, AskUserQuestion, subagent dispatch)
are never pure SCRIPT; big output needs `--out`; one-liners get pinned
verbatim in the rewritten step, not bundled.

## Bundled files

| Script (run, don't reimplement) | Does |
|---|---|
| `scripts/inventory.py <target> --out F` | step anchors, token costs, hints, existing-script audit; exit 0/2 |
| `scripts/render_report.py <cls> <inv>` | validates classification, renders report; exit 0/1/2 |
| `scripts/smoke_test.py <manifest>` | verifies generated scripts; exit 0/1/2 |

| Reference | Read at |
|---|---|
| `references/delegation-rubric.md` | Step 2, before classifying |
| `references/script-conventions.md` | Step 6, before writing scripts |

`tests/` holds authoring-time pytest coverage for the bundled scripts
(`python3 -m pytest tests/`); `evals/` holds triggering/behavior evals.
Neither is read at run time.
