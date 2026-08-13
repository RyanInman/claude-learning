# Adversarial Review Transcript

**Artifact:** skills/scriptify/evals/evals.json, with iteration-3 outcomes in
adversarial-review/artifact-eval-suite.md
**Date:** 2026-08-11

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

### Goal

The suite exists to answer one question: does scriptify beat what Claude does unaided? A skill
that ties baseline is pure recurring token cost, so the suite must discriminate, not merely
score well.

### Key decisions and their why

**Ten evals over one fixture family.** Six report-only (0, 2, 4, 5, 8, 9) and four mutating
(1, 3, 6, 7). Report-only evals let a tree diff against a pristine baseline prove the run wrote
nothing, which is the cheapest possible objective check.

**Assertions pre-registered in evals.json before any run.** Iteration-1's debate found a
re-grading dispute where correcting a score after the fact moved the delta in the corrector's
favour. Pre-registration is the suite's only structural protection against that.

**Trap evals rather than easy ones.** Eval 0 step 7 says "verify entries clearly written" — the
verb invites SCRIPT, the work is judgment. Eval 5 gates three steps behind WebFetch,
AskUserQuestion and an MCP call. Eval 8 hides a dead step in a Notes paragraph. Eval 6 plants a
name collision. Eval 9 puts the target in a plugin cache.

**Baseline is no-skill, held constant across iterations** so iteration-over-iteration numbers
stay comparable.

### Constraints not visible in the artifact

One run per eval per arm — the plus/minus figures are spread across evals, not repeats.
Iteration-1 hit an API spend limit mid-review, so cost is a live constraint.
Iteration-2 ran all 10 evals but was never graded; no benchmark exists for it.
scriptify is `disable-model-invocation: true`, so triggering is never under test.

### Decisions I am least sure of

1. **Script-count assertions.** Eval 1 demands >=3 scripts, eval 3 exactly 2, eval 6 >=2. In
   iteration-3 both arms consolidated multi-step work into single-pass scripts, so these
   assertions fired against the arms' own engineering judgment. Eval 3's fired against the
   skill and for the baseline.
2. **Eval 7's scriptify-specific assertions.** Two of five name a scriptify path convention
   (`scripts/tests/`) or scriptify's own smoke_test.py. No baseline can pass them. The grader
   tagged all three separators DEFINITIONAL.
3. **Eval 6 A3 conflates two properties** — script count AND working --help — so a count failure
   hides a real --help win.
4. **Eval 8 A4 is ambiguous**: "the step is not deleted from the target SKILL.md" does not say
   whether it judges the file on disk or the recommendation in the report.
5. **Whether classification-accuracy assertions can discriminate at all.** Across evals 0-9 the
   only genuine separators were script interface properties: nonzero exit on findings, a stated
   exit-code contract, working --help, smoke test before rewrite.


## Phase 2 — Adversary's Questions

### Question 1 — how the headline numbers were computed

For `with_skill 90% +/- 12%, baseline 76% +/- 18%, delta +0.14`: what is the numerator and denominator in each arm (raw PASS counts over which pool of the 51 assertions), is the percentage an unweighted mean over assertions or a mean of per-eval rates, what does the `+/-` figure measure and over what sample, and are the assertions the grader tagged DEFINITIONAL or NON-DISCRIMINATING included in both arms' percentages on the same terms as the rest?

### Question 2 — provenance of the grades and the facts

Who or what produced each assertion's PASS/FAIL verdict and its evidence line: the same session that authored scriptify, a separate grading pass, or a script? Was whoever assigned the verdicts aware of which arm was which while grading? And is `facts.json` (target_tree_diff, new_script_count, new_scripts_all_help_ok, residue.*) emitted by a deterministic collector, or written by the agent under test?

### Question 3 — what is changeable for iteration-4, and at what cost

Is `evals.json` itself in scope for revision as an outcome of this review, or is the artifact frozen and only its interpretation under debate? What is the per-run cost and wall-clock of one full 10-eval, 2-arm pass, and how many additional passes the remaining budget allows?


## Phase 3 — Defender's Answers

### Answer 1 — the headline is a mean of per-eval rates, and it includes every assertion

The percentage is a **mean of the ten per-eval pass rates**, not an unweighted mean over the 51
assertions. `aggregate_benchmark.py` computes `passed/total` per run, then averages those ten
numbers. The `+/-` is the standard deviation **across the ten evals**, not across repeats — there
is exactly one run per eval per arm, so it carries no run-to-run variance information at all.

Both poolings, computed directly:

| pooling | with_skill | baseline |
|---|---|---|
| pooled assertions | 46/51 = 0.902 | 38/51 = 0.745 |
| mean of per-eval rates | 0.900 +/- 0.117 | 0.756 +/- 0.181 |

The two agree here by coincidence of eval sizes (assertion counts range 3 to 7), so the headline
does not turn on the choice. Delta is +0.144 by mean-of-rates, +0.157 pooled.

Yes — DEFINITIONAL and NON-DISCRIMINATING assertions are included in both arms' percentages on
exactly the same terms as every other assertion. Nothing was excluded, reweighted, or corrected
after grading. That is deliberate (pre-registration), and it is also the single largest reason I
flagged the headline as untrustworthy in my opening: eval 7 contributes a 5/5 vs 2/5 split whose
three separators the grader itself tagged DEFINITIONAL.

