# Brief: resources/human-level-ai-review.md

## TL;DR
- The report argues that reviewing AI code as a raw diff fails: comprehension is the bottleneck, so reviewers should read re-presentations instead (spec before code, AI self-explanation with a "least-confident" section, tests as specs, risk-tiered ~200 LOC chunks, layered summaries and diagrams, adversarial second-model back-translation) and name one human accountable per merge.
- Evidence base: working memory holds ~4 chunks; defect detection peaks under 200 LOC and collapses past 400 LOC or 60-90 minutes (SmartBear/Cisco, 2006 data); AI-assisted developers write less secure code while feeling more confident (Stanford CCS 2023); AI PRs carry ~1.87x the redundancy of human PRs yet get warmer reviews (MSR 2026).
- Package hallucination is a live supply-chain risk: 19.7% fictitious packages across 16 LLMs (USENIX 2025), frontier models still at ~4.6-6.1% in 2026; the report says do not raise agent autonomy without package validation and a security scanner in CI.
- Recommendations by stage: this week cap review units at ~200 LOC and sessions at 60-90 min, require a self-explanation block, name a human of record; this quarter adopt spec-driven review, isolated test-writing agents, an adversarial second-model pass; ongoing, auto-generate summaries/diagrams and track churn against a human baseline.
- One internal inconsistency: the EASE 2026 direct-review share of human comments on AI PRs is given as both 64.53% and 65.53% in the same paragraph (L84). Several thresholds (1.5x churn, 300-500 LOC/hour) are the author's own, not sourced.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | prose | low | 1269 words | Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43) |
| chunk-02 | prose | low | 1439 words | Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86) |
| chunk-03 | prose | low | 584 words | Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118) |

## Chunk summaries

### chunk-01 [low] Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43)

Opening of the report: TL;DR, six key findings, and the cognitive-science foundations. It argues that comprehension, not generation, is now the bottleneck, so reviewers should read re-presentations of AI code (summaries, stated intent, tests, back-translations) rather than raw diffs. It grounds this in cognitive load theory (about four working-memory chunks), the SmartBear/Cisco review-size limits (best under 200 LOC, collapse past 400 LOC or 60-90 minutes), automation bias (Stanford CCS 2023), distinctive AI failure modes (40% vulnerable in Pearce et al., GitClear duplication trends, MSR 2026 redundancy 1.87x), and Bacchelli & Bird's finding that review is mostly about understanding.

### chunk-02 [low] Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86)

Details sections 3 to 5. Section 3 lists AI-specific review concerns: automation bias, vigilance decrement after ~30 minutes, GitClear quality erosion, ~40% vulnerable code, and package hallucination (slopsquatting) with USENIX 2025 and 2026 figures. Section 4 ranks nine re-presentation techniques in three tiers: spec-before-code, AI self-explanation with a least-confident section, tests as specs (Tier A); risk-tiered ~200 LOC chunks, layered summaries, diagrams (Tier B); back-translation, adversarial second model, review-friendly prompting (Tier C). Section 5 surveys Google SRE, Anthropic, and GitHub guidance and the EASE 2026 AIDev study, concluding observable review activity is a poor proxy for oversight and one named human must own each PR.

### chunk-03 [low] Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118)

