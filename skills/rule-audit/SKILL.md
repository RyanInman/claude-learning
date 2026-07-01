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
computed deterministically by `scripts/map_rules.py`, never guessed. The review can target a subset of
rules (Step 1 asks which); `map_rules.py --rules` then restricts the mapping to that selection so only
chosen rules fan out. The script groups files with an
identical rule-set, then splits each group by total source bytes so no subagent gets an oversized load
— one **batch** (one review subagent) per resulting group. Each subagent is a cheap `haiku` model that
reads its files in its own context, writes findings as JSON, and validates that JSON with
`scripts/validate_findings.py` before returning — so raw code stays out of the main conversation and a
malformed file is caught where the subagent can still fix it, not at render time. A second `haiku` pass
then adversarially reviews each batch's JSON (Step 3.5), challenging every finding against the rule text
and source to strip false positives and mis-citations before they reach the report — the reviewer is a
fresh agent, not the one that wrote the findings, so it has no stake in defending them.
`scripts/render_report.py` then aggregates the reviewed files into two ranked reports, so sorting and
formatting stay deterministic (same fan-out/fan-in shape as `pattern-extractor`).

## Step 0 — Exit plan mode if active

This skill is execution-only (map → fan-out → render). There are no design decisions to make before
running. If plan mode is active, call `ExitPlanMode` immediately — do not write a plan file, do not
ask for approval. Then proceed to Step 1.

## Step 1 — Scope the review (ask first)

Confirm scope before running anything — a vague "check our rules" must not silently become a full-repo
audit spawning many subagents. Three things to settle: **which rules**, **what file set** (staged vs
audit), and — for global rules — **how wide**.

### 1a — Discover the rules

Run once in main context to get the rule inventory (skips the file universe and batching):

```bash
python3 <skill>/scripts/map_rules.py --mode audit --list-rules
```

It prints `global_rules`, `path_scoped_rules` (with globs), and `notes`. If `notes` reports no
`.claude/rules/` was found (or the dir is empty) → there is nothing to check; tell the user and stop.

### 1b — Ask which rules to audit

Unless the user already named specific rules, ask with a single `AskUserQuestion` (multiSelect) — one
option per discovered rule: label = filename, description = `global — applies to all files` or its
globs. Invite "select all listed to audit everything." `AskUserQuestion` caps at 4 options: with >4
rules, list the first 4 as options and have the question text note the total count and that `Other`
accepts additional rule names (or `all`). Pass the chosen filenames to `--rules` (comma-separated) in
Step 2; an unknown name there surfaces as a `note`, not a crash.

### 1c — Pick the file set (staged vs audit)

- **staged** — files in `git diff --cached`; cheap pre-commit / pre-PR check. Default when they
  imply "before I commit/push" or "my changes".
- **audit** — files matched by rule globs. Default for "audit", "sweep the repo", "are we following
  our rules".

### 1d — Global-rule scope guard

A global rule matches *every* file, so auditing one over a full `audit` universe fans out across the
whole repo. If the selection includes a global rule **and** mode is `audit`, do not fan out repo-wide
by default — ask (via `AskUserQuestion`) to narrow: a `--path <subdir>`, switch to `--mode staged`, or
explicit confirmation of a full-repo audit. Path-scoped rules self-limit via their globs and skip this
guard. Narrowing is opt-in; a full-repo audit remains a valid explicit choice.

Do not ask about impact threshold here. Subagents grade every level regardless, and Step 4 always
writes both a HIGH+MEDIUM report and a full HIGH+MEDIUM+LOW report — no threshold decision needed.

**Session hygiene:** a full-repo audit fans out 60+ batches twice and is context-heavy for the main
session. Run it in its own fresh session (`/clear` first; do not chain it after an unrelated task). Keep
per-wave dispatch narration terse — the dispatch prompts are short by design; do not re-summarize each
wave. This keeps the main context small and avoids accuracy decay over a long run.

## Step 2 — Map rules to files

Run once in main context. `--out` writes the full JSON to `.rule-review/map.json` (read back by
`render_report.py` in Step 4 for the header, `unmatched_files`, and rule count) and prints a compact
summary — `batches`, `notes`, and counts — to stdout, keeping the per-file `assignments` array out of
the conversation:

```bash
mkdir -p .rule-review
python3 <skill>/scripts/map_rules.py --mode <staged|audit> [--path <subdir>] [--max-batch-bytes N] --rules <selected> --out .rule-review/map.json > /dev/null
```

`--rules <selected>` is the comma-separated filenames chosen in Step 1b; omit it only when the user
opted to audit every rule. A filtered `map.json` carries just the selected rules, so subagents and the
rendered `Rules: N` count follow the selection with no further wiring.

The `> /dev/null` suppresses stdout — all data is in `--out map.json` and the compact summary can
exceed 40KB on large repos, bloating the main context with partial (truncated) data.