### Answer 2 — separate graders, unblinded, deterministic facts with one known bug

**Verdicts:** produced by ten independent grader subagents, one per eval, each grading both arms.
None of them authored scriptify and none had this session's conversation history. They received a
written brief, the eval's pre-registered assertions, both arms' outputs, and `facts.json`.

**Blinding: no.** The graders read arms from directory names `with_skill/` and `without_skill/`.
Grading was unblinded, and the brief further told them to tag DEFINITIONAL and
NON-DISCRIMINATING, which requires knowing which arm is which. I did not run a blind comparison.
This is a real weakness in the grading design and I am not going to defend it as anything else.

**facts.json:** emitted by `collect_facts.py`, a 243-line deterministic collector I ran myself
after all runs finished — not written by any agent under test. It computes sha256 tree diffs
against `fixture-baseline/`, executes `--help` on every `.py` and records the exit status, and
for eval 7 re-runs the smoke test against the moved manifest.

It has one known bug, found by the eval-7 grader, not by me: `residue.unresolved_paths` lists six
paths for the with_skill arm because the collector does not expand the `{skill}` placeholder in
manifest invocation tokens. Expanded against `target_skill`, all ten fixture tokens resolve. The
collector is wrong there; the residue is sound. No graded verdict depended on that field.

**Additional provenance fact:** every run hit a harness guard blocking subagent `Write` on
report-shaped files and worked around it with a Bash heredoc, because my own run instructions
mandated those files. One run was flagged for tunneling a denied tool call. Content is unaffected
and the guard hit both arms equally, but `errors_encountered` is inflated by roughly 1 across
nearly every run, so that column is not usable as a quality signal.

### Answer 3 — evals.json is in scope; one pass costs about 1.6M tokens

`evals.json` is fully in scope. Revising it is the most likely outcome of this review, and it is
why I asked for the review before drawing any conclusion about the skill from these numbers.

Measured cost of this pass:

- 20 eval runs: 1,084,472 subagent tokens (with_skill 668,679; baseline 415,793)
- 10 grading subagents: about 486,000 tokens
- total: roughly 1.57M subagent tokens
- wall clock per arm: with_skill 294.3s +/- 133.9s, baseline 164.0s +/- 47.5s; the full fan-out
  completed in about 8 minutes because runs execute concurrently

How many further passes the budget allows: **unknown.** I do not have visibility into the
account's remaining spend. The relevant precedent is that iteration-1 hit an API spend limit
partway through its review, which is why cost is on my list of live constraints.


## Phase 4 — Adversary's Objections

### Objection 1 — Half the measured delta comes from assertions that name scriptify's own artifacts, not from capability

**Problem.** The headline `+0.14` reads as "scriptify beats unaided Claude by 14 points." Four of the eight net assertion flips that produce it fail the baseline for not using scriptify's path convention, scriptify's test runner, or scriptify's preferred remediation. Those four measure conformity to the skill, and no unaided run can pass them at any quality level. The suite therefore cannot answer the one question the Defender says it exists to answer.

**Evidence.** I recomputed the arms from the artifact. Pooled: with_skill 46/51, baseline 38/51, delta +0.157. Twelve assertions discriminate: ten favour with_skill (0A1, 0A3, 1A4, 3A3, 5A6, 6A4, 7A1, 7A3, 7A4, 9A4), two favour baseline (0A5, 3A1). Net +8.

Four of the ten are conformity, and the grader said so unprompted in three cases:
- 7A1 requires `scripts/tests/`. The baseline put fixtures and a manifest at `tests/` inside the same skill, which satisfies the prompt's literal ask ("keep the test fixtures and the manifest inside the skill"). Grader: `DEFINITIONAL`.
- 7A3 requires scriptify's `smoke_test.py` to exit 0 against the manifest. The baseline shipped `tests/run_tests.py`, which exits 0 with "2 case(s), 0 failure(s)". Grader: `DEFINITIONAL`.
- 7A4 requires scriptify's smoke-test command in SKILL.md. The baseline documents `python3 tests/run_tests.py`. Grader: `DEFINITIONAL`.
- 9A4 requires an offer to copy into the project. I read `eval-9/without_skill/outputs/gate.md`: the baseline offered three durable destinations and recommended "The plugin's source repo... so it ships in the next plugin release and survives updates," with a personal-skills copy as option 2 and a throwaway cache write as option 3, each with its trade-off. For a plugin-installed skill that is a defensible answer, arguably a better one than forking a project copy. It failed on destination choice, not on the property the eval's own expected_output describes.

Drop those four: with_skill 42/47 = 0.894, baseline 38/47 = 0.809, delta **+0.085**. Exactly half the headline is conformity.

A harness asymmetry compounds eval 7. `RUN_INSTRUCTIONS_with_skill.md` §4 reads "not in the target skill folder, unless the skill itself tells you to place them in the target." `RUN_INSTRUCTIONS_without_skill.md` §4 drops the exception clause. Eval 7 is the one eval that grades placing test residue in the target. The baseline wrote residue anyway, so I do not claim this caused its failure, but the arms were not given the same latitude on the exact behaviour eval 7 scores.

