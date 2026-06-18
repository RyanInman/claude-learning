---
name: rule-audit
description: >-
  Audit code for adherence to a project's `.claude/rules/*.md` — report where source files violate or
  contradict the path-scoped and global rules. Trigger on "check my code against our rules", "audit
  rule adherence", "are we following our .claude/rules", "review staged changes against the rules",
  "rule compliance report", or any ask about whether the codebase complies with the rules — even if no
  file is named. Do NOT use to CREATE or edit rules (use `rule-context-builder`), or for general code
  review unrelated to `.claude/rules`.
---

# Rule Adherence Review

Audit source files against `.claude/rules/*.md` and report where they violate or contradict a rule.
Counterpart to `rule-context-builder` (that skill writes rules; this one checks compliance).

Correctness hinges on **which rules apply to which files**: a path-scoped rule (`paths:` glob in its
frontmatter) governs only files its glob matches; a global rule (empty frontmatter) governs every file.
Misassigning a rule — or skipping a file a glob covers — produces a wrong report, so the mapping is
computed deterministically by `scripts/map_rules.py`, never guessed. The script also groups files with
an identical rule-set into **batches** — one review subagent per batch. Each subagent reads its files
in its own context and writes findings as JSON to a file, keeping raw code out of the main
conversation; `scripts/render_report.py` then aggregates those files into the ranked report, so sorting
and formatting stay deterministic (same fan-out/fan-in shape as `pattern-extractor`).

## Step 1 — Scope the review (ask first)

Confirm scope before running anything — a vague "check our rules" must not silently become a full-repo
audit spawning many subagents. Confirm **what to review** (skip if the user already pinned it):

- **staged** — files in `git diff --cached`; cheap pre-commit / pre-PR check. Default when they
  imply "before I commit/push" or "my changes".
- **audit** — files matched by rule globs. Default for "audit", "sweep the repo", "are we following
  our rules". Negotiate the smallest useful scope: push `--path <subdir>` over the whole tree.
  Full-repo audit is allowed only on explicit confirmation.

Do not ask about impact threshold here. Subagents grade every level regardless, so it is purely a
render-time filter — default to HIGH+MEDIUM and offer the LOW re-render in Step 4.

## Step 2 — Map rules to files

Run once in main context. `--out` writes the full JSON to `.rule-review/map.json` (read back by
`render_report.py` in Step 4 for the header, `unmatched_files`, and rule count) and prints a compact
summary — `batches`, `notes`, and counts — to stdout, keeping the per-file `assignments` array out of
the conversation:

```bash
mkdir -p .rule-review
python3 <skill>/scripts/map_rules.py --mode <staged|audit> [--path <subdir>] --out .rule-review/map.json
```

It discovers `.claude/rules/*.md`, classifies each as global or path-scoped, resolves the file universe
(`git diff --cached` for staged; tracked + untracked-not-ignored for audit), and emits `assignments`,
`batches`, `unmatched_files`, and `notes`. Act on `notes`:

- "No `.claude/rules/` found" → nothing to check; tell the user and stop.
- "No staged files" → tell the user, suggest `--mode audit`, stop.
- "Audit universe is N files" (large) → offer to narrow with `--path` before fanning out.

## Step 3 — Fan out one subagent per batch

For each entry in `batches`, spawn a review subagent in parallel (cap ~10 concurrent — see
`superpowers:dispatching-parallel-agents`). Number batches 0, 1, 2, …; each writes to
`.rule-review/batch-<N>.json`. Pass the rule file paths from `batch.rules` (relative to root) and have
the subagent read them itself — the files are static, so every subagent reads identical rule text
without it passing through the main context. Use this shape:

```
Review these files for adherence to the rules below. Root: <root from script output>.
Files (relative to root): <batch.files>
Read the full text of each file under the root before judging.

Applicable rule files (read each in full before judging; paths relative to root):
<batch.rules, one path per line>

Read <skill>/references/rubric-and-schema.md for the ranking rubric and exact JSON output schema.
Review each file against ONLY the rules listed above — do not import rules not given to you. Report clean
files with empty findings. Write the JSON object to `.rule-review/batch-<N>.json` with the Write tool,
then return ONLY a one-line count (rule files read, files reviewed, findings). Do not paste the JSON or any file contents.
```

Each subagent writes the `file_findings` / `meta` JSON from `references/rubric-and-schema.md` and
returns only counts — findings never enter the main context.

## Step 4 — Render the report (deterministic)

Once every batch has written its file, render the ranked report — do not collect, sort, or format by
hand:

```bash
python3 <skill>/scripts/render_report.py --findings .rule-review --map .rule-review/map.json --expect <batch-count> [--min-impact HIGH|MEDIUM|LOW]
```

It validates each findings file against the schema (malformed or missing = hard error, exit 2 — re-run
that batch), drops findings below `--min-impact` (default MEDIUM = keep HIGH+MEDIUM, exclude LOW; default
HIGH+MEDIUM), sorts by impact (HIGH→MEDIUM→LOW) then risk, writes
`rule-adherence-report.md` in the cwd, and prints the title block + ranked Summary table to stdout.
Relay that stdout; the file holds per-file detail — rule, exact bullet, line, impact/risk, offending
snippet, and a fix example when the fix is local. `unmatched_files` and meta-findings render
automatically; see `references/report-template.md` for the output shape.

After relaying, offer the LOW re-render (the run already graded every level — no re-review needed):

> Reported HIGH+MEDIUM. To include LOW (cosmetic) findings, re-render:
> python3 <skill>/scripts/render_report.py --findings .rule-review --map .rule-review/map.json --expect <batch-count> --min-impact LOW

Clean up only once the user has the report and declines the LOW re-render — the `.rule-review` dir must
survive for it: `rm -rf .rule-review` (safe to gitignore).

## Gotchas

- **Trust the mapping.** The most common failure is a subagent flagging a file against a rule never
  assigned to it (e.g. judging a UI file by an API rule). The script already scoped each file; the
  prompt tells the subagent to honor it.
- **A clean file is a valid result.** Empty `findings` is correct, not a sign the review failed.
- **This skill reviews; it does not edit.** Report findings and suggested fixes; the user decides what
  to change.
- Subagent-side judgment — don't manufacture findings, treat vague or contradictory rules as
  meta-findings (not per-file violations), never guess at fixes — lives in
  `references/rubric-and-schema.md`. Contradictory rules are a rules problem: point the user to
  `rule-context-builder` to reconcile them.
