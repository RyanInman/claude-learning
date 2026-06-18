---
name: rule-audit
description: >-
  Use when the user wants to audit or review code for adherence to the project's `.claude/rules/*.md`
  files — whether source files follow, or contradict, the path-scoped and globally-applied rules.
  Trigger on "check my code against our rules", "audit rule adherence", "are we following our
  .claude/rules", "review staged changes against the rules", "rule compliance report", or when someone
  points at the rules and asks whether the codebase complies — even if they don't name a file. Do NOT
  use to CREATE or edit rules (that is `rule-context-builder`), or for general code review unrelated to
  `.claude/rules`.
---

# Rule Adherence Review

Audits source files against the project's `.claude/rules/*.md` and reports where they violate or
contradict a rule. The counterpart to `rule-context-builder`: that skill *writes* rules, this one
*checks compliance*.

The whole job hinges on one thing being right: **which rules apply to which files.** A path-scoped
rule (`paths:` glob in its frontmatter) governs only files its glob matches; a global rule (empty
frontmatter) governs every file. Applying an API rule to a UI file — or skipping a file a glob covers
— produces a wrong report. So that mapping is computed deterministically by `scripts/map_rules.py`,
not guessed. The script also groups files that share an identical rule-set into **batches**, and you
spawn one review subagent per batch. Each subagent reads its files in its own context and **writes its
findings as JSON to a file**, so raw code never floods the main conversation; a second script
(`scripts/render_report.py`) then aggregates those files into the ranked report — sort and formatting
stay deterministic instead of being re-derived by the model each run (same fan-out/fan-in shape as
`pattern-extractor`).

## Step 1 — Pick the mode

- **staged** — review only files in `git diff --cached` (a pre-commit / pre-PR check). Default here
  when the user implies "before I commit/push" or "my changes".
- **audit** — review every file matched by a rule's globs across the repo. Default when they say
  "audit", "sweep the repo", "are we following our rules". Audit accepts an optional subdir to narrow
  scope (e.g. "audit `src/api`").

If unclear, ask which one. Audit on a large repo spawns many subagents; staged is cheap and focused.

## Step 2 — Map rules to files

Run once in the main context (it returns compact JSON, not file contents). Tee the output to
`.rule-review/map.json` — `render_report.py` reads it back in Step 4 for the report header,
`unmatched_files`, and rule count:

```bash
mkdir -p .rule-review
python3 <skill>/scripts/map_rules.py --mode <staged|audit> [--path <subdir>] | tee .rule-review/map.json
```

The script discovers `.claude/rules/*.md`, classifies each as global or path-scoped, resolves the
file universe (`git diff --cached` for staged; tracked + untracked-not-ignored files for audit), and
emits `assignments`, `batches`, `unmatched_files`, and `notes`. Read `notes` and act on them:

- "No `.claude/rules/` found" → there is nothing to check. Tell the user and stop.
- "No staged files" → tell the user, suggest `--mode audit`, stop.
- "Audit universe is N files" (large) → offer to narrow with `--path` before fanning out.

## Step 3 — Fan out one subagent per batch

For each entry in `batches`, spawn a review subagent (run them in parallel; cap ~10 concurrent — see
`superpowers:dispatching-parallel-agents`). Number the batches 0, 1, 2, … — each subagent writes to
`.rule-review/batch-<N>.json`. Read each applicable rule file once yourself (they are small) so you can
embed its text in the prompt — that keeps every subagent reviewing against identical rule text. Use
this prompt shape:

```
Review these files for adherence to the rules below. Root: <root from script output>.
Files (relative to root): <batch.files>
Read the full text of each file under the root before judging.

Applicable rules:
--- .claude/rules/api.md ---
<verbatim contents of that rule file>
--- .claude/rules/global.md ---
<verbatim contents>

Read <skill>/references/rubric-and-schema.md for the ranking rubric and the exact JSON
output schema. Review each file against ONLY the rules above — do not import rules that were
not given to you. Report clean files with empty findings.
Write the JSON object to `.rule-review/batch-<N>.json` with the Write tool, then return ONLY
a one-line count (files reviewed, findings). Do not paste the JSON or any file contents.
```

Each subagent writes the `file_findings` / `meta` JSON defined in `references/rubric-and-schema.md` to
its `.rule-review/batch-<N>.json` and returns only counts — the findings never enter the main context.

## Step 4 — Render the report (deterministic)

Once every batch has written its `.rule-review/batch-<N>.json`, render the ranked report with the
script — do not collect, sort, or format by hand:

```bash
python3 <skill>/scripts/render_report.py --findings .rule-review --map .rule-review/map.json --expect <batch-count>
```

It validates every findings file against the schema (a malformed or missing one is a hard error, exit
2 — re-run that batch), sorts findings by impact (HIGH→MEDIUM→LOW) then risk, writes the full report to
`rule-adherence-report.md` in the cwd, and prints the title block + ranked Summary table to stdout.
Relay that stdout to the user; the file holds the per-file detail — rule + exact bullet + line,
impact/risk, the offending code snippet, and an example fix when the fix is local. `unmatched_files`
(from the map) and any meta-findings render automatically. See `references/report-template.md` for the
output shape.

Then clean up: `rm -rf .rule-review` (safe to gitignore).

## Gotchas

- **Scope is the rubric's first rule.** The most common failure is a subagent flagging a file against a
  rule that was never assigned to it (e.g. judging a UI file by an API rule). The script already did the
  scoping; the prompt tells the subagent to honor it. Trust the mapping.
- **Don't manufacture findings.** A clean file is a valid, valuable result. Empty `findings` is correct,
  not a sign the review failed.
- **Vague rules can't be mechanically checked.** "Write maintainable code" yields a meta-note, not a
  pile of subjective violations. Say it can't be verified and move on.
- **Don't guess at fixes.** Example fixes must use APIs/patterns already visible in the codebase (a
  clean sibling file is the best template). If the right fix needs judgment or wider context, give a
  prose direction instead — a wrong canned fix erodes trust in the whole report.
- **Contradictory rules are a rules problem, not a code problem.** Surface them as meta-findings and
  point the user to `rule-context-builder` to fix the rules.
- **This skill reviews; it does not edit.** Report findings and suggested fixes; let the user decide
  what to change.
