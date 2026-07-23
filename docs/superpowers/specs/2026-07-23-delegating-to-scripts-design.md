# Design: `delegating-to-scripts` skill

Date: 2026-07-23
Status: approved design, pre-implementation

## Problem

Skills in this repo (and skills generally) re-derive mechanical work in prose on every run: parsing files, validating structure, counting, rendering reports. Each re-derivation costs tokens, adds latency, and produces run-to-run variance. The existing `skill-reviewer` mentions the compile-to-script principle in `references/token-economics.md` but only as background judgment guidance; nothing mechanically finds delegation opportunities or applies them.

Operating principle for the new skill: **"Always use a script unless Claude is needed specifically."**

## Decisions (settled with user)

1. **Standalone skill.** `skill-reviewer` stays a read-only general quality review; the two cross-link. One skill = one job.
2. **Flow: report → ask → write.** Skill produces a delegation report, the user picks which delegations to apply, then the skill implements only the chosen ones.
3. **Verification: smoke tests + fixture run.** Every generated script gets a `--help` check, exit-code checks, and one run against a small fixture before the rewritten SKILL.md ships.
4. **Architecture: script-assisted.** The skill dogfoods its own principle — deterministic extraction is a bundled script; only classification, script authoring, and prose rewriting are Claude work.

## Skill layout

Location: `skills/delegating-to-scripts/`

```
delegating-to-scripts/
├── SKILL.md                          (~200 lines)
├── scripts/
│   ├── inventory.py                  parse target skill → candidates JSON
│   └── smoke_test.py                 verify generated scripts via manifest
├── references/
│   ├── delegation-rubric.md          SCRIPT/CLAUDE/HYBRID criteria (with TOC)
│   └── script-conventions.md         interface rules for generated scripts (<60 lines)
└── evals/
    ├── evals.json                    3 evals (rule-audit schema)
    └── fixtures/
        ├── changelog-checker/        planted skill: 4 delegable steps + 1 CLAUDE step
        └── well-delegated/           negative control: already-delegated skill
```

## Workflow (SKILL.md body)

"Target skill" = the skill under review.

0. **Locate target.** Folder containing SKILL.md; pasted content saved to scratch dir first. No SKILL.md → decline (this skill reviews skills, not arbitrary markdown).
1. **Inventory (deterministic).** `python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json`. Compact summary to stdout, full JSON to `--out`. Body states explicitly: inventory extracts candidates; it does not classify.
2. **Classify (Claude judgment).** Read `references/delegation-rubric.md`, assign each step SCRIPT / CLAUDE / HYBRID with one-line reason, write decisions to `.delegation-review/classification.json` (plan-validate-execute: decision record on disk, not chat memory). Inline 6-line schema example including `proposed_script {name, interface, stdout, exit}`.
3. **Report (fixed template).** Verdict line plus per-step table: `# | Step (line) | Current form | Class | Why | Proposed script interface`. CLAUDE rows get no interface. SCRIPT/HYBRID rows must name concrete argv, stdout shape, exit codes. Steps already backed by an adequate script are marked `already delegated`.
4. **Gate.** AskUserQuestion multiSelect, one option per SCRIPT/HYBRID row; with more than 4 candidates, top 4 by payoff (estimated per-run token savings and variance reduction, judged from step length and how often the step runs) and Other accepts row numbers or `all` (rule-audit pattern). No pick → stop after report. Never write into the target without an explicit pick.
5. **Implement chosen delegations.** Per row: write script into `<target>/scripts/` following `references/script-conventions.md`; rewrite the SKILL.md step to an exact invocation (HYBRID becomes "run script → apply judgment to its output"); create a small fixture under `.delegation-review/fixtures/<script>/`; append an entry to `.delegation-review/manifest.json`.
6. **Smoke test.** `python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json`. On FAIL, fix the script (not the expectation, unless the expectation was wrong) and re-run until exit 0. Never claim done on a red smoke test.
7. **Wrap up.** Chat summary (scripts written, steps rewritten before→after, PASS line), suggest a follow-up `skill-reviewer` pass, remove `.delegation-review/`.

