# Brief: resources/human-level-ai-review.md

## TL;DR
- The report argues that reviewing AI code as a raw diff fails; reviewers should read re-presentations instead (spec before code, AI self-explanation with a "least-confident" section, tests as specs, risk-tiered ~200 LOC chunks, layered summaries and diagrams, adversarial second-model back-translation) and name one human accountable per merge.
- Evidence base: working memory holds ~4 chunks, defect detection collapses past 400 LOC and 60-90 minutes (SmartBear/Cisco 2006), AI-assisted developers wrote less secure code while feeling more confident (Perry et al., CCS 2023), ~40% of Copilot suggestions were vulnerable (Pearce et al.), and AI PRs show ~1.87x human redundancy yet get warmer reviews (MSR 2026).
- Package hallucination is a live supply-chain risk: 19.7% fictitious packages across 16 LLMs (USENIX 2025), frontier models still at ~4.6-6.1% in 2026; validate package existence in CI before raising agent autonomy.
- One internal inconsistency: the EASE 2026 direct-review share of human comments on AI PRs is given as both 64.53% and 65.53% in the same paragraph.
- Read the Caveats: LOC/time limits are 2006 human-code data, GitClear trends are correlational, several sources are vendors, and the 2026 studies are preprints.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | prose | low | 1269 words | Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43) |
| chunk-02 | prose | low | 1439 words | Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86) |
| chunk-03 | prose | low | 584 words | Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118) |

## Chunk summaries

### chunk-01 [low] Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load .. Details > 2. Code-review empirical findings (L1-L43)

Opens the report. Argues that reviewing AI code as a raw diff fails because comprehension, not generation, is the bottleneck, and that reviewers should read re-presentations instead: plans, self-explanations, tests, layered summaries, diagrams, adversarial back-translation. Grounds this in cognitive science (four-chunk working memory, cognitive load theory, top-down comprehension via beacons, dual coding) and in code-review empirics (SmartBear/Cisco size and speed limits, author annotation, checklists, Bacchelli & Bird on review as comprehension). Adds AI-specific evidence: Perry et al. over-trust, Pearce et al. 40% vulnerable suggestions, GitClear duplication trends, MSR 2026 reviewer blind spot.

### chunk-02 [low] Details > 3. AI-specific concerns .. Details > 5. Practical workflows (2025–2026) (L44-L86)

Covers AI-specific review hazards, the prioritized technique list, and 2025-2026 industry workflows. Hazards: automation bias, vigilance decrement after ~30 minutes, GitClear quality erosion, 40% vulnerable suggestions, hallucinated packages (huggingface-cli incident; Spracklen et al. 19.7% fictitious packages). Argues AI errors are plausible-but-wrong, so review must ask 'does it do what was intended and do the APIs exist'. Ranks nine techniques in three tiers: spec-first review, AI self-explanation with least-confident section, tests as specs; chunking and risk tiering, layered summaries, diagrams; back-translation, adversarial second model, review-friendly prompting. Workflows: Google SRE move-up-the-ladder guidance, Anthropic verification emphasis, GitHub agentic PR gates, EASE 2026 AIDev review-comment statistics, named human accountability.

### chunk-03 [low] Details > 6. Beyond code — prose, analysis, research output .. Reviewing AI-Generated Output: Principles and Techniques for Comprehension Under Load > Caveats (L87-L118)

