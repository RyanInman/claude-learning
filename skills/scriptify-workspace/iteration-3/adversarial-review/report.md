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
