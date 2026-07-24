# Design: `delegating-to-scripts` skill

Date: 2026-07-23
Status: approved design, revised after adversarial review (rev 2), pre-implementation

## Problem

Skills in this repo (and skills generally) re-derive mechanical work in prose on every run: parsing files, validating structure, counting, rendering reports. Each re-derivation costs tokens, adds latency, and produces run-to-run variance. The existing `skill-reviewer` mentions the compile-to-script principle in `references/token-economics.md` but only as background judgment guidance; nothing mechanically finds delegation opportunities or applies them.

Operating principle for the new skill: **"Always use a script unless Claude is needed specifically."**

## Decisions (settled with user)

1. **Standalone skill.** `skill-reviewer` stays a read-only general quality review; the two cross-link. One skill = one job.
2. **Flow: report → ask → write.** Skill produces a delegation report, the user picks which delegations to apply, then the skill implements only the chosen ones.
3. **Verification: smoke tests + fixture run.** Every generated script gets a `--help` check, exit-code checks, and fixture runs before the rewritten SKILL.md ships.
4. **Architecture: script-assisted.** The skill dogfoods its own principle — deterministic extraction, cost profiling, and report rendering are bundled scripts; only classification, script authoring, and prose rewriting are Claude work.

Adversarial-review adoptions (rev 2): contract-first implementation order (manifest expectations before scripts, SKILL.md rewrite last and atomic); negative-data smoke requirement; target-eligibility guard; lossless-rewrite rule with diff; agent-runtime-tool rubric exclusion; inventory refocused as anchor generator + cost profiler; terse consumed classification.json; HYBRID/trap fixtures and partial-selection eval.

## Skill layout

Location: `skills/delegating-to-scripts/`

```
delegating-to-scripts/
├── SKILL.md                          (~200 lines)
├── scripts/
│   ├── inventory.py                  anchors + cost profile + script interface audit → JSON
│   ├── render_report.py              classification.json + inventory.json → report table
│   └── smoke_test.py                 verify generated scripts via manifest
├── references/
│   ├── delegation-rubric.md          SCRIPT/CLAUDE/HYBRID criteria (with TOC)
│   └── script-conventions.md         interface rules for generated scripts (<60 lines)
└── evals/
    ├── evals.json                    4 evals (rule-audit schema)
    └── fixtures/
        ├── changelog-checker/        planted skill: SCRIPT/CLAUDE/HYBRID/trap steps
        └── well-delegated/           negative control: already-delegated skill
```

## Workflow (SKILL.md body)

"Target skill" = the skill under review.