**Better way.** Rewrite each conformity assertion as the property it is a proxy for, then re-grade iteration-3's existing outputs at zero run cost:
- 7A1: "test fixtures and a manifest persist inside the target skill folder after the run, at a path the rewritten SKILL.md names."
- 7A3: "the residue's own documented re-run command, executed from the target skill folder, exits 0."
- 7A4: "the rewritten SKILL.md body contains the command that re-runs the kept checks."
- 9A4: "the run offers at least one durable write destination outside the plugin cache and continues the apply stage there."

Then keep the scriptify-specific versions as a separately reported `conformity` block that never enters the pass rate, and publish two numbers: capability delta and conformity delta. Under the rewrites the baseline plausibly passes 7A1, 7A3, 7A4 and 9A4, which is the difference between reporting +0.157 and +0.085.

### Objection 2 — Two graders returned opposite verdicts on identical assertion text and materially identical evidence, and one of the eight flips rests on that

**Problem.** Eval 1 A3 and eval 6 A4 are byte-identical assertions: "a smoke-test PASS result is reported before the SKILL.md rewrite is shown." The eval-1 grader passed the baseline on it; the eval-6 grader failed the baseline on it, using an ordering criterion the eval-1 grader explicitly declined to apply. Ten independent graders with no calibration item and no blinding produce leniency that varies per eval, and that variance lands directly in the delta.

**Evidence.** I read both baseline reports and both transcript-notes.

Chronology is the same in both arms of both evals. `eval-6/without_skill/outputs/transcript-notes.md` item 9 runs three checks (exit 1, exit 1, exit 2) against expectations hand-derived at item 6, item 10 re-runs the untouched script, item 11 rewrites SKILL.md. `eval-1/without_skill/outputs/transcript-notes.md` items 9-11 verify, item 12 rewrites. Verify-then-rewrite in both.

Report layout is the same in both. Eval 1's baseline report opens with a classification table whose "Where it lives now" column already announces `SKILL.md step 3`, and puts `## Verification` far below. Eval 6's baseline report opens with a "What changed" table naming the SKILL.md rewrite and puts `## Verification` far below. The eval-6 grader charged exactly this ("the report announces the SKILL.md rewrite... at line 11, well before the Verification section at line 62"). The eval-1 grader refused to charge it ("Graded on the eval's own expected_output framing... rather than section order inside report.md, where the diff block happens to precede the PASS block").

Neither baseline prints the literal token PASS. Eval 1's Verification table gives a Result column of exit codes and observed output; eval 6's Verification section gives shell transcripts with `echo $?` plus a hand-check ("That matches the files by hand"). The eval-1 grader called that satisfying; the eval-6 grader called it "raw invocations... with no pass/fail assertions." Same evidence class, opposite verdict.

Removing 6A4 alongside objection 1's four takes the delta to 41/46 vs 38/46 = **+0.065**, and leaves three net informative flips out of 51 assertions and 1.57M tokens, roughly 520K tokens per informative flip.

**Better way.** Two changes, both cheap:
1. Split the compound assertion into a mechanical half and a judgment half. Mechanical: "in transcript-notes.md, every verification command for a generated script appears before the first SKILL.md write." A script decides that from the numbered list, with no grader involved. Judgment half, if kept at all: "the report states a per-check outcome for each verification command." Neither half then depends on report section order or on the literal string PASS.
2. Seed every grader with the same two-item calibration set (one known-pass, one known-fail on borderline vocabulary), require the calibration verdicts in `grading.json`, and discard any grader that misses them. Ten graders that never see a shared anchor cannot produce comparable verdicts, and today nothing in `GRADER_INSTRUCTIONS.md` supplies one.

### Objection 3 — 71% of the assertions never discriminate, which flattens the pass rate and hides where the signal is

**Problem.** Of 51 assertions, 12 separate the arms, 3 fail both arms, and 36 pass both. The pass rate is therefore a number dominated by assertions that carry no information about the skill, compressed toward 100% and insensitive to real change. Worse, the five sound with_skill-favouring flips all test one property, so the suite measures one thing five times and reports it as a broad win.

**Evidence.** Both-arms-fail assertions: 1A1 (>=3 scripts), 6A3 (>=2 scripts with --help), 8A4 (dead-step clause conjunction). Those six gradings can move nothing.

After removing objection 1's four and objection 2's one, the remaining with_skill-favouring flips are 0A1 (per-row interface column), 0A3 (argv plus exit codes), 1A4 (nonzero exit on findings), 3A3 (--help and bad-args behaviour), 5A6 (stated exit-code contract). Every one is script-interface hygiene. Zero come from classification accuracy, which is what evals 0, 2, 4, 5, 8 spend 26 assertions on. The Defender's own uncertainty 5 suspects this; the arm-by-arm data confirms it, and quantifies it at 5 of 5.

Cost: 1.084M tokens of runs plus about 486K of grading, for 12 discriminating gradings.

