---
name: scriptify
description: >-
  Reviews a target skill folder for workflow steps to delegate to pre-written
  deterministic scripts, then, after the user picks delegations, writes the
  scripts into the target skill, rewrites its SKILL.md steps to invoke them,
  and smoke-tests every generated script. Use when the user says "scriptify
  this skill", "make my skill use scripts", "which of these steps could be a
  script", or "this skill re-derives the same busywork every run". Not for a
  general skill quality or triggering review with no intent to add scripts
  (use skillit:review), and not for authoring a brand-new skill from scratch
  (use skillit:create).
disable-model-invocation: true
---

# Delegating Skill Steps to Scripts

Convert a skill's workflow steps into generated scripts. Principle:
**script-first — every step is SCRIPT until proven CLAUDE.** A deterministic
step re-derived in prose costs tokens, latency, and variance on every run. A
script pays that cost once.

Aim for a rewritten SKILL.md that reads as a **thin orchestrator**: a control
flow of exact script invocations. Claude's role shrinks to three jobs. Claude
routes between scripts, judges structured script output at genuine decision
points, and talks to the user.

Scripts live in `scripts/`. **Run them. Do not reimplement them.**

This skill changes the target skill. After this skill finishes, run
`skillit:review` on the target as a final check.

Below, `<skill>` = the absolute path of the folder holding this SKILL.md.
Resolve it once before Step 1. Print it. Substitute the real path into every
command below, because Claude cannot run a literal `<skill>`. Never leave a
placeholder in text that reaches the target, because the target's user cannot
resolve it.

"Target" = the skill under review.

Transient files live in `.delegation-review/` in the working directory. If the
working directory is at or under the target, put `.delegation-review/`
somewhere else. Two exits leave that directory behind: a report-only
stop at Step 4 and a red smoke test at Step 7. A run started inside the target
then pollutes the skill it reviews. Print where you put it.

Every `.delegation-review/` path below means the directory you chose.
Substitute the real path. If you moved the directory, pass
`--out <dir>/manifest.json --fixtures <dir>/fixtures` to `new_manifest.py`.
Pass `--review-dir <dir>` to `keep_residue.py`.

## Step 0 — Locate the target and check eligibility

Find the folder holding the target SKILL.md. If the user pasted SKILL.md
content, save it to a scratch folder first. No SKILL.md at all → say so and
stop, because this skill reviews skills, not arbitrary markdown.

The target must be writable, user-owned, and outside every plugin cache path,
such as `~/.claude/plugins/` or `.claude-personal/plugins/cache/`. The next
plugin update silently clobbers any script written into a plugin cache.
Ineligible target → run Steps 1-3 report-only. Then offer to copy the skill
into the project. Offer to continue from Step 4 on the copy. Do not open the
Step 4 gate on a target you cannot write to.

On an eligible target only, run `git status` on the target SKILL.md. If it
holds uncommitted changes, warn the user first. Then copy the file to
`.delegation-review/SKILL.md.orig`, because that copy is the restore point.
Skip the `git status` check and the copy on an ineligible target, because the restore point protects a
rewrite that branch never performs.

## Step 1 — Inventory (deterministic)

    mkdir -p .delegation-review
    python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json

The interface audit runs each existing target script with `--help`, which
executes it. Add `--no-probe` to the command above whenever the target is
code the user did not write.

Stdout carries counts and hints only. The inventory extracts candidates. It
does not classify, and its verb hints and tool hints are hints, not verdicts.
Read the target SKILL.md yourself before you classify, because the inventory
maps the steps without reading what they mean.

Then digest the data the target's steps operate on. Run exactly:

    python3 <skill>/scripts/sample_target_data.py <target-dir>

Exit 0 digest produced, 1 the target ships no data of its own, 2 usage error.
`outliers` names the files whose first line breaks the shared shape. Those
files are usually the planted defect a step exists to catch. Use them as the
fixtures Step 5 must fail on. Read individual files only when the digest leaves
a real question. One digest costs one tool call. Reading the tree by hand costs
one call per file.

An interface you propose without opening the data invents its own fixture. It
misses the malformed file already in the target, so Step 5 derives
expectations that never exercise that file. Name in the report at least one
real finding the target's own data produces.

## Step 2 — Classify (judgment)

Read `references/delegation-rubric.md`. Then classify every inventoried step
as SCRIPT, CLAUDE, HYBRID, DEAD, or ALREADY_DELEGATED.

Classify every step SCRIPT or HYBRID unless a named judgment blocks it,
because CLAUDE is the last resort.

The rubric owns the tie-break ladder: SCRIPT over HYBRID, HYBRID over CLAUDE,
CLAUDE last. This file does not restate it, because two copies drift and you
hold both. What follows is only what the rubric does not say:

- A step mixing mechanical and judgment work is HYBRID, never CLAUDE. Cover
  every mechanical part with the proposed script. Leave a minimal judgment
  core. Keep the one inventory id, because render_report.py rejects invented
  ids.
- Every CLAUDE entry needs a `why` naming the specific judgment, conversation
  input, or user interaction no script can replace. "Requires thinking" is not
  a reason. "Reasonable runs should differ here" is.
- Every inventory id needs its own entry, because render_report.py rejects a
  classification that omits one. Where the inventory fragmented one logical
  step into several ids, classify each fragment on its own merits. Give the
  fragments that share a script the same `proposed_script.name`.
- Origin `heading-fallback` means the target has no numbered steps. The
  inventory then anchors every body-bearing section heading.
  `non_step_heading_hint: true` marks the ones that look like reference
  material. Confirm the hint against the section's text. Classify a confirmed
  hint CLAUDE with `why: reference prose, not a workflow step`. Do not force a
  script onto it. Do not skip its row.

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

**Question 2 — keep verification residue.** Ask whether to leave the fixtures
and manifest in the target's `scripts/tests/`. Offer "No (Recommended)" and
"Yes".

No pick → stop after the report. Never write into the target without an
explicit pick.

## Steps 5-9 — Apply the picks

The user picked rows → read `references/applying.md`. Follow Steps 5 to 9:
contract first, implement, smoke test, rewrite the target SKILL.md, wrap up.
`applying.md` is a reference rather than part of this body because a
report-only run never reaches it, and an unread reference costs nothing.

No pick → stop here.

## Gotchas

`references/delegation-rubric.md`'s Gotchas, read at Step 2, stay binding for
the whole run.

## Bundled files

| Script (run, do not reimplement) | Does |
|---|---|
| `scripts/inventory.py <target> --out F` | step anchors, token costs, hints, existing-script audit. Exit 0 or 2 |
| `scripts/sample_target_data.py <target>` | digests the target's own data, names first-line outliers. Exit 0, 1, or 2 |
| `scripts/new_manifest.py <cls> --target D` | scaffolds the smoke manifest from the classification. Exit 0, 1, or 2 |
| `scripts/render_report.py <cls> <inv>` | validates classification, renders report. Exit 0, 1, or 2 |
| `scripts/smoke_test.py <manifest>` | verifies generated scripts. Exit 0, 1, or 2 |
| `scripts/keep_residue.py <target>` | installs the residue and proves it survives relocation. `--force` replaces existing residue files in `scripts/tests/`. Exit 0, 1, or 2 |

| Reference | Read at |
|---|---|
| `references/delegation-rubric.md` | Step 2, before classifying |
| `references/script-conventions.md` | Step 6, before writing scripts |
| `references/applying.md` | after the Step 4 gate opens, for Steps 5-9 |

`tests/` holds authoring-time pytest coverage for the bundled scripts, run
with `python3 -m pytest tests/`. Claude does not read that coverage at run time.
