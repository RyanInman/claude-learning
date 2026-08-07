---
name: scriptify
description: >-
  Reviews a target skill folder for workflow steps to delegate to pre-written
  deterministic scripts, then, after the user picks delegations, writes the
  scripts into the target skill, rewrites its SKILL.md steps to invoke them,
  and smoke-tests every generated script. Operating principle: script-first —
  every step is SCRIPT until proven CLAUDE; end-state is SKILL.md as a thin
  orchestrator over deterministic scripts. Not for a general skill quality or
  triggering review with no intent to add scripts (use skillit:review), and
  not for authoring a brand-new skill from scratch (use skillit:create).
disable-model-invocation: true
---

# Delegating Skill Steps to Scripts

Convert a skill's workflow steps into pre-written scripts. Principle:
**script-first — every step is SCRIPT until proven CLAUDE.** A deterministic
step re-derived in prose costs tokens, latency, and variance on every run. A
script pays that cost once.

Aim for a rewritten SKILL.md that reads as a **thin orchestrator**: a control
flow of exact script invocations. Claude's role shrinks to three jobs. Claude
routes between scripts, judges structured script output at genuine decision
points, and talks to the user.

Scripts live in `scripts/`. **Run them. Do not reimplement them.**

This skill changes the target skill. For a read-only quality review, run
`skillit:review` instead. After this skill finishes, run `skillit:review` on
the target as a final check.

Below, `<skill>` = this skill's folder. "Target" = the skill under review.
Transient files live in `.delegation-review/` in the working directory.

## Step 0 — Locate the target and check eligibility

Find the folder holding the target SKILL.md. If the user pasted SKILL.md
content, save it to a scratch folder first. No SKILL.md at all → say so and
stop, because this skill reviews skills, not arbitrary markdown.

The target must be writable, user-owned, and outside every plugin cache path,
such as `~/.claude/plugins/` or `.claude-personal/plugins/cache/`. The next
plugin update silently clobbers any script written into a plugin cache.
Ineligible target → run Steps 1-3 report-only. Then offer to copy the skill
into the project and to continue from Step 4 on the copy. Do not open the Step
4 gate on a target you cannot write to.

Run `git status` on the target SKILL.md. If it holds uncommitted changes, warn
the user first. Then copy the file to `.delegation-review/SKILL.md.orig`,
because that copy is the restore point.

## Step 1 — Inventory (deterministic)

    mkdir -p .delegation-review
    python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json

Stdout carries counts and hints only. The inventory extracts candidates. It
does not classify, and its verb hints and tool hints are hints, not verdicts.
Read the target SKILL.md yourself before you classify, because the inventory
maps the steps without reading what they mean.

The interface audit runs each existing target script with `--help`. Add
`--no-probe` when the target is code the user did not write, because probing
executes it.

## Step 2 — Classify (judgment)

Read `references/delegation-rubric.md`. Then classify every inventoried step
as SCRIPT, CLAUDE, HYBRID, DEAD, or ALREADY_DELEGATED.

Classify aggressively. Tie-break rules:

- In doubt between SCRIPT and HYBRID → SCRIPT.
- In doubt between HYBRID and CLAUDE → HYBRID.
- Before you write CLAUDE, try a HYBRID decomposition. Ask whether a script
  can enumerate the candidates, pre-compute the facts, validate the answer, or
  render the result. If yes, classify the step HYBRID and leave Claude the
  narrow decision.
- A step mixing mechanical and judgment work is HYBRID, never CLAUDE. Cover
  every mechanical part with the proposed script, and leave a minimal judgment
  core. Keep the one inventory id, because the validator rejects invented ids.
- Every CLAUDE entry needs a `why` naming the specific judgment, conversation
  input, or user interaction no script can replace. "Requires thinking" is not
  a reason. "Reasonable runs should differ here" is.
- Every inventory id needs its own entry, because render_report.py rejects a
  classification that omits one. Where the inventory fragmented one logical
  step into several ids, classify each fragment on its own merits. Give the
  fragments that share a script the same `proposed_script.name`.
- Origin `heading-fallback` means the target has no numbered steps, so the
  anchors are plain section headings. Classify a section that is not a
  workflow step as CLAUDE with `why: reference prose, not a workflow step`.
  Do not force a script onto it.

Write the decisions to `.delegation-review/classification.json`. Keep the file
terse. Reference inventory step ids. Never duplicate step text. The schema
follows. render_report.py's header holds the full version:

    {"target": "<abs path>", "steps": [
      {"id": "s2", "class": "SCRIPT", "why": "same regex check every run",
       "proposed_script": {"name": "check_headings.py",
         "interface": "python3 scripts/check_headings.py changelogs/ --json",
         "stdout": "findings JSON", "exit": "0 clean / 1 findings / 2 usage"}}]}

SCRIPT and HYBRID entries need a full proposed_script. Every other class sets
it null.

## Step 3 — Render the report

    python3 <skill>/scripts/render_report.py .delegation-review/classification.json .delegation-review/inventory.json

Exit 1 means the classification is invalid. Fix classification.json per the
stderr messages. Re-run the command. Paste the rendered report to the user
verbatim.

## Step 4 — Gate: the user picks

Ask with AskUserQuestion. Send both questions below in one call. Each question
caps at 4 options, so the rows and the residue choice cannot share a question.

**Question 1 — which rows to apply.** Default to "apply all", because
the gate exists so the user can drop rows, not so the user must opt in.

