---
name: auditing-test-harnesses
description: >-
  Audits a codebase's testing and validation harness across five tiers (static, unit,
  integration, e2e, evals), fans out one sub-agent per tier, scores seven design dimensions
  1-10, and writes a dated report with per-tier current → target → action recommendations.
  Use whenever the user asks to audit, review, grade, or score a test suite, test setup,
  testing strategy, or validation harness; asks "how good are our tests", "what testing are
  we missing", "is our CI gating enough", or "is this repo safe for AI agents to change";
  wants a testing remediation roadmap for an existing codebase; or wants a testing strategy
  for a greenfield project, even if they never say "harness". Do NOT use to build or change
  tests - use scaffolding-integration-tests for API/service harnesses and
  scaffolding-e2e-tests for browser or mobile UI harnesses. Do NOT use to debug one failing
  test.
---

# Auditing test harnesses

Audit a system's testing and validation harness. Produce a scored report with one
independently actionable recommendation block per tier. The audit changes no code and writes
no plans, because the report is the artifact the user plans from.

Read these files at the step that names them:

- `references/rubric.md` holds the inventory taxonomy, tier weights, the seven dimensions, the
  structural-versus-transient rule, the AI layer, and brownfield sequencing.
- `references/tier-static.md`, `references/tier-unit.md`, and `references/tier-evals.md` state
  their tier's golden state directly.
- `references/tier-integration.md` and `references/tier-e2e.md` are audit lenses. The golden
  state for those tiers lives in the sibling skills `scaffolding-integration-tests` and
  `scaffolding-e2e-tests`.

Work from these files. Do not invent dimensions, tiers, or targets, because audits of the same
repo must stay comparable over time.

## Step 0: Before starting

Confirm these facts before running anything:

1. **Scope.** Is the target one repo, one monorepo package, or several repos?
2. **Mode.** Brownfield (the default) audits what exists. Greenfield applies when no harness
   exists or the user says so.
3. **Production access.** Do any test commands or env files point at production or a prod
   copy? If they do, exclude those commands from every run.

Mine the conversation and the repo for the answers first. Ask the user only when scope is
ambiguous, because an audit of the wrong package wastes the whole fan-out. When all three are
known, proceed without asking.

For several repos, or a monorepo with several deployable apps, run Phases 1-3 once per repo or area. Then merge the
syntheses into one report.

## Phase 1: Preflight and skim (orchestrator)

1. Find the canonical test commands in package scripts, AGENTS.md, and CI config.
2. Run the cheapest command. Record the baseline as green or red first, because a red baseline
   reframes every later observation.
3. Record repo state as context, never as a finding: branch, dirty files, in-flight migrations.
4. Skim the tree and decide which tiers are in scope. Map each applicable taxonomy family in
   `references/rubric.md` Part 1 to its tier.
5. Mark evals N/A when the repo has no probabilistic (LLM or model-scored) features. Spread its
   15% weight across the other tiers in proportion.

Analyse no tier in this phase. Every finding and score input must come from a tier sub-agent,
because an orchestrator that audits one tier inline gives that tier uneven depth.

## Phase 2: Fan out (orchestrator dispatches)

Dispatch one `general-purpose` sub-agent per in-scope tier, all in one message so they run in
parallel. That agent type has the Skill tool and every file tool the brief needs. Give each
sub-agent the brief below with the slots filled. Wait for all of them, then collect each sub-agent's
returned JSON.

The static sub-agent also owns the operability-affordances family, because that family is an
artifact sweep (docs, scripts, seeds, tooling) with no tier of its own.

In greenfield mode, every tier is a scaffold target. Each sub-agent writes scaffold
recommendations against the same golden state instead of auditing existing tests.

### Tier sub-agent brief

```text
You own the full audit of the <TIER> tier for <SCOPE> (mode: <brownfield|greenfield>).
Preflight baseline: <green|red, command, duration>. Repo state: <branch, dirty files, migrations>.
Excluded commands (prod or prod-copy targets): <list | none>. Never run these.

Read <SKILL_DIR>/references/tier-<TIER>.md and <SKILL_DIR>/references/rubric.md
(Part 1 row for your tier, Part 3 dimensions and the structural rule, Part 4 AI layer,
Part 5 brownfield sequencing, Part 6 report contract).
<static tier only: you also own the "Operability affordances" family in rubric.md Part 1.>

1. Ground against golden state.
   - static, unit, evals: the tier doc states the target. Work from it.
   - integration, e2e: invoke the skill named in the tier doc with the Skill tool, args
     "evaluation-only". If the Skill tool is unavailable, read <SKILLS_ROOT>/<skill>/SKILL.md
     and follow its evaluation-only path. Run its discover and plan phases against this repo, then stop before
     any implementation. Treat that plan, and the ladder or matrix it cites, as golden-state
     evidence. Cite the skill; do not restate its content.
2. Inventory your families for presence, design, and cadence, with file-path evidence.
   Record a missing family as a finding, not a blank.
3. Run your tier's runnable suites and time them. Record cold-start friction as operability
   evidence. Never flip a live-tier flag: inventory live suites by their files. Never run a
   suite against production or prod-copy data.
4. Classify every finding structural or transient (rubric.md Part 3). Score only structural
   findings. Trace each transient to the structural gap that permitted it, or mark it one-off.
   Record accepted risks aside with their existing mitigation, unscored.
5. Write your full evidence and reasoning to <WORKING_DOC_DIR>/<TIER>-audit.md.
6. Return only this JSON, no prose:
   { "tier", "docPath", "currentState": [], "structuralFindings": [], "transients": [],
     "acceptedRisks": [], "recommendations": [], "dimensionEvidence": {}, "coverageGaps": [] }
   - Each recommendation: { "current", "target", "action", "flag": "engineering"|"owner-decision" }.
     Cite the tier doc in each action, and route the HOW to the skill that owns it.
   - dimensionEvidence: exactly one line for each of the seven dimensions.
   - Every claim cites a file or command output, or goes in coverageGaps.
```