It discovers `.claude/rules/*.md`, classifies each as global or path-scoped, resolves the file universe
(`git diff --cached` for staged; tracked + untracked-not-ignored for audit), and emits `assignments`,
`batches`, `unmatched_files`, and `notes`. Each batch carries `n_files` and `bytes`; a same-ruleset
group over `--max-batch-bytes` (default 80000) is split across multiple batches so each subagent's load
stays bounded. Act on `notes`:

- "No `.claude/rules/` found" → nothing to check; tell the user and stop.
- "No staged files" → tell the user, suggest `--mode audit`, stop.
- "Audit universe is N files" (large) → offer to narrow with `--path` before fanning out.
- "Requested rule '…' not found" → a `--rules` name didn't match a rule file; re-check the selection.

## Step 3 — Fan out one subagent per batch

For each entry in `batches`, spawn a review subagent in parallel on the `haiku` model (pass
`model: haiku` to the Agent tool — the work is mechanical pattern-matching against given rules, so the
cheap model is enough and keeps a wide fan-out affordable; cap ~10 concurrent — see
`superpowers:dispatching-parallel-agents`). Number batches 0, 1, 2, …; each writes to
`.rule-review/batch-<N>.json`. The fixed prompt body lives in `assets/review_prompt.md`; the subagent
self-fetches both its rule list and its file list from `map.json` (nothing is inlined by the main agent).
Use this dispatch template:

```
Rule-audit review batch <N>. ROOT=<root>. SKILL=<skill>. Read and follow <skill>/assets/review_prompt.md
exactly, resolving <ROOT>=<root>, <N>=<N>, <SKILL>=<skill>. Your rules and file list are in
<ROOT>/.rule-review/map.json under batches[<N>]. Return only the one-line count.
```

**Do not embed file lists inline in the prompt.** The map.json stdout is often truncated at ~2KB in the
tool preview, making inline lists unreliable. The self-fetching `python3 -c` command in the template lets
each subagent read its own authoritative file list from disk.

Dispatch all waves without waiting for prior-wave completions — the 10-concurrent cap is a rate limit,
not a serialization requirement. Send all waves, then wait for ALL batch notifications before Step 3.5.

Each subagent writes the `file_findings` / `meta` JSON from `references/rubric-and-schema.md`, confirms
it passes `validate_findings.py`, and returns only counts — findings never enter the main context, and a
malformed file is caught here (where the subagent still has the code in context) rather than at render.

## Step 3.5 — Adversarially review each batch (haiku)

A review subagent grading its own work has an incentive to over-report (a flagged finding looks like
diligence). So after a batch's `batch-<N>.json` is written, spawn a **separate** `haiku` subagent — never
the one that wrote it — to attack that JSON: every finding is guilty of being a false positive until the
rule text and source prove otherwise. Spawn one reviewer per batch as its file lands; same ~10-concurrent
cap. Each reviewer reads only its batch's JSON + that batch's rules + the cited files (all on disk), so
the critique stays out of main context. The reviewer corrects `batch-<N>.json` **in place** and
re-validates it, so Step 4 renders the reviewed set with no extra wiring.

The fixed prompt body lives in `assets/adversarial_prompt.md`; the subagent self-fetches the applicable
rule list from `map.json`. Use this dispatch template:

```
Rule-audit adversarial review batch <N>. ROOT=<root>. SKILL=<skill>. Read and follow
<skill>/assets/adversarial_prompt.md exactly, resolving <ROOT>=<root>, <N>=<N>, <SKILL>=<skill>. The
applicable rules are in <ROOT>/.rule-review/map.json under batches[<N>]['rules']. Return only the one-line count.
```

Wait for ALL reviewer notifications before Step 4. A reviewer that empties a batch to zero findings is a
valid outcome (the original subagent over-reported); the file must still exist and validate.

## Step 4 — Render the reports (deterministic)

Once every batch has written its file, render — do not collect, sort, or format by hand:

```bash
python3 <skill>/scripts/render_report.py --findings .rule-review --map .rule-review/map.json --expect <batch-count> [--reports-dir reports]
```

It re-validates every findings file against the schema (malformed or missing = hard error, exit 2 —
re-run that batch), sorts by impact (HIGH→MEDIUM→LOW) then risk, and writes **two** reports to
`reports/`: `rule-adherence-high-medium.md` (HIGH+MEDIUM only — the actionable set) and
`rule-adherence-with-low.md` (adds the LOW/cosmetic findings). Both come from the same graded JSON, so
no re-review is needed. It prints the HIGH+MEDIUM title block + ranked Summary table plus both file
paths to stdout. Relay that stdout; the files hold per-file detail — rule, exact bullet, line,
impact/risk, offending snippet, and a fix example when the fix is local. `unmatched_files` and
meta-findings render automatically; see `references/report-template.md` for the output shape.

Clean up once the user has the reports: `rm -rf .rule-review` (safe to gitignore). The `reports/` dir is
the durable output — leave it.

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
