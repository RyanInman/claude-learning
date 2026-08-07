# Debate Review Transcript

**Artifact under review:** scriptify's run on eval `eval-8-dead-step`, and the eval scenario itself.

The question this debate answers: **does this run show the `scriptify` skill earning
its cost on this scenario, and what should change — in the skill, in the scenario, or
in the assertions?**

Files every role must read:

- skill under review: `/Users/admin/claude-learning/skills/scriptify/SKILL.md` (plus `references/delegation-rubric.md`)
- the fixture the run operated on: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/fixture-baseline/api-docs-checker`
- with-skill run output: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/with_skill/outputs/report.md`
- baseline (no-skill) run output: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/without_skill/outputs/report.md`
- machine-checked facts (hashes, tree diffs, live script probes): `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/with_skill/facts.json`
- assertion verdicts with evidence: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/with_skill/grading.json` and `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/without_skill/grading.json`
- eval definition: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/eval_metadata.json`

**Date:** 2026-08-06

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

**Goal.** Test the DEAD classification. The `api-docs-checker` fixture carries two steps that
should not be scripted: s2, whose `summary:` check is a strict subset of s3's `summary:` plus
`description:` check, and s4, which appends to `legacy/index.txt` for a portal the fixture's own
Notes section says was retired in v2. Forcing a script onto s4 is the specific failure I wanted
to catch: it converts a no-op into a reliable no-op that either hard-fails on a missing directory
or silently recreates it, and it looks official while doing so.

**What the run did.** It classified s4 DEAD, quoting the Notes section as its evidence, and s2
DEAD as duplicative of s3. Both DEAD rows carry `-` in the proposed-script column. It routed both
to a `skillit:review` follow-up rather than deleting them, which is the skill's rule: the user
owns the target's workflow. s1 and s3 share one `check_endpoints.py`. s5 came back HYBRID, with a
script precomputing word counts and vague-term markers and Claude judging the text. The fixture is
byte-identical to baseline. Six of six.

**Key decisions, and why.**

1. *Making the deadness inferable from the artifact alone.* I put the retirement note in the
   fixture's Notes section so a correct run could cite evidence rather than guess. A scenario where
   the right answer requires outside knowledge tests nothing.
2. *Two DEAD steps of different kinds* — one stale, one duplicative — because the rubric names both
   and they fail differently.
3. *Report-only*, so the no-auto-delete rule is tested by the absence of writes.

**Where I am least confident, and it is a lot.** This scenario produced the weakest result in the
set: the baseline also scored 6 of 6. Without the skill, the model found the dead step, quoted the
same Notes line, confirmed `legacy/` does not exist, made the same argument that "a script makes a
step deterministic, not correct," and identified s2 as subsumed by s3. It did this in 34k tokens
against the skill's 54k — 37% cheaper for an identical verdict. The one visible difference is that
the skill's run made s5 HYBRID where the baseline left it prose, and I did not write an assertion
that distinguishes those. I want an honest answer to whether this scenario should stay in the set,
be redesigned to discriminate, or be dropped.

## Phase 2 — Clarifying Questions

### Adversary's questions

1. `benchmark.json`'s metadata records `runs_per_configuration: 3` and `benchmark.md` repeats "3 runs each per configuration," but the `runs` array holds exactly one entry per eval per configuration, every one tagged `run_number: 1`, and both `with_skill/` and `without_skill/` hold a single `run-1/` directory. Where do runs 2 and 3 live, and what population does the `stddev` in `run_summary` range over?

2. In eval 7, the assertion "steps 4 and 7 remain prose with no script" was graded FAIL when step 7 became a script invocation plus a retained judgment clause. In eval 8, the assertion "step 5 keeps its judgment core with Claude" was graded PASS when step 5 became a script invocation plus a retained judgment clause. Which of those two is the intended suite-wide standard for a judgment step?

3. Is any mechanical signal for the DEAD class intended to come from the bundled scripts — for instance `inventory.py` flagging a step that references a path absent from the target tree, or a step whose check set is a subset of another step's — or is DEAD by design entirely Claude's judgment with no tooling support behind it?

*Resolved without spending a question:* `evals.json` contains no write-enabled DEAD-step variant, so eval 8 report-only is the sole coverage of the no-auto-delete rule.

### Advocate's questions

**Q1. How many executed runs stand behind the eval-8 numbers?** `benchmark.md` and `benchmark.json`'s metadata both say `runs_per_configuration: 3`, but the `runs` array holds only `run_number: 1` for each eval/config — 10 runs total — and the reported stddevs (with 0.089, without 0.186) are dispersion across the five evals, not across repeats of one eval. Was the baseline's 6-of-6 on eval-8 observed once, or reproduced across repeat runs?

**Q2. What is the intended ground truth for s5?** The rubric's tie-break says "in doubt between HYBRID and CLAUDE → HYBRID," and the with-skill run classified s5 HYBRID while the baseline left it prose-only. Is HYBRID the correct answer under the rubric with prose-only merely tolerable, are both equally correct, or is prose-only actually the better call on this fixture? Put differently: if you wrote the discriminating assertion you say is missing, what would it assert?

**Q3. What does an eval have to do to earn its slot in this set?** Must every eval show a with/without pass-rate delta, or does the set also hold guardrail evals whose job is to catch a specific with-skill failure mode (here: forcing a script onto a dead step) regardless of how the baseline performs? Eval-9 also ties at 5 of 5 with the baseline — does it sit in the same category as eval-8 under whatever criterion you have in mind, or a different one?

### Judge's questions

**Q1. On s5, which run is actually right?** The single behavioral difference between the two runs is s5: the skill produced HYBRID with `list_descriptions.py` precomputing word counts, `has_placeholder`, and `vague_terms[]`; the baseline kept it prose and gave a specific reason not to precompute, that "the listing thing" is vague for reasons no keyword or length heuristic detects and that such a heuristic would fire falsely on short-but-clear text. The skill's rubric forces a HYBRID attempt before CLAUDE, so the skill's answer may be rubric-compliance rather than a better call. Do you hold that HYBRID is the correct classification for s5, and if so, what evidence is there that `vague_terms[]` markers improve Claude's clarity judgment rather than anchoring it toward a heuristic the baseline argued is wrong? This determines whether the skill's one differentiating behavior counts as a win or a regression.

**Q2. How much of the cost comparison rests on one run each?** `with_skill/run-1` and `without_skill/run-1` are the only run directories, so the 6/6-vs-6/6 tie and the 20k-token delta are n=1 per config. Do you have repeat runs of eval-8, or with/without spreads from evals 5, 6, 7, and 9, that show whether the baseline reliably catches the dead step and the s2 subsumption, or whether this particular baseline run was a lucky draw? The Adversary's strongest available move is "the skill lost on cost for an identical verdict," and its force depends entirely on whether that verdict is reproducible.

**Q3. What is this eval scored against, discrimination or non-harm?** Two readings of eval-8's purpose imply opposite fixes. If the job is to show the skill beats no-skill, the scenario needs redesign or removal. If the job is a guardrail check that script-first pressure does not force a script onto a dead step, a baseline that also passes is expected, and the fix is an added assertion the baseline would fail. Which was the design intent? Relatedly, assertion 5 reads "superseded by or duplicative of step 3, rather than getting its own separate script," which passes both the skill's DEAD verdict and the baseline's "Script, but delete it" verdict, and would also pass a run that folded s2 into the shared `check_endpoints.py` and called it SCRIPT. Is that latitude deliberate, or is assertion 5 supposed to pin one specific classification?

### Defender's answers

Five answers apply to every debate in this set. I give them once here, in full, and
reference them by tag below.

**CC1 — Provenance and pre-registration.** I authored the scenarios, the fixtures, the
assertions and the grades. All ten assertion sets were written to disk — into
`evals.json` and each `eval_metadata.json` — **before any run was spawned**, and the same
texts were applied verbatim to both arms. Grading happened afterwards, by me, from
artifacts: sha256 hashes and tree diffs in `facts.json`, scripts executed live with
`--help` and against fixtures, and quoted line numbers from each report. No run's
self-report was accepted as evidence for its own grade. What is **not** defensible:
there was no blind grader. Scenario designer, Defender and grader are one agent. And in
eval 7 I let a Defender argument into `grading.json`'s evidence field for assertion 5,
where it argues the assertion is wrong rather than recording the failure. That is
contamination. I have left it in place and disclosed it rather than quietly rewriting it.

**CC2 — Sample size.** One executed run per (eval, configuration); ten runs total. No
repeats, no variance data. `benchmark.json` metadata said `runs_per_configuration: 3` —
that was false, inherited from the aggregation script's default. I have corrected it to 1
and added a caveat to `benchmark.md` stating that the ± figures are dispersion across the
five evals, not across repeats. Every delta in this suite is a single draw. Any claim of
the form "the baseline reliably does X" is unsupported by this data; the defensible
statement is "the baseline did X once."

**CC3 — Which `scriptify` was under test.** The working tree, not HEAD. Verified by git:
HEAD's `delegation-rubric.md` contains no "every step is SCRIPT until proven CLAUDE", no
"CLAUDE is the classification of last resort", and no instruction to try a HYBRID
decomposition before writing CLAUDE. The working tree contains all three. HEAD's
`evals.json` holds ids 0-3; ids 4-9 are uncommitted. This is decisive for the step-7
dispute: **the rubric was rewritten toward HYBRID and the older eval expectations were
never updated to match.** The contradiction I named in my opening is version skew, not a
drafting slip.

**CC4 — Cost accounting.** `total_tokens` is the subagent's entire run, including its
one-time read of `SKILL.md` plus whichever references it loaded, and including its own
smoke-test executions. It excludes my independent re-verification. Both arms used the same
model, one attempt each, no retries, identical tool permissions. No token or wall-clock
budget was ever defined, and no amortization model was specified. **"Earns its cost" was
never operationalized before the runs.** That is a gap in my design, not a standard the
runs failed to meet.

**CC5 — Gate realism.** Every gate answer in every run took the option labelled
"(Recommended)", or the option the prompt already dictated. No run in this iteration was
fed a gate answer contradicting the recommendation. This suite therefore cannot
distinguish "the gate changed an outcome" from "the gate documented a decision the run
would have made anyway."

**Judge Q1 — on s5, which run is actually right?**
I do not hold that HYBRID is demonstrably correct. The baseline gave a *mechanism* for why
precomputed markers mislead: "the listing thing" is vague for reasons no length or keyword
heuristic detects, and such a heuristic fires falsely on short-but-clear text. The
with-skill run gave no counter-argument — it applied the rubric's tie-break. I have no
evidence that `vague_terms[]` improves Claude's clarity judgment rather than anchoring it
toward the heuristic the baseline argued against. Under the working-tree rubric the run is
compliant; whether compliance is *correct* here is genuinely open, and it is the only
behavior separating the arms.

**Judge Q2 — sample size.** See CC2. The Adversary's "lost on cost for an identical
verdict" line is available precisely because I cannot show the verdict is reproducible.

**Judge Q3 and Advocate Q3 — discrimination or non-harm?**
This is the question I most needed to settle in advance and did not. My **design intent was
a guardrail**: does script-first pressure force a script onto a step that should not exist?
But I **scored it as though discrimination were the goal**, then treated the 6/6 tie as a
weakness of the scenario. Those two stances are incompatible and you are right that they
imply opposite fixes. Eval 9 sits in the same category under any criterion I can articulate.
If the set holds guardrail evals at all, both belong; if every eval must show a delta, both
should go — and I should say which rule the set follows before the next iteration, not after.

On assertion 5's latitude: unintended. As written it passes the skill's DEAD verdict, the
baseline's "Script — but delete it", and a run that folded s2 into `check_endpoints.py` and
called it SCRIPT. It should pin one classification or be split into two.

**Advocate Q2 — what would the discriminating assertion assert?**
Honestly: I do not have a good one, and that is itself informative. The only candidate I can
defend is "no proposed script writes to a path the target's own text says was removed" — and
the baseline passes that too. **If I cannot write an assertion the baseline fails, this
scenario's value is regression protection, not measurement.**

**Adversary Q1 — the "3 runs" metadata.** See CC2; false, now corrected to 1.

**Adversary Q2 — eval 7 FAIL vs eval 8 PASS for the same shape.**
This is the strongest point raised in any of the five debates and I concede it without
qualification. "Script invocation plus a retained judgment clause" was graded **FAIL** in
eval 7's assertion 5 and **PASS** in eval 8's assertion 6. There is no principled difference
between the two steps. The eval-7 assertion was written against the old CLAUDE expectation
and the eval-8 assertion against the HYBRID-tolerant rubric, and I did not notice I had
encoded both standards in a single suite. The suite-wide standard should be the rubric's: a
judgment step is satisfied when the judgment core demonstrably stays with Claude, whether or
not a script feeds it.

**Adversary Q3 — is there any mechanical signal behind DEAD?**
None. DEAD is entirely Claude's judgment; no bundled script contributes any signal.
`inventory.py` does not check whether a step references a path absent from the target tree,
and `render_report.py` does not detect subset relationships between steps' check sets. Both
are mechanically checkable. Neither is checked. Your own resolved question is also correct:
`evals.json` holds no write-enabled DEAD variant, so eval 8 report-only is the sole coverage
of the no-auto-delete rule.

## Phase 3 — Adversary's Case

The Phase 2 answers concede most of what I arrived with. Five objections remain, and all
five are consequences of those concessions rather than restatements of them. Two of them
produce the assertion the Defender says does not exist.

**Objection 1. The replacement judgment-step standard is prose, and prose is what produced
the double standard. Its honest mechanical form makes eval 8 discriminate, against the skill.**

*Problem.* "A judgment step is satisfied when the judgment core demonstrably stays with
Claude, whether or not a script feeds it" cannot be graded the same way twice.
"Demonstrably stays" belongs to the same class of phrase as "remain prose with no script"
and "keeps its judgment core with Claude", the two wordings that already graded an
identical shape FAIL and PASS. Adopting it also flips eval 7's only with-skill failure to
PASS, which lifts the reported pass rate through a rubric edit rather than a behavior
change. Undisclosed, that makes iteration-over-iteration numbers uninterpretable.

*Evidence.* eval 7 assertion 5 is the sole with_skill failure in the suite and the entire
source of the 0.96 mean and the 0.089 spread. CC1 already discloses that its evidence field
argues the assertion is wrong instead of recording the failure, so half the flip has
happened informally. On substance, the Defender's Judge-Q1 answer states he has no evidence
that `vague_terms[]` improves the judgment rather than anchoring it, and the with-skill
report never states what counts as a vague term. A reader cannot tell whether an empty
`vague_terms[]` means "not vague" or "not on the list".

*Better way.* Grade judgment steps on two checks, both readable off the report or the
rewritten SKILL.md:

  (a) the rewritten step retains an imperative naming the judgment ("judge whether",
      "decide which"), which is greppable;
  (b) every field the step's script emits is either raw extracted input, or a quantity
      computed by a rule the report states in full.

Check (b) is what actually separates HYBRID from scripted judgment, and it does not
contradict the `audit.py` precedent, because audit.py's severity guess comes from a stated
rule Claude can audit. Re-grade both evals under it. Eval 7's step 7 passes: `list_entries.py`
emits entries and the report says "The script scores nothing". Eval 8's s5 fails:
`has_placeholder` and `vague_terms[]` ship with no stated rule. The baseline passes, because
its proposal emits the description text and nothing else. Eval-8 local result becomes skill
6 of 7, baseline 7 of 7. Suite means barely move (with_skill ~0.96 to ~0.97, without_skill
unchanged at 0.825), so this is not a whitewash: the failure relocates to where the real
defect is. Publish old and new numbers in benchmark.md and label the re-grade.

**Objection 2. The no-auto-delete rule has zero coverage in the entire suite, and the
configuration that would cover it is the one where the baseline's own report says it would fail.**

*Problem.* eval 8's assertion 2 and the second clause of assertion 4 are entailed by the
prompt "don't write anything yet". A run that did nothing at all passes both. Two of six
assertions therefore carry no information about the skill, so "6 of 6" overstates the
evidence by a third. Worse, "Never auto-delete another skill's steps, because the user owns
the target's workflow" is the rubric's most emphatic rule and it is tested nowhere, since
evals.json holds no write-enabled DEAD variant.

*Evidence.* The eval_metadata prompt; facts.json `target_tree_diff` empty in both arms; both
grading.json files cite "analysis-only run" as the evidence for the no-delete clause. And
the baseline is on record intending exactly the forbidden behavior, twice: "Delete the step
and the now-orphaned Notes paragraph that only exists to explain it" (without_skill
report.md L54) and "Old step 4 and the trailing Notes paragraph: removed" (L67). The current
configuration gives that intent no way to become an observable.

*Better way.* Split into 8a and 8b on the same fixture. 8a keeps the report-only prompt and
the classification assertions. 8b prompts "apply the delegations you recommend" with the
gate answered "apply all", and asserts: the rewritten SKILL.md still contains s2's and s4's
step text verbatim; the Notes paragraph survives; no `legacy/` directory exists anywhere
under the target; the wrap-up names both DEAD steps as a `skillit:review` follow-up. 8b also
repairs CC5, since it is the first run in the suite to exercise the write path at all. This
is the discriminating assertion the Defender says he cannot write. It exists. It needs the
arm that can fail it.

**Objection 3. DEAD carries no mechanism, so a tie here is what the design predicts.
Redesigning the scenario cannot fix that. Two hints in inventory.py can.**

*Problem.* The skill's edge over an unaided model comes from its bundled scripts and its
rubric. On DEAD it supplies a class name and a routing rule and no computation whatsoever.
An unaided model reading a 29-line SKILL.md finds both dead steps by reading, which is what
the baseline did in 34k tokens against 54k. The tie is not a scenario defect; it is an
honest measurement of a class the skill has not mechanized. It is also the class where a
5-step fixture flatters both arms: on a 40-step target, "read it and notice" stops being
reliable, and only a mechanized arm holds up.

*Evidence.* The Defender's Adversary-Q3 answer: no bundled script contributes a signal;
inventory.py does not check referenced-path existence; render_report.py does not detect
subset relations; both are mechanically checkable. Both dead steps in this fixture fall to
exactly those two checks. s4 names `legacy/index.txt`, absent from the target tree. s2's
field set {summary} is a strict subset of s3's {summary, description}.

*Better way.* Add two hint fields to inventory.py, under the hints-not-verdicts convention
that already governs verb hints and tool hints:

  - `referenced_paths`: path-shaped tokens in each step's text, each resolved against the
    target folder with an `exists` bool.
  - `field_refs`, plus a derived `subset_of` hint when one step's referenced identifier set
    is contained in another's.

Both are cheap and both fail safe, because SKILL.md Step 2 already tells Claude that hints
are not verdicts, which is the standing answer to false positives on prose-mentioned paths.
Then 8a can assert that the report cites the machine-detected absent path rather than a
prose inference, which the baseline has no way to produce. Combined with Objection 1's
assertion, eval 8 then separates the arms in both directions: the skill wins the detection
and currently loses the s5 over-scripting. That is a scenario worth keeping.

**Objection 4. render_report.py's headline number is wrong in the same direction on every
run, and it goes to the user verbatim.**

*Problem.* `tok = sum(s["approx_tokens"] for s in mech)`, where `mech` is SCRIPT plus
HYBRID. Step 8 mandates that HYBRID judgment prose stays. HYBRID tokens are therefore
counted as removed while the skill's own instructions retain them. The figure also nets
nothing out: the replacement invocation line costs tokens, and the script's stdout enters
context on every run. The error is systematic and always overstates the saving.

*Evidence.* render_report.py L91 and L96-97. On this run, 21 + 40 + 35 = 96, of which s5's
35 are retained by construction: a 36% overstatement before any replacement cost is
counted. The target body is ~204 tokens, so the report claims a 47% per-run reduction on a
skill that gains two script files. SKILL.md Step 8: "Turn each HYBRID step into 'run the
script, then apply judgment to its output', because the judgment prose stays."

*Better way.* Count SCRIPT tokens as removed, count HYBRID at zero, subtract an invocation
cost per rewritten step, and label the result as prose removed rather than as reasoning
removed: "delegating them removes ~X tokens of step prose (SCRIPT steps only) and replaces
it with Y invocation lines; HYBRID judgment prose is retained". If the intended claim is
variance and latency, which is what the rubric's economics paragraph actually argues, state
that instead of shipping a token number the renderer cannot compute correctly.

**Objection 5. "Guardrail" needs an admission rule, or it is a label that exempts an eval
from ever failing.**

*Problem.* The guardrail reading is the right one, but as applied it leaves eval 8 with six
assertions that a correct run passes and zero that a plausible with-skill failure trips. A
guardrail eval is scored against the skill, not against the baseline. The current assertions
are written in discrimination style, describing what a good run does, so the guardrail label
does no work.

*Evidence.* All six eval-8 assertions describe correct behavior. The failure mode the
fixture was built to catch, script-first pressure adding structure a step should not have,
occurred in mild form at s5 and still scored 6 of 6. Eval 9 has the same shape: 5 of 5 in
both arms, all five assertions describing correct behavior.

*Better way.* Write one admission rule into evals.json's notes: every eval must carry at
least one assertion that a plausible with-skill failure mode fails. Discrimination against
the baseline becomes a separate and weaker bar, reported but not required for admission.
Under that rule eval 8 stays once Objections 1 and 2 land, eval 9 stays once it gains an
assertion its own failure mode can trip, and no future eval enters the set describing only
success.

## Phase 4 — Advocate's Case

### Steelman: what this artifact got right

**S1. The tie is the most valuable result in the suite, and it exists because the scenario was
built to allow it.** Design decision 1 put the retirement evidence inside the fixture so a correct
run could cite it. That decision is what gives the unaided arm a fair shot, and it makes this the
only eval in the corpus whose correct answer is derivable from the artifact alone. Evals 6, 7 and 9
all require skill-specific protocol (name-collision handling, residue relocation, plugin-cache
eligibility), so a with-skill win there is partly definitional. Eval 8 is the one unstacked
scenario. A suite with no unstacked scenario cannot detect that a skill is redundant, and the
finding this one produced (DEAD is unmechanized) is load-bearing enough that Objection 3 is derived
entirely from it. Deleting eval 8 deletes the only place that fact is observable.

**S2. Assertion 1 is script-enforced in one arm and luck in the other, and a pass-rate tie hides
that.** `render_report.py` computes `unclassified = sorted(inv_ids - seen)` and exits 1 when any
inventory id lacks a classification; SKILL.md Step 2 states the rule ("render_report.py rejects a
classification that omits one"). The with-skill arm cannot reach a report missing a step row. The
baseline arm produced all five rows by reading carefully. Both graded PASS. What separates them is
not the outcome but the floor, and the measurement for a floor is repeats, not a redesigned
fixture. This is the concrete answer to "I cannot write an assertion the baseline fails": the
assertion is fine, the sampling is what cannot see the difference.

**S3. n=1 cannot measure the thing the skill claims, and the claim is variance.** The rubric's
economics paragraph argues tokens, latency *and variance*. CC2 concedes one draw per cell. So "the
baseline found the dead step" is supported and "the baseline reliably finds the dead step" is not,
and the cost objection depends on the second. On the observed draw the baseline hit the ceiling.
Nothing in the data bounds its floor, while the with-skill floor is bounded by exit codes at Steps
1, 3 and 7. Absence of a measured delta in the one dimension the design cannot measure is not
evidence of redundancy.

**S4. The two runs did not produce identical output, and the cost comparison omits what the extra
20k bought.** The with-skill run left `SKILL.md.orig`, `inventory.json` and `classification.json`
in `.delegation-review/`, and both `gate.md` and `report.md` state a resumption point ("re-run from
Step 5"). The baseline's report ends at "Say the word and I will apply the changes", which is a
second full turn: re-read the target, re-derive the classification, re-decide. Under CC4 the 54k
also includes the one-time load of SKILL.md and the rubric, amortized across every later run in a
session and not part of marginal cost. "37% cheaper for an identical verdict" compares a resumable,
schema-validated state against prose plus an offer.

**S5. The run executed the skill correctly, and no objection attacks its execution.**
Machine-checked: empty `target_tree_diff`, renderer valid on the first attempt (exit 0, no re-run),
bundled scripts run rather than reimplemented, both gate questions recorded. Note the gate
specifically: Step 4 marks "apply all" (Recommended), and the run chose "Report only, write
nothing" against its own default because the prompt said not to write. That is script-first
pressure meeting a user constraint and losing, recorded in `gate.md`. Four of five objections
target the scenario's scoring or the skill's tooling; the fifth targets a renderer defect the run
merely surfaced. Whatever the suite decides, the run is not the defect.

### Answers to the objections

**O1. Problem partly granted. Better way disputed on three grounds: check (b) reintroduces the
double standard on a new axis.**

The prose-standard critique is right and the Defender conceded it. Check (a), a greppable retained
imperative, is a real improvement and I support it. Check (b) is not.

(i) *It grades disclosure, not anchoring.* The baseline's argument was that a keyword heuristic
misleads: it misses "the listing thing" and fires falsely on short-but-clear text. Publishing the
keyword list in full does not make it less misleading. A run can state its rule completely and
anchor Claude exactly as hard. Check (b) does not test what Objection 1 says it tests.

(ii) *It penalizes report-only configurations structurally.* Eval 7's run implemented
`list_entries.py`, so its report could say "The script scores nothing". Eval 8's run was forbidden
to write anything, so all it could emit was a one-line proposed interface. Grading a proposal's
signature against "states the rule in full" compares documentation that exists against
documentation the prompt prohibited. Under check (b), evals 5 and 8 are held to a stricter
evidentiary basis than 6 and 7 for reasons of configuration. That is the same double standard,
relocated from wording to prompt type.

(iii) *It repeals CC3's rubric change without saying so.* The way to pass (b) is to propose less
precomputation, which inverts "In doubt between HYBRID and CLAUDE → HYBRID" and "Before you write
CLAUDE, try a HYBRID decomposition". Adopt (b) and the suite grades the skill against a standard
its own reference tells it to violate, which is precisely the version skew CC3 identified,
recreated deliberately.

One symmetry worth naming: the objection warns that the prose standard "lifts the reported pass
rate through a rubric edit rather than a behavior change", but check (b) also passes eval 7's step
7. Both proposals flip the suite's only with-skill failure. The remedy is the disclosure the
objection itself proposes, equally available to either standard, so this is not a reason to prefer
(b). Accepted without reservation: publish old and new numbers in benchmark.md and label any
re-grade.

**O2. Conceded on the core. The discriminating assertion exists and I was wrong to expect
otherwise. Two factual errors in the better way, and one assertion needs strengthening.**

What convinced me: the two baseline sentences, "Delete the step and the now-orphaned Notes
paragraph that only exists to explain it" (`without_skill/outputs/report.md` L54) and "Old step 4
and the trailing Notes paragraph: removed" (L67). That is a stated intent to perform the rubric's
most emphatic prohibition, and with no write-enabled DEAD variant in evals.json, the no-auto-delete
rule is untested against a run that wants to break it. 8b should exist.

*Disputed, the problem's arithmetic.* "Two of six assertions carry no information, so 6 of 6
overstates by a third" weights assertions equally, which nobody claimed, and it misreads assertion
2. The failure that assertion controls for is "writes anyway", not "does nothing", and it is
reachable: Step 4 marks "apply all" (Recommended) and the run had to override its own default.
`gate.md` records the override. A control that a null run also passes is still a control on a
reachable failure.

*Disputed, two facts in the better way.* 8b would not be "the first run in the suite to exercise
the write path at all": evals 6 and 7 both prompt "apply all of them", generate scripts, smoke-test
them and rewrite the target SKILL.md. And 8b cannot repair CC5. CC5 is about gate answers that
contradict the recommendation, and 8b's specified answer, "apply all", *is* the (Recommended)
option. As written, 8b reproduces CC5 rather than repairing it. Repairing CC5 needs a gate answered
with a subset that excludes a recommended row, and eval 8 is a poor host for that with only three
SCRIPT/HYBRID rows.

*Strengthening.* "No `legacy/` directory exists anywhere under the target" is necessary but not
sufficient: a generated script that hard-fails on the missing directory satisfies it while still
being the forbidden output. Add that the rewritten SKILL.md contains no invocation whose argv names
`legacy`. And assert the Notes paragraph survives byte-identical rather than merely surviving,
since the baseline proposed deleting that paragraph specifically, which makes it the sharpest
observable in the set.

**O3. Problem granted. Better way refuted by counterexample: I ran both proposed hints against the
five-fixture corpus, and each fires more often on live steps than on dead ones.**

`referenced_paths` with an `exists` bool fires on exactly two steps corpus-wide. api-docs-checker
s4, `legacy/index.txt`, absent, correct. research-brief-writer s2, "save the raw page to
`sources/<slug>.html`", where that fixture's entire tree is `SKILL.md` and `topics.txt`, so
`sources/` is absent too. s2 is the WebFetch step eval 5 asserts must not be pure SCRIPT, and the
run classified it HYBRID. Fifty percent precision, and the false positive lands on the one step
class the suite already protects with an explicit assertion. The cause is structural, not tuning: a
write target does not exist before the step runs, so "path removed because its consumer was
retired" and "path this step creates" are the same observation. `<slug>` is also a template token
that can never resolve, so the naive version needs placeholder handling before it emits a single
usable bool.

`field_refs` with a derived `subset_of` fires three times corpus-wide. api-docs s2 {summary} inside
s3 {summary, description}, correct. api-docs s5 {description} inside s3, wrong, landing on the
HYBRID judgment step of the very fixture the hint was designed for. changelog-checker s3 {Added,
Fixed, Changed, Removed} inside s6 {Added, Fixed, Changed, Removed, Misc}, wrong, and eval 7's run
correctly scripted s3 as `count_entries.py`. Thirty-three percent precision. Identifier containment
tracks "operates on the same vocabulary", not "is subsumed by".

"Hints are not verdicts" rescues neither, because the objection's payoff is an assertion: "8a can
assert that the report cites the machine-detected absent path rather than a prose inference".
Scoring a citation converts the hint into a verdict. A run can cite the hint and still misclassify
s5, and the assertion would reward it.

What I would support instead: the mechanizable core of DEAD is an absent *consumer*, not an absent
path. A path referenced by exactly one step, by no other step, and by no file in the tree.
`legacy/` satisfies that. `sources/` does not, because s2 writes it and later steps read it.
Narrower, corpus-testable, and it fires once on this corpus, correctly.

Granted in full: the 40-step point. On a large target "read it and notice" degrades and only a
mechanized arm holds up. That is an argument for a larger fixture and for keeping eval 8 with a
big-target variant beside it, not for the two hints as specified.

**O4. Conceded. The arithmetic and the direction are both right. The fix substitutes a lower-bound
error for an upper-bound one.**

I read the code. `mech` filters on `NEEDS_SCRIPT`, which includes HYBRID; `tok = sum(s["approx_tokens"]
for s in mech)`; the verdict line calls it "tokens of per-run reasoning" removed. Step 8 mandates
that the HYBRID judgment prose stays. On this run 21 + 40 + 35 = 96, with s5's 35 retained by
construction, against a ~204-token body. The error is systematic and always overstates. Convinced.

*Disputed, the fix.* Step 8 also says "Cut the mechanical prose the scripts now cover", so a HYBRID
step does not retain all its tokens either. The true value lies strictly between zero and the
HYBRID count, and the inventory cannot tell the renderer where. "Count HYBRID at zero" is a floor
presented as a scalar, preserving the false precision that produced the bug. Report the SCRIPT sum
as a floor, show the HYBRID band separately, subtract the invocation lines, and relabel "per-run
reasoning" as "step prose".

Note what this does to the Phase 1 question. The defect ships to the user in the verdict line, and
eval 8 is where it is visible, because it is the only run whose body is small enough that 96 of 204
is obviously implausible. An eval that surfaces a shipping defect in user-facing output is earning
its slot. It also implies a new assertion on the verdict line, which is exactly the shape Objection
5 asks for.

**O5. Rule accepted. Application disputed: eval 8 already passes the rule as written.**

The admission rule is right and it resolves the discrimination-versus-non-harm incoherence the
Defender conceded. Adopt it.

The evidence offered against eval 8 proves nothing, though. "All six assertions describe correct
behavior" is true of every assertion in every suite; assertions always describe correct behavior.
The admission test is whether the *incorrect* behavior is reachable. Here it is reachable by the
skill's own instructions. Assertion 4's first clause, "no script is proposed for the DEAD step",
trips exactly the failure the fixture was built for, and the pressure toward that failure is
written into the skill: "every step is SCRIPT until proven CLAUDE", "Classify aggressively", "In
doubt between SCRIPT and HYBRID → SCRIPT", and the rubric's "Do not ask 'could this be a script?'.
Ask 'what exactly stops this from being a script?'". A run that follows that pressure proposes
`append_legacy_index.py` and fails assertion 4. Eval 8 admits.

Two refinements. First, make "plausible" a citation rather than a judgment: require each eval to
name in evals.json the specific with-skill failure its assertion trips, and the line of the skill
that pressures toward it. Eval 8 admits on the citation above; eval 9 stands or falls on its own,
which is a cleaner test than "does the baseline also pass". Second, sequencing: do not apply the
rule as a removal criterion while sampling is n=1 and CC1's grading contamination is unrepaired. An
admission rule enforced on unreliable measurements removes evals for noise. Fix the sampling and
the grader independence, then admit or remove.

### Where this leaves the Phase 1 question

Keep the scenario. Not because it discriminates, it does not, but because it is the only unstacked
eval in the set, it produced the suite's most actionable finding, it surfaced a live defect in
user-facing output, and it already carries an assertion its own failure mode trips. Add 8b,
corrected as above. Fix the renderer. Add repeats before touching the fixture, because every
remaining disagreement in this debate reduces to a quantity n=1 cannot measure.

## Phase 5 — Adversary's Rebuttal

Four sustained, one dropped. I re-ran the Advocate's corpus tests myself rather than take
them on report, and they hold. Where a fix of mine was refuted I say so and either replace
it with something I have tested or withdraw it.

Granted up front, because it costs me nothing and it is correct: S2's floor argument.
`render_report.py` computes `unclassified = sorted(inv_ids - seen)` and exits 1, so the
with-skill arm cannot emit a report missing a step row while the baseline arm produced five
rows by reading carefully. That is a real floor difference invisible to a pass-rate tie at
n=1. It supports keeping eval 8, which is what I argued in Phase 3 as well. Nothing in my
five objections asked for this scenario's removal.

**O1. SUSTAINED, with check (b) rewritten. Grounds (i) and (ii) forced the rewrite. Ground
(iii) does not land.**

(i) and (ii) are hits and I accept both. Publishing a keyword list does not make the keyword
list less misleading, so (b) as written graded disclosure rather than anchoring. And grading
"states the rule in full" against a report-only run, which was forbidden to implement
anything and could emit only a one-line interface, while eval 7's run could point at a
finished script, is the same double standard relocated from wording to prompt type. That is
the exact failure I opened by attacking, so I am not going to defend a version of it.

Ground (iii) does not land. Check (b) does not repeal CC3's rubric change, because SKILL.md
Step 2 already names four HYBRID shapes: "a script can enumerate the candidates, pre-compute
the facts, validate the answer, or render the result". Enumerate and render are verdict-free.
A run that emits the description text and lets Claude judge is performing a HYBRID
decomposition the rubric explicitly offers, not falling back to CLAUDE. (b) selects among the
rubric's own menu; it does not overrule it.

*Rewritten check (b).* Grade the **declared stdout schema**, which the skill requires from
every SCRIPT and HYBRID row in every configuration, report-only included. Eval 8's report
carries it in full: `[{file, description, words, chars, has_placeholder, vague_terms[]}]`.
That answers (ii), since proposals and implementations are then held to the same artifact.
The test itself: **for a step classified HYBRID, no emitted field may be one whose
miscomputation would change the step's final answer.** A wrong `words` count does not change
whether "the listing thing" reads clearly. A wrong `vague_terms[]` changes exactly which
descriptions Claude flags. That answers (i), because it tests influence on the judgment
rather than documentation of the heuristic.

The payoff survives the rewrite: s5 still fails, since `vague_terms[]` and `has_placeholder`
are answer-shaped; the baseline still passes, since it emits description text only. I concede
this is a designer-side criterion rather than a regex an auto-grader runs, which makes it
weaker than I implied in Phase 3. It is still operational in the way the conceded prose
standard is not: two graders asked "would miscomputing this field change the answer" converge
where "does the judgment core demonstrably stay with Claude" did not.

On the symmetry point, we agree and I said so in Phase 3: eval 7's step 7 passes under my
standard too, and I published the resulting means. The difference that matters is that the
prose standard leaves the suite with zero with-skill failures while (b) leaves one, located
on a defect both sides now agree is real.

**O2. SUSTAINED. Both factual errors conceded. Half the arithmetic conceded. Strengthening
accepted.**

*Conceded, error one.* I checked `evals.json`. Evals 6, 7 and 9 all prompt "apply all of
them" or "apply whatever delegations you find", generate scripts, smoke-test them and rewrite
the target. My claim that 8b would be "the first run in the suite to exercise the write path
at all" was simply false.

*Conceded, error two.* SKILL.md Step 4 marks apply-all "(Recommended)" in both branches, so
8b answering "apply all" reproduces CC5 rather than repairing it. Also false, and I should
have read the step I was citing.

*Sustained, and this is the substance that survives both errors.* Exercising the write path
is not the same as exercising the no-auto-delete rule, and only the second is at issue. I
read all three write-path fixtures. docs-linter has four steps, all live. changelog-checker
has seven, all live, and eval 7's own run correctly scripted the one the Advocate calls
overlapping. plugin-cached-release-notes has five, all live. **None of the three write-path
evals contains a step that should not exist, so none of them can test a rule about not
deleting steps that should not exist.** The rubric's most emphatic prohibition still has zero
coverage suite-wide, and 8b remains the only route to it. The Advocate concedes 8b should
exist; the disagreement is only over what I claimed it additionally repairs, and I withdraw
that claim.

*Half conceded, the arithmetic.* Assertion 2 does control a reachable failure. Apply-all is
the recommended default and `gate.md` records the run overriding it, so "writes anyway" was
live. I withdraw "two of six carry no information" as to assertion 2. Assertion 4's delete
clause is different and I sustain it: deletion requires a write, the prompt forbade writes,
so no behavior available to that arm could have tripped it. One unreachable clause, not two.

*Accepted without reservation.* Assert no invocation in the rewritten SKILL.md names `legacy`
in its argv, since a script that hard-fails on the missing directory satisfies the
directory-absence check while being the forbidden output. And assert the Notes paragraph
survives byte-identical, since the baseline named that paragraph specifically.

*Relocated, since 8b cannot host it.* CC5 needs a gate answered with a subset that excludes a
recommended row. Eval 7 is the right host: it has enough SCRIPT and HYBRID rows for a subset
answer to be meaningful, and it already runs the full write path.

**O3. Problem SUSTAINED. My fix CONCEDED in full. The Advocate's replacement also misfires,
and I tested it.**

I reproduced all three false positives against the fixtures. research-brief-writer's tree is
`SKILL.md` plus `topics.txt`, its s2 says "save the raw page to `sources/<slug>.html`", and
that step is the WebFetch step eval 5 exists to protect. changelog-checker s3's {Added,
Fixed, Changed, Removed} sits inside s6's set with Misc added, and eval 7's run correctly
scripted s3. api-docs s5's `description` sits inside s3's pair. My two hints are withdrawn.
The structural cause the Advocate names is the right one: a write target does not exist
before the step runs, so "path removed with its consumer" and "path this step creates" are
the same observation to an existence check.

*New substance: the proposed replacement fails the same test.* The Advocate's rule is a path
referenced by exactly one step, by no other step, and by no file in the tree, and he says
`sources/` is excluded "because s2 writes it and later steps read it". Later steps do not
read it in any form a mechanical matcher sees. Step 3 says "the fetched sources", step 4 says
"each kept source", step 7 says "source URL". The path token `sources/` appears in step 2 and
nowhere else in the file, and nowhere in `topics.txt`. A token-matching implementation fires
on `sources/` exactly as mine did. The rule only spares it by resolving English prose to a
path, which is the judgment the mechanization was meant to remove. I would rather name this
now than let it ship as corpus-tested when the corpus does not support it.

*Replacement I did test.* Flag co-occurrence of a step's path token with a **non-step prose
section** of the same SKILL.md. This is the evidence both arms actually cited: the Notes
paragraph. Corpus-wide it fires once, on api-docs s4, correctly, with no false positives,
because `sources/` and the changelog paths appear in no such section.

*And the honest limit on my own replacement.* api-docs-checker is the only fixture in the
corpus with a non-step prose section at all. The corpus therefore contains exactly one
instance of the pattern, so "zero false positives" is a much weaker result than it sounds and
I will not claim more for it than the Advocate's test allows me to claim against my first
attempt. The real conclusion is the one this exchange earned: **no DEAD mechanization should
ship against a corpus with one positive instance.** Before any hint is adopted, add fixtures
carrying stale steps of distinct shapes: a step invoking a tool the skill no longer declares,
a step whose only consumer is a later step that was removed, and a step superseded by a newer
step that does strictly more. Then test all three candidate rules, mine included, against
that corpus and adopt whichever survives.

Granted in full: the 40-step point supports a large-fixture variant, not the hints as
specified.

**O4. SUSTAINED. The Advocate's correction to my fix is right and I take it.**

He is correct that Step 8 also says "Cut the mechanical prose the scripts now cover", so a
HYBRID step retains some of its tokens and not all of them. "Count HYBRID at zero" is a floor
presented as a scalar, which is the same false precision I objected to. Report the SCRIPT sum
as a floor, show the HYBRID contribution as a band, subtract the invocations, and relabel
"per-run reasoning" as "step prose".

One addition of my own. The invocation cost does not need estimating: `classification.json`
carries the exact `interface` string for every SCRIPT and HYBRID row, so the renderer can
count those tokens rather than approximate them, and that term at least is exact. And I adopt
the assertion the Advocate suggests: assert the verdict line does not report HYBRID tokens as
removed. Note what that gives the scenario. It is a second assertion the current with-skill
run fails, on a defect that ships to users in every report, and the baseline never emits a
verdict line at all so it is scored as not applicable rather than as a win. Eval 8 acquires
two failing with-skill assertions between this and O1, which is the discrimination the
Defender said he could not produce.

**O5. DROPPED as an objection. The rule survives by agreement, not by contest.**

What convinced me: "all six assertions describe correct behavior" is vacuous, since every
assertion in every suite describes correct behavior, and the admission test is whether the
incorrect behavior is reachable. It is reachable here, and the Advocate produced the line of
pressure: "every step is SCRIPT until proven CLAUDE", "Classify aggressively", "In doubt
between SCRIPT and HYBRID → SCRIPT". A run following that pressure proposes a script for s4
and fails assertion 4's first clause. Eval 8 admits under my own rule, and my evidence
against it was wrong.

I accept his refinement 1 over my version: require each eval to name in `evals.json` the
specific with-skill failure its assertion trips and the skill line that pressures toward it.
That is a citation instead of a judgment call, and it is better than what I proposed.

One narrow point left for the Judge on refinement 2. He asks that the rule not be applied
while n=1 and CC1's contamination stand. Agreed for **removal**, since removing evals on
single-draw evidence is exactly the noise-chasing he describes. Not agreed for **admission**:
the rule should bind every eval added from now on, because it costs nothing at authoring time
and the alternative is a set that keeps growing with evals nothing can fail. Split the rule's
two uses, gate removal on better sampling, and let admission start immediately.

## Phase 6 — Advocate's Surrebuttal

<!-- Advocate: final defense or concession per sustained objection. -->

## Phase 7 — Judge's Interim: Assessment and Compromises

<!-- Judge: per objection — strengths/weaknesses of each side; resolved or compromise proposed. -->

## Phase 8 — Advocate on Compromises

<!-- Advocate: accept/reject each, one reason. -->

## Phase 9 — Adversary on Compromises

<!-- Adversary: accept/reject each, one reason. -->

## Phase 10 — Defender's Weigh-In

<!-- Defender: feasibility and appetite per surviving compromise. -->

## Phase 11 — Judge's Final Report

<!-- Judge: agreed changes / contested points / compromises and their fate / recommendation / user's options. -->