0. **Locate target + eligibility guard.** Folder containing SKILL.md; pasted content saved to scratch dir first. No SKILL.md → decline (this skill reviews skills, not arbitrary markdown). Target must be writable, user-owned, and outside plugin/cache paths (`~/.claude/plugins/`, plugin cache dirs — scripts written there are clobbered on plugin update); ineligible target → degrade to report-only mode (steps 1-4), offer copy-to-project. Record whether target SKILL.md is git-clean; if dirty, warn and copy it to `.delegation-review/SKILL.md.orig` before any later rewrite.
1. **Inventory (deterministic).** `python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json`. Stdout: counts and hints only (no step text). Then read the target SKILL.md directly — the inventory provides anchors and numbers, not the territory.
2. **Classify (Claude judgment).** Read `references/delegation-rubric.md`, assign each inventoried step SCRIPT / CLAUDE / HYBRID / DEAD, write `.delegation-review/classification.json`. Terse by design: reference inventory step ids, never duplicate step text. Per step: `{id, class, why (one clause), proposed_script {name, interface, stdout, exit} | null}`. DEAD = step that should be deleted, not scripted (stale, duplicative) — reported for awareness, routed to a `skill-reviewer` follow-up, never auto-deleted. Steps already backed by an adequate script (per inventory's interface audit) are marked `already delegated`.
3. **Report (rendered, not hand-written).** `python3 <skill>/scripts/render_report.py .delegation-review/classification.json .delegation-review/inventory.json` → fixed-template markdown: verdict line plus per-step table `# | Step (line) | Current form | Tokens | Class | Why | Proposed script interface`. CLAUDE/DEAD rows get no interface. SCRIPT/HYBRID rows carry concrete argv, stdout shape, exit codes. Paste output to chat verbatim.
4. **Gate.** AskUserQuestion multiSelect, one option per SCRIPT/HYBRID row; with more than 4 candidates, top 4 ranked by inventory's per-step token counts (arithmetic, not judgment) and Other accepts row numbers or `all` (rule-audit pattern). No pick → stop after report. Never write into the target without an explicit pick. Offer as checkbox: keep verification residue (fixtures + manifest) in `<target>/scripts/tests/` for future regression runs (default: off).
5. **Contract first.** For each chosen row, before writing any script: derive manifest expectations from the step's *semantics* (what the prose says the step must catch), and create fixtures under `.delegation-review/fixtures/<script>/` containing at least one passing and one failing example for every validation/check script. Append entries to `.delegation-review/manifest.json`: good invocation(s) plus a bad-data invocation asserting the finding (nonzero exit or finding substring) plus a bad-args invocation. Steps 4-5 re-read `classification.json` from disk — do not work from chat memory.
6. **Implement scripts.** Write each script into `<target>/scripts/` following `references/script-conventions.md`, built to pass the pre-written manifest. Name collision with an existing file → ask, never silently overwrite. Target SKILL.md untouched in this step.
7. **Smoke test.** `python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json`. On FAIL, fix the script (not the expectation, unless the expectation misread the step's semantics) and re-run until exit 0. Red smoke → stop; target SKILL.md still pristine, `.delegation-review/` preserved for resumption. Never claim done on red.
8. **Rewrite SKILL.md (atomic, last).** Only after green: rewrite all chosen steps in one pass. Lossless rule: replace only the mechanical instruction with the exact invocation; preserve rationale, branching, and gotcha sentences verbatim (HYBRID → "run script → apply judgment to its output" keeping the judgment prose). Show the unified diff in chat.
9. **Wrap up.** Chat summary: scripts written, diff shown, smoke PASS line, DEAD steps flagged for skill-reviewer follow-up. If residue option chosen, move fixtures + manifest to `<target>/scripts/tests/` and note the smoke command in the target body (enables idempotent re-runs); else remove `.delegation-review/` — only on a fully green run.

### Gotchas (in body)

- Mechanical verbs lie: "validate the approach with the user" is CLAUDE.
- Steps invoking agent-runtime tools (MCP, WebFetch, AskUserQuestion, subagent dispatch, anything permission-gated) are CLAUDE or HYBRID, never pure SCRIPT — a script reimplementation loses auth, permissions, and rate handling.
- A one-liner (`ls`, single `grep`) needs no bundled script; threshold is "hard to get right first try, or must run identically every invocation".
- Don't script steps that run once per skill *authoring* rather than per skill *run*.
- Don't delegate steps that read conversation context — a script can't see the conversation.
- Scripting a judgment step doesn't remove variance; it hides it behind false authority.
- A delegated step that dumps large output into context traded token cost for token cost — require `--out` for large output.
- Some steps deserve deletion, not delegation — classify DEAD, don't force a script onto a step that shouldn't exist.

## scripts/inventory.py

Role: anchor generator + cost profiler + existing-script interface auditor. NOT a step-text extractor — Claude reads the target SKILL.md itself (workflow step 1); regex step-splitting must not be load-bearing.

- CLI: `inventory.py <target-skill-dir> [--out FILE]`. Accepts a SKILL.md path (uses parent).
- Exit codes: 0 inventory produced (even zero steps), 2 usage error / no SKILL.md. No exit 1 — extraction has no findings layer; severity is Claude's job.
- Produces (line/regex based, stdlib + optional PyYAML; reuse `_split_frontmatter`/`_naive_yaml` from `skill-reviewer/scripts/audit.py`):
  - frontmatter (name, description length, unexpected keys)
  - step anchors from three origins: numbered list items, `Step/Phase N` headings, checklist items — id, origin, heading_path, line range, `approx_tokens` (per-step token estimate: drives gate payoff ranking)
  - per-step hints: `mechanical_verb_hints` word scan (parse, validate, count, check, extract, sort, format, render, diff, aggregate, collect, list, scan, verify, lint, convert), `agent_tool_mentions` (`mcp__`, WebFetch, AskUserQuestion, Task/Agent dispatch), `mentions_existing_script`, attached fenced code blocks with `looks_like_command` heuristic — all documented as hints, not verdicts
  - existing `scripts/` interface audit: lines, `mentioned_in_body`, `has_argparse`, `has_docstring`, live `--help` probe (exit 0 + non-empty usage, `stdin=DEVNULL`, short timeout) → feeds the `already delegated` verdict
  - `references/` and `assets/` inventory: lines, `mentioned_in_body`
- Output JSON: `target, frontmatter, body{lines, approx_tokens}, steps[{id, origin, heading_path, line_start, line_end, approx_tokens, code_blocks, mechanical_verb_hints, agent_tool_mentions, mentions_existing_script}], orphan_code_blocks, scripts[{path, lines, mentioned_in_body, has_argparse, has_docstring, help_ok}], references, assets, stats`. Step text NOT included beyond a ~80-char snippet for table labels.
- Honesty: zero steps → stdout summary says "workflow may be prose-only; read SKILL.md directly".

## scripts/render_report.py

- CLI: `render_report.py <classification.json> <inventory.json> [--out FILE]`. Joins by step id; markdown report (verdict line + table) to stdout.
- Exit codes: 0 rendered, 1 classification references unknown step ids or missing required fields (names them — doubles as classification.json validator), 2 usage/unreadable input.
- Rationale: report table is "rendering from structured data" — the skill's own delegable category; also validates classification.json so the artifact has both a consumer and a validator.

## scripts/smoke_test.py

- CLI: `smoke_test.py <manifest.json> [--timeout SECS] [--only NAME] [--json]`.
- Exit codes: 0 all pass, 1 failures, 2 manifest missing/unreadable/schema-invalid (message names the missing field).
- Manifest written by Claude during workflow step 5 (before scripts exist — contract first); schema documented in the script's header docstring. Per script: `path` (relative to `target_skill`), `invocations[{argv, cwd, expect_exit, expect_stdout_json, expect_stdout_contains}]`, `bad_data_invocation` (required for validation/check scripts: run against the failing fixture, assert nonzero exit or finding substring), `bad_invocation{argv, expect_exit_nonzero}`.
- Checks per script, each a named PASS/FAIL line:
  1. `exists`
  2. `help` — `--help` exits 0 with non-empty usage, `stdin=DEVNULL`, timeout (default 20s)
  3. `fixture-run` — exit code match, stdout JSON-parses if declared, contains declared substring; interactive scripts surface as FAIL `interactive-or-hung` (EOFError via DEVNULL stdin or timeout)
  4. `bad-data` — the failing fixture must produce the declared finding (proves the logic discriminates, not just that the interface works)
  5. `bad-args` — nonzero exit AND non-empty stderr
- Manifest schema check rejects a validation/check script entry lacking `bad_data_invocation`.
- Failure output: failing command, exit code, first ~10 stderr lines (verbose verifier so Claude can fix without manual re-runs).

## references/delegation-rubric.md

TOC at top. Sections:

1. **Core test:** "Would two different Claude runs produce meaningfully different output on this step? No → SCRIPT." Secondary test for close calls: "Could you write the unit test for this step's output right now? Yes → deterministic enough to script."
2. **Classifications:** SCRIPT (step is a function of its inputs; rewritten step is one exact command), CLAUDE (judgment/synthesis/conversation-dependent; stays prose), HYBRID (script prepares, Claude decides; in-repo precedent: audit.py's mechanical severity guess re-triaged by the agent), DEAD (step should be deleted, not scripted — flag only, route to skill-reviewer).
3. **Delegable categories:** parsing/extraction, fixed-rule validation, file discovery/inventory, report rendering from structured data, diffing, aggregation/counting, format conversion.
4. **Claude-needed categories:** judgment and trade-offs, contextual classification, prose writing, design decisions and naming, conversation-reading, user negotiation (AskUserQuestion steps), **agent-runtime-tool steps** (MCP, WebFetch, subagent dispatch, permission-gated tools — never pure SCRIPT; at most HYBRID around the tool call).
5. **Hybrid shapes:** extract-then-judge, judge-then-render (plan-validate-execute), script-gates-judgment.
6. **Gotchas** (mirror of the SKILL.md list plus rubric-specific ones).

## Frontmatter description

Third person, what + when, "pushy" trigger list, under 1024 chars. Triggers: "scriptify a skill", "compile skill steps into code", "which parts of this skill should be scripts", "make this skill more deterministic", "delegate this skill's steps to scripts", "my skill gives different output every run", reducing a skill's token cost or run-to-run variance. Negative triggers: NOT for general skill quality/triggering/token review with no intent to add scripts (use skill-reviewer); NOT for authoring a brand-new skill (use smart-skill-creator).

## Evals

Schema: rule-audit style (`skill_name`, `evals[]` with `id`, `name`, `prompt`, `expected_output`, `files`, `assertions[{text, type: structure|content}]`).

**Fixture A — `changelog-checker/`**: ~70-line SKILL.md, 7 numbered steps — (1) list .md files in changelogs/ [SCRIPT: discovery], (2) check each starts with `## vX.Y.Z — date` [SCRIPT: validation], (3) count entries per category [SCRIPT: aggregation], (4) write release narrative [CLAUDE: prose], (5) render summary table [SCRIPT: rendering], (6) check category tags against the allowed list, then judge whether `misc` entries fit an existing category [HYBRID: extract-then-judge], (7) "verify entries are clearly written" [trap: `verify` hint, CLAUDE class]. Three changelog files; v1.2.0.md has a planted defect (missing version header) so generated checkers have a bad-data fixture in the wild.

**Fixture B — `well-delegated/`**: small skill whose mechanical steps already invoke a bundled, documented `scripts/check.py`; remaining steps are genuine judgment. Nothing worth delegating.

1. **classify-and-report** (fixture A, report-only prompt): rendered table produced, steps 1/2/3/5 SCRIPT, step 6 HYBRID, steps 4/7 CLAUDE (7 despite the `verify` hint), nothing written into the fixture, stops at the gate.
2. **apply-and-smoke-test** (fixture A, apply-all prompt): scripts written each supporting `--help`, manifest includes bad-data invocations, header-check script flags v1.2.0.md, SKILL.md steps rewritten to exact invocations only after smoke PASS, steps 4/7 stay prose, step 6 keeps its judgment sentence.
3. **nothing-to-delegate** (fixture B): existing `check.py` acknowledged as already delegated (help_ok from inventory audit), judgment steps classified CLAUDE, no new files. Guards against over-delegation — the skill must be able to say "no".
4. **partial-selection** (fixture A, prompt pre-selects "apply only steps 1 and 3"): exactly those two scripts exist, step 2's prose byte-identical, diff shown covers only steps 1 and 3. Exercises the gate's selection path.

## Build order (verification per step)

1. Fixture A → valid mini-skill, defect planted, HYBRID + trap steps present.
2. `inventory.py` → vs fixture A (7 step anchors, token counts, hints incl. trap's `verify`), vs real skill (`rule-audit` — interface audit shows help_ok for its scripts), vs non-skill dir (exit 2); `--help` and `--out` modes.
3. `delegation-rubric.md` → hand-classify fixture A using only the rubric; must resolve the HYBRID and trap steps correctly or the rubric is incomplete.
4. `render_report.py` → valid classification+inventory renders table; classification with unknown step id exits 1 naming it.
5. `smoke_test.py` → manifest against known-good `skill-reviewer/scripts/audit.py` passes; wrong `expect_exit` fails; missing `bad_data_invocation` on a check script rejected at schema stage; 3-line `input()` script fails `interactive-or-hung`; garbage manifest exits 2.
6. `script-conventions.md` → every rule checkable by smoke_test.py or visible in the audit.py exemplar; <60 lines.
7. `SKILL.md` → `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts` shows no high findings; body <300 lines; all three scripts and all references mentioned in body.
8. Fixture B + `evals.json` → schema matches rule-audit shape; all fixture paths exist.
9. End-to-end dry run on a copy of fixture A (full flow through gate, apply-all, contract-first order observed, smoke green before rewrite, diff shown) plus partial-selection run, plus fixture B ("nothing to delegate").

## Reuse (don't reinvent)

- `skills/skill-reviewer/scripts/audit.py` — script structure, exit-code house style (0/1/2), frontmatter parsing to reuse
- `skills/rule-audit/SKILL.md` — exact-invocation style, dot-dir outputs, AskUserQuestion 4-option cap pattern
- `skills/audit-refactor/SKILL.md` — pipeline body shape, schema-in-docstring convention, "Run them; don't reimplement them", red-before-green safeguard rule (a check is only a safeguard if it currently fails)
- `skills/rule-audit/evals/evals.json` — eval schema to replicate
- `skills/skill-reviewer/references/token-economics.md` — compile-to-script rationale the rubric builds on