- 4 or fewer SCRIPT and HYBRID rows → `multiSelect: true`, one option per row,
  every option marked "(Recommended)".
- More than 4 rows → three options: "Apply all N (Recommended)", "Apply a
  subset — list row ids in Other", "Report only, write nothing". Do not list
  the top 4 rows instead, because that drops the remaining rows silently.

**Question 2 — keep verification residue** (fixtures and manifest) in the
target's `scripts/tests/` afterward? Offer "No (Recommended)" and "Yes".

No pick → stop after the report. Never write into the target without an
explicit pick.

## Step 5 — Contract first (before any script exists)

For each picked row, derive the test expectations from the semantics of the
step — what the prose says the step must catch. Never derive them from script
output. Then write the contract:

1. Create fixtures under `.delegation-review/fixtures/<script-name>/`. Give
   every validation script at least one passing example and one failing
   example.
2. Append the entry to `.delegation-review/manifest.json`, per the schema in
   smoke_test.py's header. Each entry holds the happy-path invocations, a
   `bad_data_invocation` against the failing fixture that asserts the finding,
   and a `bad_invocation` with broken args. Write every fixture path in the
   manifest as an absolute path, because smoke_test.py runs scripts from
   the target skill folder, not the working directory.

Re-read `.delegation-review/classification.json` from disk here, because the
recorded decisions outrank chat memory.

## Step 6 — Implement the scripts

Write each script into `<target>/scripts/`. Build each one to pass the
manifest you already wrote. Follow `references/script-conventions.md`:
argv-only, exit codes 0, 1, and 2, JSON to stdout, `--help`, header docstring.
Name collision with an existing file → ask the user. Never overwrite silently.
Leave the target SKILL.md untouched in this step, because Step 8 rewrites it
in one atomic pass.

## Step 7 — Smoke test

    python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json

On FAIL, fix the script, not the expectation. Change an expectation only when
it misread the step's semantics, and name the one you changed. Re-run until
exit 0. Red run → stop here. The target SKILL.md stays pristine, and
`.delegation-review/` holds the state so a later run can resume. Never claim done
on red.

## Step 8 — Rewrite the target SKILL.md (atomic, last)

Rewrite only after a green smoke test. Rewrite all picked rows in one pass.
Lossless rule: replace only the mechanical instruction with the exact
invocation, as in "Run exactly:
`python3 scripts/check_headings.py changelogs/ --json`".
Keep rationale, branching, and gotcha sentences verbatim. Turn each
HYBRID step into "run the script, then apply judgment to its output", because
the judgment prose stays.

Shape the result as an orchestrator. Open each rewritten step with its exact
invocation. Key the branching off script exit codes or stdout fields wherever
the script exposes them. Write each branch as "exit 1 → …" or as "if
`findings` is empty → …". Leave only the judgment, user interaction, and routing that scripts cannot do.
Cut the mechanical prose the scripts now cover.

A SCRIPT step and a HYBRID step, before → after:

    - 2. Check that each file starts with a heading of the form
    -    `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
    + 2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
    +    Exit 0 clean, 1 findings (JSON on stdout), 2 usage error.

    - 6. Check every entry's category tag against the allowed list; for
    -    entries tagged `Misc`, judge whether they fit another category.
    + 6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
    +    Invalid tags come back under `invalid`. For each entry under `misc`,
    +    judge whether it actually fits another category and suggest the move.

If the user picked keep-residue at Step 4, add the smoke-test command to the
target's body in this same pass. Add it here, because Step 9 moves files only
and must not reopen the body. Then show the user the unified diff of the
SKILL.md change.

## Step 9 — Wrap up

Summarize four things: the scripts written, the diff already shown, the smoke
PASS line, and any DEAD steps flagged for a `skillit:review` follow-up.

If the user picked keep-residue, move `.delegation-review/fixtures/` and
`manifest.json` into `<target>/scripts/tests/`. Then rewrite the manifest's
absolute fixture paths to the new location. Then re-run smoke_test.py against
the moved manifest. The move invalidates every fixture path the manifest
holds, so a skipped rewrite leaves residue that fails on first use.

Otherwise remove `.delegation-review/`, but only after a fully green run.

## Gotchas

The Gotchas section of `references/delegation-rubric.md`, read at Step 2,
stays binding through Steps 5-8. Three of those gotchas bite at implementation
time:

- Agent-runtime-tool steps (MCP, WebFetch, AskUserQuestion, subagent dispatch)
  are never pure SCRIPT, because a script reimplementation loses auth and the
  permission model.
- Big output needs `--out`, because a step that dumps 40KB into context spends
  the tokens the script was meant to save.
- Pin one-liners verbatim in the rewritten step. Never bundle them, because a
  single command costs less inline than in a file.

## Bundled files

| Script (run, do not reimplement) | Does |
|---|---|
| `scripts/inventory.py <target> --out F` | step anchors, token costs, hints, existing-script audit. Exit 0 or 2 |
| `scripts/render_report.py <cls> <inv>` | validates classification, renders report. Exit 0, 1, or 2 |
| `scripts/smoke_test.py <manifest>` | verifies generated scripts. Exit 0, 1, or 2 |

| Reference | Read at |
|---|---|
| `references/delegation-rubric.md` | Step 2, before classifying |
| `references/script-conventions.md` | Step 6, before writing scripts |

`tests/` holds authoring-time pytest coverage for the bundled scripts, run
with `python3 -m pytest tests/`. `evals/` holds triggering evals and behavior
evals. Claude reads neither at run time.