Set `<WORKING_DOC_DIR>` to `.artifacts/reports/YYYY-MM-DD-validation-audit-tiers/`. Set
`<SKILLS_ROOT>` to the parent folder of this skill, and `<SKILL_DIR>` to this skill's absolute
base directory. Fill the excluded-command list from Step 0 item 3. For several repos or areas,
add an `<area>/` segment to `<WORKING_DOC_DIR>`, so one run does not overwrite another's docs.

## Phase 3: Synthesize (orchestrator)

1. Build each of the seven dimension scores from the tiers' `dimensionEvidence`. Give one
   justified score per dimension across all tiers. Re-run no tier analysis here.
2. Dedupe findings that recur across tiers. Group structural findings by shared root cause.
3. Order findings, transients, accepted risks, and recommendation blocks by tier weight:
   integration, unit, e2e, static, evals.
4. Write the report to `.artifacts/reports/YYYY-MM-DD-investigation-validation-audit.md` with
   the template below. Link each tier's working doc.
5. End by telling the user to pick the tier blocks they accept and run the `brainstorming`
   skill on each one, one plan per tier or subset. Write no plans yourself.

## Report template

Use this exact template. Audits of the same repo must diff cleanly, so the section shapes must
not change between runs.

```markdown
# Validation audit - <scope> - <YYYY-MM-DD>

## Summary

- Scope: <repo / package / repos>
- Mode: <brownfield | greenfield>
- Verdict: <two sentences>
- Baseline: <green | red> (`<command>`, <duration>)
- Mean score: <x.x>/10

## Current-state table

| Tier | Present | Design | Cadence |
| --- | --- | --- | --- |
| Static | ... `path` | ... | ... |
| Unit | | | |
| Integration | | | |
| End-to-end | | | |
| Probabilistic (evals) | | | |
| Operability affordances | | | |

## Scores

| Dimension | Score /10 | Why |
| --- | --- | --- |
| Tier breadth | | |
| Fidelity | | |
| Speed and feedback | | |
| Isolation and determinism | | |
| CI gating and cadence | | |
| AI-runnability and operability | | |
| Conventions and maintainability | | |
| **Mean** | **x.x** | |

## Structural findings

1. **<root cause>** - <finding> (`path`, `path`)

## Transient observations

- <observation> - expression of finding <N> | genuinely one-off

## Accepted risks

- <risk> - mitigation: <existing mitigation>

## Per-tier recommendations

### Integration (30%) - [working doc](<path>)

| # | Current | Target | Action | Flag |
| --- | --- | --- | --- | --- |
| 1 | | | Run `scaffolding-integration-tests` (<topic>; tier-integration.md) | engineering |

### Unit (20%) - [working doc](<path>)
### E2E (20%) - [working doc](<path>)
### Static (15%) - [working doc](<path>)
### Evals (15% | N/A) - [working doc](<path>)

## Coverage gaps

- <what was not assessed> - <why: suite not runnable | credentials absent | area not read>
```

Flag a row `owner-decision` when it spends money, sets policy, or sets cadence budget, because
those calls belong to the owner. Flag every other row `engineering`.

## Example

A recommendation row from a brownfield NestJS repo whose integration suite shares one dev
database:

```markdown
| # | Current | Target | Action | Flag |
| --- | --- | --- | --- | --- |
| 1 | Integration suite runs against shared `dev` Postgres; cleanup deletes by email prefix (`test/cleanup.ts`) | Rung 1: fresh state per run for the merge-gating suite | Run `scaffolding-integration-tests` (DB isolation ladder, rung 0 → 1; tier-integration.md) | engineering |
| 2 | `summary.live.test.ts` has no schedule; runs only by hand | Scheduled live run with results published | Run `scaffolding-integration-tests` (live tier; tier-integration.md); schedule costs OpenAI tokens | owner-decision |
```

## Gotchas

- Score design, not weather. A red test today is transient unless the design makes it
  reproducible for any developer. Scoring transients punishes a repo for being mid-change.
- Tier weights set audit emphasis, remediation order, and doc depth only. Never multiply
  dimension scores by weights, because the dimensions already span tiers.
- A backend black-box suite named `test:e2e` belongs to the integration tier (system tier).
  Judge a suite by what it drives, not by its script name.
- Audit operability from artifacts only. Never claim to have assessed agent behaviour you did
  not observe.
- A presence gap outranks a polish gap. A missing tier comes before a suboptimal one in every
  block.
- Never recommend a blanket coverage percentage, because it triggers mass low-value test
  generation. Follow the sequencing in `references/rubric.md` Part 5.
- Sub-agents that run the sibling scaffold skills must pass `evaluation-only`. Without it, the
  scaffold skill proceeds toward implementation and the audit changes code.
