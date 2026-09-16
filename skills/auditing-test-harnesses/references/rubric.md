# Validation rubric

This file defines what to sweep, how to score, and how to package the result. Every golden state an audit cites comes from a `tier-*.md` doc or a sibling scaffold skill.

## Contents

- [Part 1 - Inventory taxonomy](#part-1---inventory-taxonomy)
- [Part 2 - Tier weights](#part-2---tier-weights)
- [Part 3 - Seven dimensions](#part-3---seven-dimensions)
- [Part 4 - The AI layer](#part-4---the-ai-layer)
- [Part 5 - Brownfield sequencing](#part-5---brownfield-sequencing)
- [Part 6 - Report contract](#part-6---report-contract)

## Part 1 - Inventory taxonomy

Sweep all six families. Record a missing family as a finding, not a blank. Check the
"commonly missing" column by name, because those items are absent in most repos.

| Family | Owning sub-agent | Sweep for | Commonly missing |
| --- | --- | --- | --- |
| Static | static | typecheck; lint; format check; boundary rules; an aggregate `check` command; autofix-only hooks; secret scan; a prod-artifact boot smoke per deployable | boundary rules, boot smoke |
| Unit | unit | co-located logic tests; coverage measured and published; a ratchet on business-logic packages; per-artifact minimum shapes in the agent rules | coverage measurement |
| Integration | integration | real-DB in-process tests; the DB isolation rung; real or minted auth, with authz drift checks; a system tier where infra sits between components; a live tier per costly external seam, with default-off flags and paired substitutes; an endpoint-coverage gate on API servers | live-tier pairing, authz drift checks |
| End-to-end (UI-driving only) | e2e | browser or mobile flows; a `smoke` tag against the full suite; selector discipline; retries pinned to 0 | a PR-gateable smoke slice |
| Probabilistic (evals) | evals | an eval harness per LLM feature; goldens as validated data files with provenance; deterministic scorers before judges; baseline gating | regression baselines |
| Operability affordances | static | an AGENTS.md command routing table; a one-command dev stack with idempotent reset; seeds and test accounts; probe or screenshot tooling; fail-fast prerequisite errors | fail-fast prerequisites |

Audit operability from artifacts only: the docs, scripts, seeds, and tooling exist or they do
not. Never claim to have assessed agent behaviour.

## Part 2 - Tier weights

| Tier | Weight |
| --- | --- |
| Integration | 30%, because AI-assisted development wins or loses here |
| Unit | 20% |
| E2E | 20% |
| Static | 15% |
| Evals | 15%, or N/A with no probabilistic features. Spread the weight across the other tiers in proportion. |

Use the weights for audit emphasis, remediation order, and doc depth. Never apply them as
arithmetic on dimension scores.

## Part 3 - Seven dimensions

Score each dimension from 1 to 10 with a one-line justification, then give the mean. Each row
states what an 8 or higher requires. Missing any item caps the score at 7.

| Dimension | 8+ requires |
| --- | --- |
| Tier breadth | Every applicable Part 1 family is present and substantial. |
| Fidelity | A real DB; real auth when light; emulators over stubs; live-gated externals; mocks only at owned third-party seams. |
| Speed and feedback | A PR gate fast enough that agents run it habitually; a unit slice in seconds; a suite / one / tag run ladder on every slow tier. |
| Isolation and determinism | Fresh state by construction; retries at 0 with every flake root-caused; timeouts sized for load; an allowlisted env inheritance. |
| CI gating and cadence | The fast suite gates every PR; slow and live suites run on an owner-decided schedule; every suite is manually runnable; results publish visibly. |
| AI-runnability and operability | One command per tier from any state; failures name their fix in one line; docs route change-type to command; seeds plus a resettable dev stack. |
| Conventions and maintainability | Written taxonomy docs; conventions enforced by lint rules and hooks, not prose; governed datasets and goldens. |

### Structural versus transient

Score design, not weather.

- **Structural**: the finding reproduces for any developer, because the design lets it happen.
  Only structural findings affect scores.
- **Transient**: a symptom of the day, such as a red test, a drifted local DB, or a stale
  install. Record it apart. Trace it to the structural gap that let it happen, or mark it
  genuinely one-off.
- **Accepted risk**: a documented, deliberate trade-off. Record it with its existing
  mitigation. Never score against it.

## Part 4 - The AI layer

These rules cross every tier. Cite them when a finding concerns agent workflows.

1. Verification runs with one self-diagnosing command from any state. A prerequisite failure
   names its fix in one line, never surfacing as an assertion diff.
2. A flake is a bug with a root cause, never a retry knob, because agents respond to flake by
   "fixing" unbroken code.
3. Green is evidence, not assertion: require real command output. CI is the backstop, not the
   loop.
4. Guard against stale-green caches. Declare env inputs to cache keys, and guard-check them.
5. Aim anti-gaming at test quality (ratchets, per-artifact shapes, endpoint breadth), never at
   policing the agent.
6. Docs act as a routing table: change-type → exact command plus known failure modes.
7. Enforce rules with hooks and lint, not prose.
8. Before handing back a sizable feature, run the always-on suites, then the suites the change
   touches. Then boot the app and exercise the changed flow.
9. Every probabilistic feature has an eval harness (`tier-evals.md`).

## Part 5 - Brownfield sequencing

Never recommend a blanket coverage threshold, because it triggers mass low-value test
generation. Order remediation this way:

1. Characterization tests to pin current behaviour.
2. Seams, only where change is planned.
3. Ratchet and breadth gates, so coverage rises where risk lives.
4. Opt-in instruments such as mutation testing, last, on already-covered paths.

Rank presence before polish: a missing tier outranks a suboptimal one.

## Part 6 - Report contract

- Use the section shapes in the SKILL.md report template, in order: Summary, Current-state
  table, Scores, Structural findings, Transient observations, Accepted risks, Per-tier
  recommendations, Coverage gaps.
- Emit one recommendation block per tier, in weight order. Make each block independently
  actionable, so the user can plan one tier at a time.
- Cite the tier doc in each action, and route the HOW to the skill that owns it.
- Flag every row `engineering` or `owner-decision`. Money, policy, and cadence budget calls go
  to the owner.
- Cite a file or command output for every claim, or move the claim to Coverage gaps.
- Never run suites against production or prod-copy data. Never flip live-tier flags.