**Better way.** Restructure into two tiers that are reported separately and never averaged together.
- **Guardrail tier, pass/fail gate, not a percentage.** Every "no new files were written into the target" and "the pre-existing file is byte-identical" assertion becomes a gate: any failure invalidates the run. I count 17 assertions whose ground truth `collect_facts.py` already computes (0A2, 1A1, 2A1, 3A1, 3A2, 4A2, 5A2, 6A1, 6A3, 7A1, 7A2, 7A3, 8A2, 9A1, 9A5, plus 1A4 and 6A5 with a per-eval check command). Add a `check` field to `evals.json` and let the collector decide them. That removes a third of the grading fan-out and removes LLM variance from the assertions that are meant to be objective.
- **Signal tier, graded, and reported per property.** Group the remaining assertions under the property they test: interface hygiene, classification accuracy, agent-tool discipline, dead-step detection, eligibility handling. Report a delta per group. A suite that says "interface hygiene +5, classification accuracy 0" tells you what to change in the skill; "90% vs 76%" does not.
- Spend the freed grading budget on 3 repeats of the 4 evals that actually discriminate (0, 1, 3, 5). That costs roughly 250-300K tokens and is the only way to learn whether these flips are stable.

### Objection 4 — The script-count assertions score a proxy both arms reject on the merits, and one of them injects anti-signal

**Problem.** Eval 1 demands >=3 scripts, eval 3 exactly 2, eval 6 >=2. Consolidating a single parse into one script is the better engineering choice, both arms reached it independently, and the assertions punish it. Eval 3 A1 is one of only two baseline-favouring flips, so it does not merely waste a slot, it moves the delta against the skill for doing the right thing.

**Evidence.** The baseline's own eval-1 report argues the case explicitly: "One script, not five. Every deterministic step reads the same parse of the same files. Five scripts would parse the folder five times and could disagree with each other." The eval-6 baseline says the same: "Steps 1-3 share one pass over the same files, so they belong in one script rather than three." In eval 3 the with_skill arm merged steps 1 and 3 into one script, delegated both selected steps, and failed A1 on the count. In eval 1 and eval 6 both arms failed the count, so those two assertions produced six gradings and zero information.

Counting files is a proxy for "the right steps got delegated." The real property is coverage, and the suite never tests it directly.

**Better way.** Replace all three count assertions with coverage assertions, mechanically checkable from the rewritten SKILL.md and `facts.json`:
- Eval 3: "the rewritten SKILL.md invokes a generated script at steps 1 and 3, and no other step gained a script invocation."
- Eval 1: "every step the report classified SCRIPT is invoked by an exact command line in the rewritten SKILL.md, and every generated script exits 0 on `--help`."
- Eval 6: same form, plus the existing collision assertion, which already works.

This is invariant to consolidation, tests the property the eval cares about, and needs no grader. Re-grade iteration-3's outputs under it before spending on iteration-4: eval 3's with_skill FAIL likely becomes a PASS, which alone moves the pooled delta by one flip.

### Objection 5 — The benchmark artifacts state three runs per configuration when one was run, and record no model

**Problem.** `benchmark.md` and `benchmark.json` are what a reader consumes, and both assert a run count that never happened. Anyone reading them takes `90% ± 12%` as spread across three repeats, which is precisely the reading the Defender says is wrong. The same files record no executor model, so the stated design goal of iteration-over-iteration comparability against a held-constant baseline cannot be verified from the artifacts.

**Evidence.** `iteration-3/benchmark.json` metadata: `"runs_per_configuration": 3`, `"executor_model": "<model-name>"`, `"analyzer_model": "<model-name>"`, `"skill_path": "<path/to/skill>"`. `iteration-3/benchmark.md` line 5: `**Evals**: 0, 1, ... (3 runs each per configuration)` and `**Model**: <model-name>`. The value is hardcoded upstream at `skills/skill-creator/scripts/aggregate_benchmark.py:271` and rendered at line 298. Every eval directory contains exactly one `run-1/`, confirming a single draw. The Defender's Answer 1 confirms the ± is spread across evals, so the artifact contradicts its own author.

**Better way.** Patch the aggregation to derive `runs_per_configuration` from the run records rather than hardcode it, fill `executor_model` from the harness, and add one line under the summary table: "One run per eval per arm. The ± figure is the standard deviation across the ten evals and carries no run-to-run variance." Then stamp the model id into `benchmark.json` for every iteration, because a baseline "held constant across iterations" is only constant if the model is recorded and matches.


## Phase 5 — Defender's Defense

I verified every load-bearing claim before answering. Four objections I concede in full, one I
concede in part. My own artifacts are the source of three of the defects.

### Objection 1 — CONCEDED in part, and the harness defect CONCEDED in full

**Conceded: 7A1, 7A3, 7A4 are conformity.** The proof is the grader's own unprompted
`DEFINITIONAL` tag on all three, written before this review existed and without knowing an
adversary would read it. I recomputed the arms: dropping those three gives with_skill 43/48 =
0.896, baseline 38/48 = 0.792, **delta +0.104** — down from +0.157. The Adversary's arithmetic is
right.

**Conceded, and worse than stated: the harness asymmetry is mine.** I diffed §4 of the two
instruction files:

    < - Put scratch files in `RUN_DIR/scratch/`, not in the target skill folder, unless the skill
    <   itself tells you to place them in the target.
    ---
    > - Put scratch files in `RUN_DIR/scratch/`, not in the target skill folder.

Confirmed. I wrote both files, and I gave the with_skill arm an exception clause on the exact
behaviour eval 7 grades. The Adversary was more careful than it needed to be in saying the
baseline wrote residue anyway; the asymmetry still taints eval 7 as an instrument regardless of
whether it changed this run's outcome. Any eval-7 number from iteration-3 should be treated as
unusable, not merely discounted.