### Gotchas (in body)

- Mechanical verbs lie: "validate the approach with the user" is CLAUDE.
- A one-liner (`ls`, single `grep`) needs no bundled script; threshold is "hard to get right first try, or must run identically every invocation".
- Don't script steps that run once per skill *authoring* rather than per skill *run*.
- Don't delegate steps that read conversation context — a script can't see the conversation.
- Scripting a judgment step doesn't remove variance; it hides it behind false authority.
- A delegated step that dumps large output into context traded token cost for token cost — require `--out` for large output.

## scripts/inventory.py

- CLI: `inventory.py <target-skill-dir> [--out FILE]`. Accepts a SKILL.md path (uses parent).
- Exit codes: 0 inventory produced (even zero steps), 2 usage error / no SKILL.md. No exit 1 — extraction has no findings layer; severity is Claude's job.
- Parsing (line/regex based, stdlib + optional PyYAML; reuse `_split_frontmatter`/`_naive_yaml` approach from `skill-reviewer/scripts/audit.py`):
  - frontmatter (name, description length, unexpected keys)
  - heading tree (`^#{1,4} `)
  - steps from three origins: numbered list items, `Step/Phase N` headings (body truncated ~40 lines with `truncated: true`), checklist items
  - fenced code blocks with `looks_like_command` heuristic (lang bash/sh/console or first line matches `^(python3?|bash|sh|node|npx|uv|git|grep|find|mkdir|rm)\b`), attached to nearest step; orphans listed separately
  - `mechanical_verb_hints` word scan (parse, validate, count, check, extract, sort, format, render, diff, aggregate, collect, list, scan, verify, lint, convert) — documented as hints, not verdicts
  - existing `scripts/` inventory: lines, `mentioned_in_body`, `has_argparse`, `has_docstring`
  - `references/` and `assets/` inventory: lines, `mentioned_in_body`
- Output JSON: `target, frontmatter, body{lines, approx_tokens}, steps[{id, origin, heading_path, line_start, line_end, text, truncated, code_blocks, mechanical_verb_hints, mentions_existing_script}], orphan_code_blocks, scripts, references, assets, stats`.
- Honesty: zero steps → stdout summary says "workflow may be prose-only; read SKILL.md directly". Claude must read the target SKILL.md itself before classifying anything ambiguous.

## scripts/smoke_test.py

- CLI: `smoke_test.py <manifest.json> [--timeout SECS] [--only NAME] [--json]`.
- Exit codes: 0 all pass, 1 failures, 2 manifest missing/unreadable/schema-invalid (message names the missing field).
- Manifest written by Claude during step 5; schema documented in the script's header docstring. Per script: `path` (relative to `target_skill`), `invocations[{argv, cwd, expect_exit, expect_stdout_json, expect_stdout_contains}]`, `bad_invocation{argv, expect_exit_nonzero}`.
- Checks per script, each a named PASS/FAIL line:
  1. `exists`
  2. `help` — `--help` exits 0 with non-empty usage, `stdin=DEVNULL`, timeout (default 20s)
  3. `fixture-run` — exit code match, stdout JSON-parses if declared, contains declared substring; interactive scripts surface as FAIL `interactive-or-hung` (EOFError via DEVNULL stdin or timeout)
  4. `bad-args` — nonzero exit AND non-empty stderr
- Failure output: failing command, exit code, first ~10 stderr lines (verbose verifier so Claude can fix without manual re-runs).

## references/delegation-rubric.md

TOC at top. Sections:

1. **Core test:** "Would two different Claude runs produce meaningfully different output on this step? No → SCRIPT." Secondary test for close calls: "Could you write the unit test for this step's output right now? Yes → deterministic enough to script."
2. **Classifications:** SCRIPT (step is a function of its inputs; rewritten step is one exact command), CLAUDE (judgment/synthesis/conversation-dependent; stays prose), HYBRID (script prepares, Claude decides; in-repo precedent: audit.py's mechanical severity guess re-triaged by the agent).
3. **Delegable categories:** parsing/extraction, fixed-rule validation, file discovery/inventory, report rendering from structured data, diffing, aggregation/counting, format conversion.
4. **Claude-needed categories:** judgment and trade-offs, contextual classification, prose writing, design decisions and naming, conversation-reading, user negotiation (AskUserQuestion steps).
5. **Hybrid shapes:** extract-then-judge, judge-then-render (plan-validate-execute), script-gates-judgment.
6. **Gotchas** (mirror of the SKILL.md list plus rubric-specific ones).

## Frontmatter description

Third person, what + when, "pushy" trigger list, under 1024 chars. Triggers: "scriptify a skill", "compile skill steps into code", "which parts of this skill should be scripts", "make this skill more deterministic", "delegate this skill's steps to scripts", "my skill gives different output every run", reducing a skill's token cost or run-to-run variance. Negative triggers: NOT for general skill quality/triggering/token review with no intent to add scripts (use skill-reviewer); NOT for authoring a brand-new skill (use smart-skill-creator).

## Evals

Schema: rule-audit style (`skill_name`, `evals[]` with `id`, `name`, `prompt`, `expected_output`, `files`, `assertions[{text, type: structure|content}]`).

**Fixture A — `changelog-checker/`**: ~60-line SKILL.md, 5 numbered steps — (1) list .md files in changelogs/ [SCRIPT: discovery], (2) check each starts with `## vX.Y.Z — date` [SCRIPT: validation], (3) count entries per category [SCRIPT: aggregation], (4) write release narrative [CLAUDE: prose], (5) render summary table [SCRIPT: rendering]. Three changelog files; v1.2.0.md has a planted defect (missing version header) so generated checkers have a finding.

**Fixture B — `well-delegated/`**: small skill whose mechanical steps already invoke a bundled, documented `scripts/check.py`; remaining steps are genuine judgment. Nothing worth delegating.

1. **classify-and-report** (fixture A, report-only prompt): classification table produced, steps 1/2/3/5 SCRIPT, step 4 CLAUDE, nothing written into the fixture, stops at the gate.
2. **apply-and-smoke-test** (fixture A, apply-all prompt): ≥3 scripts written each supporting `--help`, SKILL.md steps rewritten to exact invocations, step 4 stays prose, header-check script flags v1.2.0.md, smoke test reported PASS.
3. **nothing-to-delegate** (fixture B): existing `check.py` acknowledged as already delegated, judgment steps classified CLAUDE, no new files. Guards against over-delegation — the skill must be able to say "no".

## Build order (verification per step)

1. Fixture A → valid mini-skill, defect planted.
2. `inventory.py` → vs fixture A (5 steps, hints on 1/2/3/5), vs real skill (`rule-audit`), vs non-skill dir (exit 2); `--help` and `--out` modes.
3. `delegation-rubric.md` → hand-classify fixture A using only the rubric; any gap means the rubric is incomplete.
4. `smoke_test.py` → manifest against known-good `skill-reviewer/scripts/audit.py` passes; wrong `expect_exit` fails; 3-line `input()` script fails `interactive-or-hung`; garbage manifest exits 2.
5. `script-conventions.md` → every rule checkable by smoke_test.py or visible in the audit.py exemplar; <60 lines.
6. `SKILL.md` → `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts` shows no high findings; body <300 lines; both scripts and all references mentioned in body.
7. Fixture B + `evals.json` → schema matches rule-audit shape; all fixture paths exist.
8. End-to-end dry run on a copy of fixture A (full flow through gate, apply-all, smoke green) and on fixture B (correct "nothing to delegate" outcome).

## Reuse (don't reinvent)

- `skills/skill-reviewer/scripts/audit.py` — script structure, exit-code house style (0/1/2), frontmatter parsing to reuse
- `skills/rule-audit/SKILL.md` — exact-invocation style, dot-dir outputs, AskUserQuestion 4-option cap pattern
- `skills/audit-refactor/SKILL.md` — pipeline body shape, schema-in-docstring convention, "Run them; don't reimplement them"
- `skills/rule-audit/evals/evals.json` — eval schema to replicate
- `skills/skill-reviewer/references/token-economics.md` — compile-to-script rationale the rubric builds on
