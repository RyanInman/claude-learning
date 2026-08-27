# Brief: Reviewing AI-Generated Output (resources/human-level-ai-review.md)

## One-line take
Stop reviewing AI code as a raw diff. Review re-presentations of it (spec, self-explanation, tests, summaries, diagrams, a second model's back-translation), because comprehension is the bottleneck and AI output specifically induces over-trust.

## Why (the evidence)
- Working memory holds ~4 chunks. Defect detection peaks under 200 LOC per review, drops past 400 LOC, and collapses after 60-90 min (SmartBear/Cisco, 2500 reviews, 3.2M LOC). Reviewers faster than 450 LOC/hr were below-average at finding defects 87% of the time.
- AI output triggers automation bias. Stanford CCS 2023 (Perry et al., 47 participants): AI-assisted devs wrote less secure code yet believed it was more secure.
- AI code fails differently: plausible-but-wrong. ~40% of Copilot suggestions vulnerable in security scenarios (Pearce et al., S&P 2022). GitClear 2025: copy/paste up, refactoring down, duplicate blocks up 8x in 2024. Hallucinated packages ("slopsquatting") at ~5-20% depending on model; still 4.6-6.1% for 2026 frontier models.
- Reviewers feel better about AI PRs even when they are worse (MSR 2026 "More Code, Less Reuse": AI redundancy 1.87x human, yet more positive reviewer sentiment). Observable review activity is a poor proxy for real oversight.
- Modern code review is mostly a comprehension exercise, not defect hunting (Bacchelli & Bird, ICSE 2013), so comprehension aids are the right lever.

## Techniques, ranked by comprehension-per-effort
Tier A
1. Review spec and plan before code (spec-driven flow: specify -> plan -> tasks; each step editable).
2. Require AI self-explanation: summary, assumptions, rejected alternatives, risks, and a "least-confident / untested" section.
3. Read tests as the behavior spec (incl. property-based tests). Isolate the test-writing agent from the code-writing agent to avoid self-ratifying tests.

Tier B
4. Chunk to ~200 LOC by system boundary; separate refactors from features; tier scrutiny by risk.
5. Layered summaries: exec summary -> architecture -> module -> line.
6. Diagrams (Mermaid control/data flow) only for genuinely complex flows.

Tier C
7. Back-translation: a different model describes what the code does; diff that against intent.
8. Adversarial second model: "find the 3 most likely bugs, missing edge cases, hallucinated APIs."
9. Prompt for review-friendly output up front: small diffs, inline rationale, flag new deps, self-generated reviewer checklist.

## Recommendations
- This week: cap units at ~200 LOC and sessions at 60-90 min; mandate the self-explanation block; name one human of record per PR.
- This quarter: spec-driven review; tests before implementation; mandatory adversarial pass plus package-existence validation and a security scanner in CI; risk-tiered review.
- Ongoing: auto-generate summaries/diagrams; track AI churn and duplication vs human baseline.
- Tripwires: AI defect/churn > 1.5x human baseline -> go line-by-line and shrink chunks. Approvals faster than 300-500 LOC/hr -> add friction (write expected behavior before viewing the diff). No scanner/package validator in CI -> do not raise agent autonomy.

## For non-code output
Extract atomic claims and verify each; check citation presence and correctness separately (DOI/CrossRef/OpenAlex lookup); verify every number against computed values; read summary and claim list before full prose.

## Caveats
Several sources are vendor reports (SmartBear, GitClear); LOC/time limits come from 2006 human-code data; GitClear trends are correlational; several 2026 items are preprints; the Stanford study used an old Codex model, but the over-confidence effect is the durable finding.