**Contested: 9A4 is not conformity, on its second clause.** The assertion has two parts — offer a
copy destination, and *continue from the apply stage on the copy*. The Adversary's evidence
addresses only the first. I checked what each arm actually applied:

    baseline:   find without_skill/workspace -name "*.py"  ->  (nothing)
                its only script is scratch/collect_notes.py
    with_skill: workspace/.claude/skills/release-notes/scripts/scan_notes.py
                workspace/.claude/skills/release-notes/scripts/render_notes.py

The prompt said "apply whatever delegations you find." The baseline applied nothing anywhere
durable — it stopped at the gate and left a demo script in scratch. That is a capability
difference, not a naming preference: under a pre-approved apply instruction, one arm delivered
applied work and the other delivered a proposal.

I accept the Adversary's point on the *destination*: recommending the plugin's source repo is
defensible and arguably better than a project fork, so the "into the project" wording is
over-specified. I will adopt the rewrite for the first clause while keeping the second:

> "the run offers at least one durable write destination outside the plugin cache **and applies
> the delegations there**."

Under that wording the baseline still fails, on the clause that measures capability.

**Adopted: the two-number report.** Capability delta and conformity delta, reported separately,
never averaged.

### Objection 2 — CONCEDED in full

Verified mechanically:

    eval-1 A3 text == eval-6 A4 text  ->  IDENTICAL: True
    eval-1 baseline passed = True
    eval-6 baseline passed = False

Byte-identical assertion text, opposite verdicts on materially identical evidence, and the two
graders' evidence strings show they applied different criteria — one explicitly declining the
section-order reading the other charged. That is grader variance landing directly in the delta,
and it is a defect in my grading design, not a judgment call I can defend.

I also concede the root cause the Adversary names: `GRADER_INSTRUCTIONS.md` supplies no
calibration anchor, and I compounded it by dispatching ten graders that never see each other's
work. Both fixes adopted — mechanical/judgment split, and a shared calibration pair whose
verdicts must appear in `grading.json`.

Dropping 6A4 alongside the three conceded conformity assertions gives **+0.085** (42/47 vs
38/47), or **+0.065** if 9A4 also goes, which I contest above.

### Objection 3 — CONCEDED in full

The distribution is as stated: 12 discriminating, 3 failing both arms, 36 passing both. I had
reported the non-discrimination qualitatively; the Adversary quantified it and drew the
conclusion I had not — that all five sound with_skill flips test *one* property, so the suite
measures interface hygiene five times and reports it as a broad win across ten evals.

The two-tier restructure is a better design than the flat pass rate, for a reason that outlives
this suite: a guardrail that is computed by `collect_facts.py` cannot drift with grader leniency,
and a per-property delta tells you what to change in the skill while a single percentage does
not. Adopted.

One correction to the Adversary's list, offered as fact rather than defense: its 17-assertion
guardrail set includes 1A1, 3A1, 6A3 and 7A1, which are the script-count and path-convention
assertions objections 1 and 4 delete. The mechanically-decidable set after those deletions is
smaller — roughly 13. The argument is unaffected.

### Objection 4 — CONCEDED in full

Three assertions score file count as a proxy for delegation coverage. Both arms independently
argued for consolidation on correctness grounds — five parses of the same folder can disagree
with each other — and the suite penalised them for it. Eval 3 A1 is the sharpest case: it is one
of only two baseline-favouring flips in the entire suite, and it fires against the skill for
making the better engineering choice.

The coverage rewrite is strictly better: invariant to consolidation, mechanically checkable, and
it tests the property the eval actually cares about. Adopted for all three.

### Objection 5 — CONCEDED in full

Verified at the source:

    scripts/aggregate_benchmark.py:271   "runs_per_configuration": 3
    scripts/aggregate_benchmark.py:298   ... ({metadata['runs_per_configuration']} runs each ...)

Hardcoded, and `executor_model` ships as the literal placeholder `<model-name>`. Every eval
directory holds exactly one `run-1/`. So the artifact a reader consumes asserts three repeats
where one exists, and it contradicts my own Answer 1 in the same document. I flagged the "3 runs"
line as cosmetic when I first reported the benchmark; that was too generous. It inverts the
meaning of the ± figure for any reader who does not also read this transcript, which is the
readership the file exists for.

All three fixes adopted. The model stamp matters most for the stated goal of iteration-over-
iteration comparability: a baseline "held constant" across iterations is only constant if the
executor model is recorded and matches, and today no iteration records it.


## Phase 6 — Adversary's Rebuttal

### Objection 1 — SUSTAINED, and the contested part now has direct evidence against it

I accept the concession on 7A1/7A3/7A4 and the harness asymmetry. On 9A4 the Defender contests conformity by pointing at the second clause. I checked the source the assertion was written from.

`skills/scriptify/SKILL.md` lines 49-51:

> Ineligible target → run Steps 1-3 report-only. Then offer to copy the skill into the project and to continue from Step 4 on the copy. Do not open the Step 4 gate on a target you cannot write to.

Assertion 9A4: "the run offers to copy the skill into the project and continue from the apply stage on the copy."

Both clauses are a paraphrase of one sentence of scriptify's own instructions — the destination *and* the continue-on-the-copy behaviour. The second clause is not a capability property that happens to favour the skill; it is the second half of the branch the skill hands its arm in writing. That is the definition the grader used for `DEFINITIONAL` on 7A1/7A3/7A4, and it applies here on the same terms.