Extends the re-presentation approach beyond code to prose and research output: extract atomic claims, verify citations in a pipeline (DOI resolution, bibliographic matching, LLM relevance check), keep a numeric registry of computed values, and read a structured summary before the full text. Then gives staged recommendations: this week cap units at ~200 LOC and sessions at 60-90 minutes, require self-explanation blocks, name a human of record; this quarter move to spec-driven review, add an adversarial second-model pass plus package validation and security scanning, tier by risk; ongoing, auto-generate summaries and diagrams and track churn/duplication against a human baseline. Closes with thresholds that trigger tighter review and caveats about vendor sources, 2006-era limits, correlational trends, and preprint status.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | 64.53% of human comments on AI-authored PRs were direct human review; 28.37% agent steering; 7.10% CI (EASE 2026, AIDev >932k PRs) | Details > 5 > Empirical reality check (L41, '64.53% were direct human review') vs Details > 5 > Empirical reality check (L41, '65.53% direct review ... on AI-authored PRs') |
| contradicted | On AI-authored PRs, 65.53% of human comments were direct review and 25.92% steering, vs 93.56% and 1.63% on human-authored PRs | Details > 5 > Empirical reality check (L41, '64.53% were direct human review') vs Details > 5 > Empirical reality check (L41, '65.53% direct review ... on AI-authored PRs') |
| unverified | Usable working memory is about four chunks, revised down from 7+/-2 | Details > 1 > Cognitive load theory (L26) |
| unverified | Pairing a diagram with concise text measurably improves comprehension and recall over text alone | Details > 1 > Dual coding (L32) |
| unverified | Authors who annotated changes before review produced markedly lower defect densities (Cisco data) | Details > 2 > Author annotation (L40) |
| unverified | Checklist-based reading beats ad-hoc on effectiveness, efficiency, and false positives, especially for omissions | Details > 2 > Checklists vs ad-hoc (L41) |
| unverified | Developers spend a majority of their time reading rather than writing code | Key Findings > 1 (L10) |
| unverified | Monitoring performance drops after the first ~30 minutes (vigilance decrement) | Details > 3 > Vigilance decrement (L4) |
| unverified | Detection of automation failures falls dramatically when a system is usually reliable (Parasuraman) | Details > 3 > Over-trust / automation bias (L3) |
| unverified | Reviewing a one-page plan is a fraction of the intrinsic load of reviewing 500 LOC | Details > 4 > Tier A > 1 (L14) |
| unverified | Reviewing tests is often faster and higher-signal than reviewing implementation | Details > 4 > Tier A > 3 (L18) |
| unverified | Anthropic usage data shows experienced users shift from per-action approval to monitoring and intervening | Details > 5 > Anthropic / Claude Code (L39) |
| unverified | Hallucinated legal citations have produced sanctions in more than a thousand tracked cases worldwide | Details > 6 > Citation verification pipeline (L5) |
| unverified | Post-merge defect or churn above ~1.5x the human baseline should trigger full line-by-line review and smaller chunks | Recommendations > Thresholds that change the plan (L25) |
| unverified | Approval faster than ~300-500 LOC/hour should be treated as rubber-stamping | Recommendations > Thresholds that change the plan (L25) |
| unverified | The 200-400 LOC and 60-90 minute figures come from 2006 human-written-code data and have not been re-derived for AI diffs | Caveats (L29) |
| unverified | SmartBear, CodeRabbit, Qodo, and GitClear are vendor sources with commercial interest | Caveats (L28) |
| verified | Defect detection is highest under 200 LOC per review and falls off past 400 LOC; 200-400 LOC over 60-90 minutes yields 70-90% defect discovery | Key Findings > 2 (L12) |
| verified | Reviewers faster than 450 lines/hour had below-average defect density in 87% of cases | Key Findings > 2 (L12) |
| verified | AI-assisted participants wrote significantly less secure code yet were more likely to believe they wrote secure code (Perry et al., CCS 2023, 47 participants) | Key Findings > 3 (L14) |
| verified | 39.33% of top Copilot suggestions across 89 scenarios (1,689 programs) were vulnerable (Pearce et al., IEEE S&P 2022) | Key Findings > 4 (L16) |
| verified | Moved/refactored code fell from 24.8% (2021) to 9.5% (2024); copy/paste rose from 8.4% to 12.3%; 5+ line duplicate blocks rose eightfold in 2024 (GitClear 2025, 211M lines) | Key Findings > 4 (L16) |
| verified | AI agents' Average Max Redundancy was 0.2867 vs 0.1532 for humans (~1.87x, p<0.001), yet reviewers express more positive sentiment toward AI PRs (Huang et al., MSR 2026) | Key Findings > 6 (L20) |
| verified | In Bacchelli & Bird (ICSE 2013), defect comments were only about one-eighth of the sample and understanding is the key aspect of review | Details > 2 > What review is really for (L43) |
| verified | A fake 'huggingface-cli' PyPI package under an LLM-hallucinated name received over 30,000 downloads in three months (Lasso Security) | Details > 3 > Hallucinated APIs / slopsquatting (L7) |
| verified | 19.7% of LLM-generated package names were fictitious across 16 LLMs and 576,000 samples; commercial 5.2% vs open-source 21.7% (Spracklen et al., USENIX Security 2025) | Details > 3 > Hallucinated APIs / slopsquatting (L7) |
| verified | A 2026 re-evaluation found frontier models still hallucinate packages at ~4.6%-6.1%, with 127 names invented identically by five models | Details > 3 > Hallucinated APIs / slopsquatting (L7) |
| verified | Google SRE guidance requires the code-generating agent to be isolated from the test-defining or reviewing agent | Details > 4 > Tier A > 3 (L18) |
| verified | Google SRE guidance says line-by-line review does not scale with 4x-10x code volume and oversight must move to designs, intent, and policies | Details > 5 > Trust but verify (L38) |
| verified | 71.58% of all review comments on AI PRs were authored by agents | Details > 5 > Empirical reality check (L41) |
| verified | Human-only reviews occur on 8.08% of AI PRs vs 25.21% of human PRs | Details > 5 > Empirical reality check (L41) |
| verified | AI redundancy ran ~1.87x human levels in the MSR 2026 study | Recommendations > Stage 3 > 8 (L23) |
| verified | GitClear churn/duplication trends are correlational, not causal | Caveats (L30) |
| verified | The EASE 2026 64.53% figure merges evaluative feedback with workflow acknowledgments, so it is not a pure measure of substantive review | Caveats (L31) |

