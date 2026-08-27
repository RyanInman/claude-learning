# Brief: resources/human-level-ai-review.md

## TL;DR
- The report argues that reviewing AI code as a raw diff fails; review re-presentations instead: spec before code, AI self-explanation, tests as specs, ~200 LOC risk-tiered chunks, layered summaries, adversarial second model.
- Evidence: defect detection collapses past 400 LOC and 60-90 minutes (SmartBear/Cisco); AI-assisted developers write less secure code while feeling more secure (Stanford CCS 2023); AI code runs ~1.87x human redundancy (MSR 2026).
- Package hallucination is a live supply-chain risk: 19.7% fictitious packages across 16 LLMs (USENIX 2025), frontier models still ~4.6-6.1%; validate package existence in CI before raising agent autonomy.
- One internal inconsistency: the EASE 2026 direct-review share of human comments on AI PRs appears as both 64.53% and 65.53% in the same paragraph.
- Three-stage plan: cap review units and name one accountable human now; spec-driven review plus adversarial pass this quarter; auto summaries and churn tracking ongoing. Thresholds are author judgment, not sourced.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | prose | low | 1269 words | Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43) |
| chunk-02 | prose | low | 1439 words | Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86) |
| chunk-03 | prose | low | 584 words | Details > 6. Beyond code — prose +2 more |

## Chunk summaries

- **chunk-01** [low] Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43): Opens the report: argues that reviewing AI code as a raw diff fails because comprehension is the bottleneck, and that reviewers should read re-presentations (spec first, AI self-explanation, tests as specs, risk-tiered ~200 LOC chunks, layered summaries, adversarial second model).
- **chunk-02** [low] Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86): Lists AI-specific review hazards (automation bias, vigilance decrement, code-quality erosion, ~40% vulnerable suggestions, package hallucination/slopsquatting), then presents nine re-presentation techniques in three tiers: spec-before-code, AI self-explanation with a least-confident section, tests as specs; risk-tiered ~200 LOC chunks, layered summaries, diagrams; back-translation, adversarial second model, review-friendly prompting.
- **chunk-03** [low] Details > 6. Beyond code — prose +2 more: Extends re-presentation to prose and research output (claim extraction, citation verification pipeline, numeric registry, summary-first reading).

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Of human comments on AI-authored PRs, 64.53% were direct review, 28.37% agent steering, 7.10% CI (EASE 2026, AIDev >932k PRs) | L84 '64.53% were direct human review' vs L84 '65.53% direct review' |
| unverified | Working memory holds about four chunks; re-presentation reduces extraneous load and frees capacity for schema-building | L26 |
| unverified | 2026 re-evaluation: frontier models still hallucinate packages at ~4.6-6.1%; 127 names invented identically by five models | L50 |
| unverified | Hallucinated legal citations have produced sanctions in more than a thousand tracked cases worldwide | L91 |
| unverified | If AI PR defect or churn exceeds ~1.5x human baseline, tighten to full line-by-line review and shrink chunks | L111 |
| unverified | Approvals faster than ~300-500 LOC/hour should be treated as rubber-stamping | L111 |
| verified | Defect detection is highest under 200 LOC, falls past 400 LOC; 200-400 LOC over 60-90 minutes yields 70-90% defect discovery | L12 |
| verified | AI-assisted participants wrote less secure code yet believed it more secure (Perry et al., CCS 2023, 47 participants) | L14 |
| verified | Approximately 40% (39.33%) of Copilot top suggestions across 89 security scenarios were vulnerable (Pearce et al., IEEE S&P 2022) | L16 |
| verified | GitClear 2025: moved code fell 24.8% to 9.5%, copy/paste rose 8.4% to 12.3%, 5+ line duplicate blocks up eightfold | L16 |
| verified | AI agents' Average Max Redundancy 0.2867 vs 0.1532 for humans, ~1.87x, p<0.001 (MSR 2026 'More Code, Less Reuse') | L20 |
| verified | Hallucinated 'huggingface-cli' PyPI package received over 30,000 downloads in three months (Lasso Security) | L50 |
| verified | 19.7% of generated packages fictitious across 16 LLMs and 576,000 samples; commercial 5.2% vs open-source 21.7% (USENIX Security 2025) | L50 |
| verified | Google SRE: line-by-line review does not scale with 4x-10x code volume; oversight must move up the abstraction ladder | L81 |
| verified | Test-defining agent must be isolated from code-generating agent to prevent cross-bias (Google SRE guidance) | L61 |
| verified | The 200-400 LOC and 60-90 minute limits come from 2006 human-code data, not re-derived for AI diffs | L115 |
| verified | The 64.53% direct-review figure merges evaluative feedback with workflow acknowledgments, so it overstates substantive review | L117 |
| verified | GitClear churn/duplication trends are correlational with AI adoption, not causal | L116 |

## Risks

- **uncited-number** [low] L39: Slower than 400-500 LOC/hour threshold restated with a range that differs from L12's 450 figure.
- **uncited-number** [low] L84: Direct-review share stated as 64.53% and 65.53% in the same paragraph; one is wrong.
- **uncited-number** [low] L48: 'Churn roughly doubling' has no figure or source beyond GitClear label.
- **uncited-number** [low] L91: 'More than a thousand tracked cases' names no tracker or source.
- **uncited-number** [low] L111: 1.5x threshold and 300-500 LOC/hour cutoff are author-chosen; no derivation given.
- **unsupported-claim** [low] L10: 'Developers spend a majority of their time reading' has no source cited.
- **unsupported-claim** [low] L40: Author-annotation lowering defect density asserts a mechanism (self-review) without data.
- **unsupported-claim** [low] L41: Checklist superiority is called 'mixed' evidence but no study is named.
- **unsupported-claim** [low] L73: Back-translation 'divergence localizes bugs' and mutation-consistency backbone cite no study.
- **unsupported-claim** [low] L82: 'Anthropic's own usage data shows' users shift to monitoring; no report named.
- **unsupported-claim** [low] L92: Numeric-registry whitelist approach recommended with no evidence it works.

## Least confident

- chunk-01: Whether the four-chunk working memory figure and the cognitive theory attributions (Sweller, Paivio, Brooks, Soloway) are accurately summarized, since no specific papers are cited for them.
- chunk-02: The EASE 2026 percentages, since the paragraph gives two different direct-review figures and I cannot tell which the source reports.
- chunk-03: The origin of the action thresholds in the 'Thresholds that change the plan' paragraph, which read as author judgment rather than sourced values.

_3 chunks, 18 claims (12 verified, 5 unverified, 1 contradicted), 11 risks. Budget 1097 words, compaction level 1._