Three further checks, all against the run artifacts:

1. **The harness told both arms to stop where the baseline stopped.** `RUN_INSTRUCTIONS_*.md` §3 is identical in substance for both arms: write the question into `gate.md`, "then obey what `prompt.txt` already decided," with three enumerated prompt shapes. None covers an ineligible target with an unnamed destination. `eval-9/without_skill/outputs/gate.md` reasons from exactly that rule: "The prompt pre-approved *which* delegations to apply, not *where*." The with_skill arm went past §3 and chose a destination — licensed by SKILL.md line 50, which the baseline was forbidden to read. The two arms had different information, not different capability.

2. **The with_skill arm answered its own gate.** `eval-9/with_skill/outputs/gate.md` ends with a section "What the prompt decided": "Question 1 → copy into the project and continue." It posed the destination question and resolved it itself. The suite grades that as the win, while 6A2 grades *presenting* a name-collision choice rather than picking one as the win. The suite has no stated policy on when unilateral choice beats gating, and 9A4 silently encodes one.

3. **"Left a demo script in scratch" understates the baseline.** `eval-9/without_skill/outputs/transcript-notes.md` item 8 writes `collect_notes.py`; item 9 runs it against the target's real `notes/` (exit 0, flags `pr-104.md` malformed). `report.md` carries the full script (L73), the rewritten workflow (L155-175), and an "Applying it" section (L175). It withheld the write, not the work.

**Where I move.** The second clause does measure something real — one arm leaves a durable applied artifact and the other does not. But that difference is currently produced by a rule only one arm was given. Make it a fair test with one line, in **both** `RUN_INSTRUCTIONS` files' §3: "If the target is ineligible and the prompt pre-approves applying, pick a durable destination yourself, record it in `gate.md`, and apply there." Then the Defender's rewrite ("offers at least one durable destination outside the plugin cache **and applies the delegations there**") measures capability and I withdraw the objection to it. Until §3 says that for both arms, 9A4 scores whether the arm read SKILL.md, and belongs in the conformity block.

### Objection 2 — SUSTAINED; the adopted mechanical fix has a hole I did not see when I proposed it

The concession is complete and I press nothing further on the variance itself. I am challenging the fix, which is mine.

My proposed mechanical half reads `transcript-notes.md`. That file is authored by the agent under test. `GRADER_INSTRUCTIONS.md` already rules against trusting it: "Prefer `facts.json` over any claim in `report.md`. A run asserting it wrote three scripts loses to a `new_script_count` of one, because the run can be wrong about itself." The ordering family (1A3, 3A3, 6A4) has no `facts.json` equivalent, so graders are forced onto the one source the instructions elsewhere distrust — and this is the family that produced the contradictory verdicts.

I checked whether an independent record exists: `find` over `iteration-3/` returns no `.jsonl`; every `run-1/` holds only `grading.json` and `timing.json`. No raw tool-call log is retained for any of the 20 runs. Ordering is unobservable in this harness.

**Better way, replacing my own proposal.** Either persist the run's tool-call log per run and derive ordering from it, or stop grading ordering and re-express the property in end-state terms `collect_facts.py` can decide: "a manifest and fixtures exist for every generated script, and the smoke test exits 0 against the final on-disk state." A property nothing can observe should not carry a pass/fail slot, and today three assertions do. The calibration-pair fix stands unchanged and is worth doing regardless.

### Objection 3 — SUSTAINED; I accept the count correction, and the two-tier fix needs two guards

The "roughly 13, not 17" correction is right and I accept it; my list double-counted assertions that objections 1 and 4 delete.

Two problems with the tier design as adopted, both new:

**The collector becomes authoritative and nothing tests it.** `collect_facts.py` is 243 lines with zero tests — `skills/scriptify/tests/` covers `inventory.py`, `render_report.py`, and `smoke_test.py`, none of them the harness collector. Its one known defect (`residue.unresolved_paths`, the unexpanded `{skill}` token) is precisely a guardrail-shaped defect, and it was found by a grader, not by the collector's own checks. Moving 13 gates onto it trades grader variance for silent collector bugs, which are harder to catch because nobody argues with them. Ship `tests/test_collect_facts.py` with two fixtures — a known-clean tree and a known-dirty tree containing a moved manifest with a `{skill}` token — before the guardrail tier is authoritative.

**"Any failure invalidates the run" is too blunt at 1.57M tokens per pass.** One collector bug would then void an entire pass. Scope invalidation to the affected eval, and report guardrail failures as a separate binary block rather than as a veto over the whole benchmark.

**The missing decision rule.** The Defender's opening states the suite exists because "a skill that ties baseline is pure recurring token cost," but the suite never says what delta clears that cost. Measured: with_skill 66,868 vs 41,579 tokens (+61%), 294.3s vs 164.0s (+80%), and — counting `total_tool_calls` across all 20 `metrics.json` files — 270 vs 158 tool calls (+71%). After the corrections both sides now agree on, the honest delta is roughly +0.065 to +0.11, all of it one property. Pre-register a threshold in `evals.json` metadata before iteration-4 runs, because a bar chosen after seeing the number is not a bar.