## Risks

- **uncited-number** [low] Key Findings > 1 (L10): The 'majority of time reading' figure names no study.
- **uncited-number** [low] Details > 1 > Reading vs writing (L34): 'Volume is now many times larger' has no source.
- **uncited-number** [low] Details > 5 > Empirical reality check (L41): Two different figures (64.53% and 65.53%) are given for direct-review share of human comments on AI PRs in the same paragraph.
- **uncited-number** [low] Details > 3 > Code-quality erosion (L5): 'Churn roughly doubling' has no year range or base figure.
- **uncited-number** [low] Details > 6 > Citation verification pipeline (L5): 'More than a thousand tracked cases' names no tracker or database.
- **uncited-number** [low] Recommendations > Thresholds that change the plan (L25): The 1.5x and 300-500 LOC/hour thresholds are author-chosen and not tied to a study; 300-500 differs from the 450 figure cited earlier.
- **unsupported-claim** [low] Key Findings > 5 (L18): Asserts re-presentation converts extraneous into germane load without citing a study that measured it on code review.
- **unsupported-claim** [low] Details > 2 > Author annotation (L40): The annotation mechanism ('forces self-review') is asserted, and the magnitude ('markedly lower') has no number.
- **unsupported-claim** [low] Details > 4 > Tier C > 7 (L30): Mutation-style consistency checking is called the 'research backbone' with no paper named.
- **unsupported-claim** [low] Details > 4 > Tier A > 3 (L18): Industrial use of property-based testing at Amazon, Volvo, Stripe is asserted without a source.
- **unsupported-claim** [low] Details > 6 > Numeric registry (L6): A whitelist of computed values is proposed without evidence it catches errors in practice.

## Least confident

- chunk-01: Whether the 'four chunks' working-memory figure and the annotation finding in the Cisco data are as settled as the chunk presents; neither cites a specific source in this chunk.
- chunk-02: Whether 64.53% and 65.53% describe two different denominators in the EASE 2026 study or one of them is a typo; the chunk does not make the distinction clear.
- chunk-03: Whether the citation-verification pipeline (CrossRef/OpenAlex/Semantic Scholar plus LLM relevance check) reflects an existing tool or is the author's proposal; the chunk does not say.

_3 chunks, 34 claims (17 verified, 15 unverified, 2 contradicted), 11 risks._
