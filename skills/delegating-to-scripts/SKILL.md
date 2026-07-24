---
name: delegating-to-scripts
description: >-
  Reviews a target skill folder to find workflow steps that should be delegated
  to pre-written deterministic scripts instead of being re-derived in prose on
  every run, then, after the user picks which delegations to apply, writes
  those scripts into the target skill, rewrites its SKILL.md steps to invoke
  them, and smoke-tests every generated script. Operating principle: always use
  a script unless Claude is needed specifically. Use whenever the user wants to
  scriptify a skill, make a skill more deterministic, reduce a skill's token
  cost or run-to-run variance, move mechanical work like parsing, validation,
  counting, or report rendering into scripts, or asks which parts of a skill
  should be scripts or why a skill gives different output every run. Do NOT use
  for a general skill quality or triggering review with no intent to add
  scripts (use skill-reviewer), and do NOT use to author a brand-new skill from
  scratch (use smart-skill-creator).
---

# Delegating Skill Steps to Scripts

Convert a skill's mechanical workflow steps into pre-written scripts.
Principle: **always use a script unless Claude is needed specifically** — a
deterministic step re-derived in prose costs tokens, latency, and variance on
every run; a script pays once.

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
SCRIPT, CLAUDE, HYBRID, DEAD, or ALREADY_DELEGATED. Write the decisions to
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

Ask with AskUserQuestion (multiSelect): one option per SCRIPT/HYBRID row. More
than 4 candidates → present the top 4 by the inventory's per-step
`approx_tokens` (highest first) and say in the question text that Other
accepts row ids or "all". Include a final option: keep verification residue
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
then apply judgment to its output" — the judgment prose stays. Show the user
the unified diff of the SKILL.md change.

## Step 9 — Wrap up

Summarize: scripts written, the diff already shown, the smoke PASS line, and
any DEAD steps flagged for a skill-reviewer follow-up. If the user chose to
keep residue, move `.delegation-review/fixtures/` and `manifest.json` to
`<target>/scripts/tests/` and note the smoke command in the target's body
(future runs can re-verify instead of regenerating). Otherwise remove
`.delegation-review/` — but only after a fully green run.

## Gotchas

- Mechanical verbs lie: "validate the approach with the user" is CLAUDE.
- Steps invoking agent-runtime tools (MCP, WebFetch, AskUserQuestion, subagent
  dispatch) are never pure SCRIPT — a script rewrite loses auth, permissions,
  and rate handling. At most HYBRID around the tool call.
- A one-liner (`ls`, single `grep`) needs no bundled script; the threshold is
  "hard to get right first try, or must run identically every invocation".
- Don't script steps that run once at skill-authoring time.
- Don't delegate steps that read conversation context — scripts can't see it.
- Scripting a judgment step doesn't remove variance; it hides it behind false
  authority.
- Big output needs `--out` — dumping 40KB to stdout trades token cost for
  token cost.
- Some steps deserve deletion, not delegation: classify DEAD, don't force a
  script onto a step that shouldn't exist.

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