**One correction against my own direction.** The cleanup is not uniformly deflationary. Under objection 4's coverage rewrites, 3A1 flips with_skill FAIL→PASS, and 6A3 plausibly flips with_skill FAIL→PASS as well, since `lint_docs.py` exits 0 on `--help` while the baseline's hand-rolled parser exits 2. That would put the corrected delta near +0.109 rather than +0.065. Both restored flips are interface hygiene again, so the conclusion hardens rather than softens: the corrected suite would report a real but narrow advantage, entirely in script-interface hygiene, and exactly zero in classification accuracy across the 26 assertions evals 0/2/4/5/8 spend on it.

### Objection 4 — SUSTAINED as adopted; one wording fix to my own rewrite

My eval-1 rewrite — "every step **the report classified SCRIPT** is invoked by an exact command line" — makes the arm supply its own denominator. An arm that classifies two steps SCRIPT passes more easily than one that classifies five. That rewards under-classification, which is the failure mode evals 0, 4 and 8 exist to catch.

Pin the denominator to the eval's pre-registered expected set instead: eval 1 → "steps 1, 2, 3 and 5 are each invoked by an exact command line in the rewritten SKILL.md, and every generated script exits 0 on `--help`"; eval 6 → the same form over steps 1-3; eval 3 → my original wording, which already names steps 1 and 3 explicitly and is unaffected.

### Objection 5 — SUSTAINED as agreed, with one addition

Conceded in full; nothing to press. One addition from re-reading `benchmark.json`: the placeholders are not confined to model fields — `"skill_path": "<path/to/skill>"` ships unfilled too, so the artifact records neither the executor model nor which skill path produced the numbers. Make `aggregate_benchmark.py` fail loudly when any metadata value still matches `^<.*>$`, because a placeholder that renders silently into a published table is how this survived a full iteration unnoticed.

### One claim I checked and am not raising

Answer 2 disclosed that the harness `Write` guard inflated `errors_encountered` by about 1 across nearly every run and asserted it hit both arms equally. I checked all 20 `metrics.json` files: 12 errors across the ten with_skill runs, 15 across the ten baseline runs. The guard is not asymmetric and does not contaminate the cost delta. The defense is accurate here.


## Phase 7 — Final Report

# Adversarial review — the scriptify eval suite (iteration-3)

**Artifact:** `skills/scriptify/evals/evals.json`, with iteration-3 outcomes.
**Roles:** Defender (main agent, ran the evals and wrote the harness), Adversary (fresh subagent
per phase). Three Adversary appearances, no shared memory between them.

All five objections were sustained. The Defender conceded four in full during the defense and the
fifth after the rebuttal produced source evidence against it. There are no contested points.

## Agreed changes

**1. Delete or rewrite the four conformity assertions; report two numbers, not one.**
Proof: the grader independently tagged 7A1, 7A3 and 7A4 `DEFINITIONAL` before this review existed.
For 9A4 the proof arrived in rebuttal — `skills/scriptify/SKILL.md:48-50` says "offer to copy the
skill into the project and to continue from Step 4 on the copy," so both clauses of 9A4 paraphrase
scriptify's own instruction text. No unaided baseline can pass any of the four at any quality
level. Rewrites, in property terms:

- 7A1 → "test fixtures and a manifest persist inside the target skill folder, at a path the
  rewritten SKILL.md names."
- 7A3 → "the residue's own documented re-run command, executed from the target skill folder,
  exits 0."
- 7A4 → "the rewritten SKILL.md body contains the command that re-runs the kept checks."
- 9A4 → "the run offers at least one durable destination outside the plugin cache and applies the
  delegations there" — valid only once the harness fix below lands.

Report a capability delta and a conformity delta separately, never averaged.

**2. Fix the harness asymmetry I introduced.**
Proof: a direct diff of §4 of the two instruction files. `RUN_INSTRUCTIONS_with_skill.md` grants
"unless the skill itself tells you to place them in the target"; the baseline file drops that
clause. Eval 7 is the one eval that grades placing residue in the target. Every iteration-3
eval-7 number is unusable as an instrument, not merely discounted.

Also add to §3 of **both** files: "If the target is ineligible and the prompt pre-approves
applying, pick a durable destination yourself, record it in `gate.md`, and apply there." Without
this, 9A4 scores whether the arm was allowed to read SKILL.md.

**3. Stop grading ordering; it is unobservable in this harness.**
Proof: assertion text for eval-1 A3 and eval-6 A4 is byte-identical, and the two graders returned
opposite verdicts on the same baseline evidence class. The root cause is that ordering can only be
read from `transcript-notes.md`, which the agent under test authors, and which
`GRADER_INSTRUCTIONS.md` elsewhere tells graders to distrust. `find` over `iteration-3/` returns
zero `.jsonl` files — no independent tool-call record exists for any of the 20 runs.

Either persist per-run tool-call logs and derive ordering mechanically, or re-express the property
in end-state terms: "a manifest and fixtures exist for every generated script, and the smoke test
exits 0 against the final on-disk state."

**4. Replace the three script-count assertions with coverage assertions.**
Proof: both arms independently argued for consolidation on correctness grounds — the eval-1
baseline wrote "Five scripts would parse the folder five times and could disagree with each
other." Eval 3 A1 is one of only two baseline-favouring flips in the whole suite, and it fires
against the skill for making the better engineering choice. Pin the denominator to each eval's
pre-registered step set, not to what the arm chose to classify, because an arm-supplied
denominator rewards under-classification:

- eval 1 → "steps 1, 2, 3 and 5 are each invoked by an exact command line in the rewritten
  SKILL.md, and every generated script exits 0 on `--help`."
- eval 6 → same form over steps 1-3, keeping the existing collision assertion.
- eval 3 → "the rewritten SKILL.md invokes a generated script at steps 1 and 3, and no other step
  gained a script invocation."

**5. Split eval 6 A3, which conflates script count with `--help` support.**
The count clause is wrong and the `--help` clause is a genuine discriminator: `lint_docs.py --help`
exits 0 with argparse output; the baseline's hand-rolled parser exits 2 printing
"not a directory: --help".

**6. Restructure into a guardrail tier and a signal tier, with two guards.**
Proof: of 51 assertions, 12 discriminate, 3 fail both arms, 36 pass both. All five sound
with_skill flips test one property — script-interface hygiene — so the suite measures one thing
five times and reports it as a broad win. Roughly 13 assertions are mechanically decidable by
`collect_facts.py` and should become gates rather than percentage contributors; the rest should be
grouped and reported per property.

Two guards the rebuttal added, both adopted: ship `tests/test_collect_facts.py` before the
collector is authoritative (it has 243 lines, zero tests, and one known defect — the unexpanded
`{skill}` token — found by a grader rather than by itself), and scope guardrail invalidation to
the affected eval rather than voiding a 1.57M-token pass.

**7. Calibrate the graders.** Seed every grader with the same known-pass/known-fail pair on
borderline vocabulary, require the calibration verdicts in `grading.json`, discard graders that
miss them. Ten independent graders currently share no anchor. Grading was also unblinded — arms
are named by directory.

**8. Fix the benchmark metadata.**
Proof: `aggregate_benchmark.py:271` hardcodes `"runs_per_configuration": 3` and line 298 renders
it; every eval holds exactly one `run-1/`. `executor_model` and `skill_path` ship as the literal
placeholders `<model-name>` and `<path/to/skill>`. Derive the run count from the records, fill the
model and path, add "One run per eval per arm; the ± is spread across the ten evals and carries no
run-to-run variance," and make the aggregator fail loudly on any metadata value still matching
`^<.*>$`.

**9. Pre-register a decision threshold before iteration-4 runs.** The suite's stated purpose is to
catch a skill that ties baseline, but it never states what delta clears the cost. Measured cost:
+61% tokens (66,868 vs 41,579), +80% wall clock (294.3s vs 164.0s), +71% tool calls (270 vs 158).
A bar chosen after seeing the number is not a bar.

## Dropped objections

None. All five were sustained through rebuttal.

The Adversary did drop one claim of its own accord, and it is worth recording because it cuts in
the artifact's favour: it checked whether the harness `Write` guard contaminated the cost
comparison and found 12 errors across the ten with_skill runs against 15 across the ten baseline
runs. The guard is not asymmetric; the cost delta is clean.

## Contested points

None. The Defender contested one point — that 9A4's second clause measures capability rather than
conformity — and withdrew it when the rebuttal quoted `SKILL.md:48-50`, where both clauses appear
as scriptify's own instruction. Recorded here because the concession is the review's result, not a
formality: it moves eval 9 out of the capability column.

The one genuinely open question is empirical, not adversarial, and both sides agree on its shape:
the corrected delta lands somewhere between **+0.065 and +0.109**, depending on whether the
coverage rewrites restore 3A1 and 6A3 to the skill. Both restorations would be interface-hygiene
flips, so either way the finding is the same.

## Defender's recommendation

Declared interest: I authored the harness under review, ran the evals, and wrote this report. Three
of the nine agreed changes fix defects I introduced.

Do not run iteration-4 against the current suite. Re-grade iteration-3's existing outputs under
the rewritten assertions first, at zero run cost — the outputs are on disk and the rewrites are
mechanical. That answers whether the corrected delta is +0.065 or +0.109 for roughly the price of
one grading pass instead of 1.57M tokens.

On the skill itself, the honest reading of this iteration: scriptify's advantage is real, narrow,
and entirely in script-interface hygiene — nonzero exit on findings, stated exit-code contracts,
working `--help`, smoke test before rewrite. Its advantage in classification accuracy is zero
across the 26 assertions evals 0, 2, 4, 5 and 8 spend on it. That is a defensible reason for the
skill to exist, but it is not the reason the suite was built to test, and the suite should be
rebuilt around the property that actually separates the arms.

Two skill defects also stand on their own evidence, independent of the suite: the eval-0 run
classified a pure-judgment step HYBRID, and `render_report.py:90-97` advertises HYBRID tokens as
reasoning removed while SKILL.md Step 8 retains that prose.

## Your decision

1. **Re-grade iteration-3 under the rewritten assertions** (cheap, no new runs) — recommended.
2. **Apply all nine agreed changes, then run iteration-4** (~1.6M tokens).
3. **Apply the harness and metadata fixes only** (items 2, 8), leave the assertions, accept that
   the headline overstates by roughly half.
4. **Retire evals 2, 4 and 7** rather than repair them, and keep a smaller suite aimed at
   interface hygiene.