Closing sections. Section 6 extends re-presentation to prose and research output: extract atomic claims, verify citation presence and correctness separately, run a DOI/bibliographic/LLM pipeline to classify references, keep a numeric registry, and read a structured summary first. Recommendations come in three stages: this week cap units near 200 LOC and sessions at 60-90 minutes, require a self-explanation block, and name one human per PR; this quarter adopt spec-driven review, isolated test-writing agents, an adversarial second-model pass, CI package validation and security scanning, and risk-tiered review; ongoing, auto-generate summaries and diagrams and track churn against a human baseline. Caveats flag vendor sources, 2006-era LOC data, correlational GitClear trends, preprint 2026 studies, and the older Codex model.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Of human comments on AI-authored PRs, 64.53% were direct human review, 28.37% agent steering, 7.10% CI (EASE 2026, AIDev >932k PRs) | L84 '64.53% were direct human review' vs L84 '65.53% direct review' |
| unverified | Developers spend a majority of their time reading rather than writing code | L10 |
| unverified | A 2026 re-evaluation found frontier models still hallucinate packages at ~4.6%-6.1%, with 127 names invented identically by five models | L50 |
| unverified | Monitoring performance drops after the first ~30 minutes (vigilance decrement) | L47 |
| unverified | Hallucinated legal citations have produced sanctions in more than a thousand tracked cases worldwide | L91 |
| unverified | If post-merge defect or churn/redundancy on AI PRs exceeds ~1.5x the human baseline, tighten to full line-by-line review | L111 |
| unverified | Approval faster than ~300-500 LOC/hour should be treated as rubber-stamping | L111 |
| verified | Defect detection is highest under 200 LOC per review and falls off past 400 LOC; reviewers faster than 450 LOC/hour had below-average defect density in 87% of cases (SmartBear/Cisco, 2500 reviews, 3.2M LOC) | L12 |
| verified | Participants with an AI assistant wrote significantly less secure code yet were more likely to believe they wrote secure code (Perry et al., ACM CCS 2023, 47 participants) | L14 |
| verified | About 40% (39.33% of top suggestions) of 1,689 Copilot-generated programs across 89 scenarios were vulnerable (Pearce et al., IEEE S&P 2022) | L16 |
| verified | GitClear 2025: moved/refactored code fell from 24.8% (2021) to 9.5% (2024); copy/paste rose from 8.4% to 12.3%; commits with 5+ duplicated lines rose eightfold in 2024 | L16 |
| verified | AI agents' Average Max Redundancy was 0.2867 vs 0.1532 for humans (~1.87x, p<0.001), yet reviewers express more positive sentiment toward AI PRs (Huang et al., MSR 2026) | L20 |
| verified | Spracklen et al. (USENIX Security 2025) tested 16 LLMs over 576,000 samples and found 19.7% of generated packages fictitious; commercial models 5.2% vs open-source 21.7% | L50 |
| verified | The hallucinated 'huggingface-cli' PyPI package received over 30,000 downloads in three months | L50 |
| verified | Google SRE guidance: line-by-line review does not scale with a 4x-10x code-volume increase; oversight must move to designs, intent, and policies | L81 |
| verified | The 200-400 LOC and 60-90 minute limits come from 2006 human-code data and have not been re-derived for AI diffs | L115 |
| verified | The 'These Aren't the Reviews' 64.53% figure merges evaluative feedback with workflow acknowledgments, so it is not a pure measure of substantive review | L117 |

## Risks

- **uncited-number** [low] L42: 'Defect comments were only about one-eighth of the sample' is stated without a quoted figure from Bacchelli & Bird.
- **uncited-number** [low] L84: Direct-review share of human comments on AI PRs is given as both 64.53% and 65.53% in the same paragraph.
- **uncited-number** [low] L47: The ~30-minute vigilance figure names no study.
- **uncited-number** [low] L91: 'More than a thousand tracked cases' of legal-citation sanctions names no tracker.
- **uncited-number** [low] L111: The 1.5x churn threshold and 300-500 LOC/hour trigger are author-chosen thresholds, not sourced findings.
- **unsupported-claim** [low] L10: The 'majority of time reading' claim carries no source in the chunk.
- **unsupported-claim** [low] L18: Finding 5 asserts re-presentation converts extraneous to germane load without citing a study that measured it.
- **unsupported-claim** [low] L73: Claims mutation-style consistency checking is the 'research backbone' of back-translation without naming any paper.
- **unsupported-claim** [low] L82: 'Anthropic's own usage data shows' experienced users shift to monitoring, with no document cited.

## Least confident

- chunk-01: Whether the 200/400 LOC and 87% figures are quoted exactly from the SmartBear study or paraphrased from secondary marketing material.
- chunk-02: Whether the 64.53% and 65.53% figures at L84 measure the same denominator or two different cuts of the AIDev data that the text conflates.
- chunk-03: Whether the Stage 2 and Stage 3 recommendations are drawn from the cited sources or are the author's own synthesis.

_3 chunks, 17 claims (10 verified, 6 unverified, 1 contradicted), 9 risks._
