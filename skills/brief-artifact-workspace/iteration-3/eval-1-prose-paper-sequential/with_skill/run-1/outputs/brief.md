# Brief: /Users/admin/claude-learning/resources/human-level-ai-review.md

## TL;DR
- The report argues reviewers should read re-presentations of AI code, not raw diffs: spec before code, AI self-explanation with a least-confident section, tests as specs, ~200 LOC risk-tiered chunks, adversarial second-model checks.
- Grounds: working memory holds ~4 chunks, defect detection collapses past 400 LOC and 60-90 minutes, and AI code triggers over-trust (Stanford CCS 2023) while carrying ~1.87x human redundancy (MSR 2026).
- Package hallucination is a live supply-chain risk: 19.7% fictitious packages across 16 LLMs (USENIX 2025), frontier models still 4.6-6.1% in 2026; validate package existence in CI before raising agent autonomy.
- Action plan: this week cap units at 200 LOC and name one human per PR; this quarter go spec-driven with an adversarial pass; tighten review if AI churn exceeds ~1.5x baseline.
- One internal inconsistency: the EASE 2026 direct-review share of human comments on AI PRs is given as both 64.53% and 65.53% in the same paragraph (L84). Most Recommendations thresholds are uncited.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | prose | low | 1269 words | Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43) |
| chunk-02 | prose | low | 1439 words | Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86) |
| chunk-03 | prose | low | 584 words | Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118) |

## Chunk summaries

### chunk-01 [low] Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43)

Opens the report: comprehension, not generation, is now the bottleneck for AI code, so reviewers should read re-presentations (specs, self-explanations, tests, summaries, diagrams, back-translations) instead of raw diffs. Grounds this in cognitive-load theory (four-chunk working memory, top-down comprehension via beacons, dual coding), the SmartBear/Cisco review-size limits, Stanford over-trust findings, AI-specific failure data (Pearce 40% vulnerable, GitClear duplication), and Bacchelli & Bird's finding that review is mainly about understanding.

### chunk-02 [low] Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86)

Details AI-specific review concerns (automation bias, vigilance decrement, GitClear quality erosion, 40% vulnerable suggestions, package hallucination at 19.7% across 16 LLMs), then ranks nine re-presentation techniques in three tiers: spec-before-code, AI self-explanation with a least-confident section, tests as specs; chunking by risk, layered summaries, diagrams; back-translation, adversarial second model, review-friendly prompting. Closes with 2025-2026 vendor workflows (Google SRE, Anthropic, GitHub) and the EASE 2026 finding that review effort on AI PRs is structured differently.

### chunk-03 [low] Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118)

Extends re-presentation to prose and research output (claim extraction, citation verification pipelines, numeric registries, summary-first reading). Then lays out staged recommendations: this week cap units near 200 LOC and sessions at 60-90 minutes, require self-explanation blocks, name a human of record; this quarter adopt spec-driven review, adversarial second-model pass, package validation, risk tiering; ongoing, auto-generate summaries and track churn. Gives thresholds that trigger tighter review and closes with caveats on vendor sources, 2006-era data, and preprint status.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Direct human review share of human comments on AI-authored PRs is 64.53% and also 65.53% in the same paragraph. | L84 '64.53% were direct human review' vs L84 '65.53% direct review' |
| unverified | Anthropic usage data shows experienced users shift from per-action approval to monitoring and intervening. | L82 |
| unverified | Hallucinated legal citations have produced sanctions in more than a thousand tracked cases worldwide. | L91 |
| unverified | If AI PR defect or churn exceeds ~1.5x human baseline, tighten to full line-by-line review and shrink chunks. | L111 |
| unverified | Approval faster than ~300-500 LOC/hour signals rubber-stamping and should trigger friction. | L111 |
| verified | Defect detection is highest under 200 LOC, falls past 400 LOC; 200-400 LOC over 60-90 minutes yields 70-90% defect discovery. | L12 |
| verified | AI-assisted participants wrote less secure code yet believed it more secure (Perry et al., CCS 2023, 47 participants). | L14 |
| verified | About 40% (39.33%) of Copilot top suggestions across 89 security scenarios were vulnerable (Pearce et al., S&P 2022). | L16 |
| verified | GitClear 2025: moved code fell 24.8% to 9.5%, copy/paste rose 8.4% to 12.3%, 5+ line duplicate blocks up eightfold. | L16 |
| verified | AI agent redundancy 0.2867 vs human 0.1532 (~1.87x, p<0.001), yet reviewers react more positively to AI PRs (Huang et al., MSR 2026). | L20 |
| verified | Modern code review is mainly about understanding; defect comments were about one-eighth of the sample (Bacchelli & Bird, ICSE 2013). | L42 |
| verified | Spracklen et al. (USENIX 2025): 19.7% of generated packages fictitious across 16 LLMs; commercial 5.2% vs open-source 21.7%. | L50 |
| verified | 2026 re-evaluation: frontier models still hallucinate packages at 4.6-6.1%; 127 names invented identically by five models. | L50 |
| verified | Hallucinated 'huggingface-cli' PyPI package got over 30,000 downloads in three months (Lasso Security). | L50 |
| verified | Google SRE: line-by-line review does not scale with 4x-10x code volume; oversight must move to designs, intent, policies. | L81 |
| verified | The 200-400 LOC and 60-90 minute limits come from 2006 human-code data, not re-derived for AI diffs. | L115 |
| verified | EASE 2026's 64.53% figure merges evaluative and workflow comments, so it is not pure substantive review. | L117 |

## Risks

- **uncited-number** [low] L39: '400-500 LOC/hour' threshold differs from the 450 figure at L12; no separate source.
- **uncited-number** [low] L84: 64.53% vs 65.53% for the same direct-review share; one figure is wrong.
- **uncited-number** [low] L47: '~30 minutes' vigilance decrement stated without a named source.
- **uncited-number** [low] L91: 'More than a thousand tracked cases' has no tracker or source named.
- **uncited-number** [low] L111: The 1.5x and 300-500 LOC/hour thresholds are author-chosen, no derivation given.
- **unsupported-claim** [low] L10: 'Developers spend a majority of their time reading' has no source in the chunk.
- **unsupported-claim** [low] L18: Re-presentation converting extraneous to germane load is asserted from theory, no study cited.
- **unsupported-claim** [low] L41: Checklist superiority is described as 'mixed but leans' with no study named.
- **unsupported-claim** [low] L61: 'Often faster and higher-signal' to review tests than code is asserted without a study.
- **unsupported-claim** [low] L73: Mutation-style consistency checking called 'the research backbone' with no citation.
- **unsupported-claim** [low] L92: Numeric registry approach recommended with no evidence it works in practice.

## Least confident

- chunk-01: Whether the 2006 SmartBear/Cisco human-code limits transfer to AI diffs; the chunk asserts it without evidence.
- chunk-02: The EASE 2026 percentages at L84: the paragraph mixes two category schemes and I cannot tell which figure is the intended direct-review share.
- chunk-03: Whether the Stage 2 and 3 thresholds are backed by any study or are the author's judgment calls.

_3 chunks, 17 claims (12 verified, 4 unverified, 1 contradicted), 11 risks._
