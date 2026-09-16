# Evals tier - golden state

Weight: 15%, or N/A when the repo has no probabilistic features. The moment an LLM feature ships,
rank evals second in emphasis, after integration.

One rule sets the boundary: anything that produces a score goes to the eval harness. Hard
pass/fail stays in the integration tier.

## Portable invariants

These hold for any LLM repo and any runner.

- **Goldens are validated data files**, such as zod-checked JSONL, with `id`, `stratum`,
  `provenance`, and `notes`. Never store goldens as code constants. The normal test command
  checks golden integrity.
- **Every prod failure becomes a golden.** Adversarial review promotes model-proposed labels.
  No human-labeling gate applies.
- **Hermetic replay.** Recorded inputs plus a model-response cache make warm runs free and
  deterministic. Live-model runs follow the live-tier rules: default-off, flagged, off the PR
  gate's hot path.
- **Deterministic scorers first.** Add an LLM judge only as the fuzzy arbiter: binary verdicts,
  temperature 0, a model family different from the system under test.
- **Gating.** A threshold floor plus a baseline-delta comparison, on path-filtered CI. Prompt
  and model changes gate like code changes.

## Minimum viable harness

For one small LLM feature, require only:

- a validated golden data file,
- deterministic checks,
- a threshold gate on path-filtered CI.

Add no judge, no corpus lifecycle, and no dashboard until a trigger in the Brownfield ramp below applies. Size the golden set
qualitatively: enough real cases to cover the behaviours you would hate to regress, seeded from
real traffic and failures.

## Tools

The harness is runner-neutral. Current picks are recommendations, not doctrine:

- **Evalite** as the runner. Note its patch debt in the report.
- **Langfuse** as the default tracing choice.

## Brownfield ramp

1. Start at the minimum viable harness for the riskiest feature.
2. Add the judge only when a fuzzy behaviour resists deterministic checks.
3. Add corpus tooling only when the golden count makes hand-editing error-prone.
