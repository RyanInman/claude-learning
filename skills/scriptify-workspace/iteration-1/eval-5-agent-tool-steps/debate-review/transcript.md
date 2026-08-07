# Debate Review Transcript

**Artifact under review:** scriptify's run on eval `eval-5-agent-tool-steps`, and the eval scenario itself.

The question this debate answers: **does this run show the `scriptify` skill earning
its cost on this scenario, and what should change — in the skill, in the scenario, or
in the assertions?**

Files every role must read:

- skill under review: `/Users/admin/claude-learning/skills/scriptify/SKILL.md` (plus `references/delegation-rubric.md`)
- the fixture the run operated on: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/fixture-baseline/research-brief-writer`
- with-skill run output: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/with_skill/outputs/report.md`
- baseline (no-skill) run output: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/without_skill/outputs/report.md`
- machine-checked facts (hashes, tree diffs, live script probes): `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/with_skill/facts.json`
- assertion verdicts with evidence: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/with_skill/grading.json` and `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/without_skill/grading.json`
- eval definition: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-5-agent-tool-steps/eval_metadata.json`

**Date:** 2026-08-06

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

**Goal.** This scenario exists to test one rule in scriptify's rubric: a step that invokes
an agent-runtime tool — WebFetch, AskUserQuestion, an MCP call — is never pure SCRIPT,
because a script reimplementation (curl in place of the MCP call) silently loses auth, the
permission model, and rate limiting. That failure is destructive and invisible: the
rewritten skill looks more deterministic and is quietly broken. I built the
`research-brief-writer` fixture with three such steps (s2 WebFetch, s3 AskUserQuestion,
s5 notion MCP) interleaved with four genuinely mechanical ones.

**What the run did.** The with-skill run classified s2, s3 and s5 HYBRID, each with a `why`
naming the specific tool-gating reason, and each with a proposed script that prepares input
or digests output but never makes the call. s1, s4 and s7 came back SCRIPT with full argv
plus exit 0/1/2 semantics. s6 (write a 200-word brief in the house voice) came back HYBRID:
prose stays with Claude, a lint checks only length and marketing phrases. Seven of seven
assertions passed. The fixture is byte-identical to baseline — nothing was written.

**Key decisions, and why.**

1. *Zero pure CLAUDE across seven steps.* This is the skill's script-first tie-break working
   as designed: before writing CLAUDE, try a HYBRID decomposition. I read this as correct,
   not as over-scripting, because every HYBRID here leaves a named judgment core.
2. *I graded "concrete argv and exit-code interface" as its own assertion.* This turned out
   to be the single place the skill separated from the baseline.
3. *Report-only.* The prompt said don't change anything, so the run stopped at the gate.

**Where I am least confident.** The baseline scored 6 of 7. Without the skill, the model
independently classified all three tool-gated steps as hybrid, with the same reasoning about
auth and permission gating. Its only miss was that it named script files without specifying
argv or exit codes. So the honest summary is: this scenario tests a rule the model already
follows unprompted, and the skill's measured contribution here is interface rigour, not
correctness. Whether that is worth 57k tokens against the baseline's 42k is exactly what I
want attacked. I also want the "zero pure CLAUDE" verdict attacked — s6 is prose writing,
the rubric's own canonical CLAUDE example, and the run made it HYBRID.

## Phase 2 — Clarifying Questions

### Adversary's questions

**Q1.** Three of the five proposed script interfaces take `.work/topics.json` or `.work/stats.json` as input (s2 `fetch_plan.py --topics .work/topics.json`, s5 and s7 `render_index.py --stats .work/stats.json`). Which step of the `research-brief-writer` workflow is expected to produce those files: an artifact that already exists, or a new intermediate the proposed scripts would introduce as part of the delegation?

**Q2.** The rendered verdict line reads "delegating them removes ~202 tokens of per-run reasoning." `render_report.py:91-97` computes that as the sum of `approx_tokens` over every SCRIPT and HYBRID step. What is that figure intended to denominate: SKILL.md body prose replaced by invocation lines, or reasoning tokens saved per run of the target skill?

**Q3.** `benchmark.json` metadata records `runs_per_configuration: 3`, and `benchmark.md` reports pass rate, time, and tokens with a stddev, but the file holds exactly one run per (eval, configuration) pair, and the reported spread is across evals 5 through 9 rather than across repeats of one eval. Are additional eval-5 runs recorded somewhere outside this workspace, or is the 56,793 vs 42,305 comparison a single run per side?

### Advocate's questions

**Q1.** How many runs back each config? `run-1/` is the only run directory under both `with_skill/` and `without_skill/`. Is there variance data across repeats, or is each config n=1? This matters because your own concession — "the model already follows this rule unprompted" — rests entirely on the baseline's single draw.

**Q2.** What does `total_tokens` count, and were both configs run under identical tool permissions and budgets? Specifically: does the with-skill 56,793 include the one-time read of `SKILL.md` plus `references/delegation-rubric.md`, and how much of the ~14.5k delta is that fixed load versus per-step work? Related: the transcript notes say the run stopped after Step 3 and skipped Steps 5-9, so I want to know whether the skill's load cost was amortized over roughly 4 of its 9 steps.

**Q3.** Were the seven assertions frozen before either run produced output? And was defect discovery in the fixture ever in the eval's scope? The baseline probed and reported four concrete defects (dedupe-order ambiguity that clobbers a file, unstable word-count method, missing URL column, ordering bug); the with-skill run reported two and probed nothing. Neither `eval_metadata.json` nor any assertion mentions finding workflow bugs, so I need to know whether that gap is out of scope or an unmeasured regression.

### Judge's questions

**Q1 — Grading provenance and pre-registration.** Who produced `grading.json` and its evidence lines for each arm: the same agent that wrote that arm's `report.md`, a separate grader reading only the outputs, or a script? And was assertion 6 ("...classified SCRIPT **with concrete argv/exit-code interfaces**") written before either run, or after outputs existed? This is the single assertion that separates the arms, and it happens to encode scriptify's own house output format (`classification.json`'s `interface`/`exit` fields), so its authoring order decides how much of the 7/7 vs 6/7 gap is a measurement of the skill versus a measurement of format conformance.

**Q2 — Is baseline compliance n=1?** The tool-gating rule is this scenario's whole reason to exist, and the unprompted baseline followed it on all three steps (s2, s3, s5). Is that one sample, or is there evidence across repeat runs, other evals in the suite, or earlier iterations that a no-skill model ever classifies a WebFetch/MCP/AskUserQuestion step as pure SCRIPT? If the failure mode has never been observed unprompted, the scenario is testing a rule that has no measured failure rate to protect against.

**Q3 — Is report substance in scope for this eval, or measured elsewhere?** The assertion set scores classification labels and interface shape, and scores nothing about whether the report is correct or useful. Concretely: the baseline's Defect 3 finds that no step ever records a source URL, while the with-skill report proposes `source_stats.py` emitting a `url` field and `render_index.py` rendering a "topic, source URL, word count" table — both reading from a `.work/stats.json` that the with-skill report never explains how gets a URL. Is that kind of internal coherence (and the baseline's empirically probed dedupe-order and word-count-method ambiguities, which the with-skill run did not find) deliberately out of scope here and covered by another eval, or does this eval consider its seven assertions a complete verdict on the run?

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

**Adversary Q1 — where do `.work/topics.json` and `.work/stats.json` come from?**
Neither exists, and no step in the fixture produces them. They are new intermediates the
proposed delegation would have to introduce, and the with-skill report never says so. This
is a real coherence gap. It gets worse: `source_stats.py` is specified to emit a `url`
field and `render_index.py` to render a source-URL column, but **no step in the fixture
ever records a URL**. The baseline found exactly this (its Defect 3, "step 7 asks for a
column no step produces"); the with-skill run proposed interfaces that quietly depend on it.

**Adversary Q2 — what does "~202 tokens of per-run reasoning" denominate?**
SKILL.md body prose. `render_report.py` computes it as the sum of `approx_tokens` over
every SCRIPT and HYBRID step. It is a static estimate of prose displaced, **not** a
measurement of reasoning tokens saved per run of the target skill. I should not have let it
stand as a benefit figure, and no measured after-cost exists anywhere in this workspace.

**Adversary Q3, Advocate Q1, Judge Q2 (sample size)** — see CC2.

**Advocate Q2 — token composition and amortization.** See CC4. One specific: the
with-skill run stopped after Step 3 of 9, so its fixed skill-load cost was amortized over
roughly four of nine steps. The +34% token delta is therefore an *understatement* of the
full-pipeline delta, not an overstatement.

**Advocate Q3 and Judge Q3 — was defect discovery ever in scope?**
No, and that is the gap. The seven assertions are the whole measurement for this scenario;
no sibling eval carries report-substance checks. They score classification labels and
interface shape and nothing else. The baseline probed the fixture empirically and reported
four concrete defects (dedupe-order ambiguity that makes step 2 clobber its own output, an
unstable word-count method, the missing URL, and step 5 running before its input exists).
The with-skill run reported two and probed nothing. **That difference is unmeasured, and on
the evidence it favours the baseline.**

**Judge Q1 — assertion 6's authoring order.** Written before the runs (CC1). But the Judge
has identified something I did not: assertion 6 encodes scriptify's own house output format,
the `interface`/`exit` fields of `classification.json`. So the one assertion that separates
the arms rewards format conformance, and a run that produced equally concrete interfaces in
prose would fail it. I think interface concreteness is a genuine quality — but I cannot
claim this assertion measures it independently of scriptify's schema.

**Judge Q2 — has the failure mode ever been observed unprompted?**
No. Not once in this iteration, and I have no data from earlier ones. This scenario guards
a rule with **no measured failure rate**.

## Phase 3 — Adversary's Case

The Defender's Phase 2 answers concede most of the measurement problems. I am not
re-arguing those. Every objection below argues the same thing from a different angle:
these are defects in `scriptify` itself, not in this run's write-up, and four of the five
ship to real users on the write path that this eval never exercised. Each one has a
mechanical fix in a script the skill already bundles.

### Objection 1 — nothing in the skill checks that a proposed script's inputs exist, so the write path can green-light a broken pipeline

**Problem.** `scriptify` validates that a classification is *well-formed* and never that it
is *runnable*. On the write path, a proposed script whose input no step produces gets
built at Step 6 against a fixture the same agent invents at Step 5, passes the smoke test
at Step 7 because the fixture was authored to match, and then Step 8 rewrites the target
SKILL.md to invoke it. The user ends with a green PASS line, a rewritten skill, and a
pipeline that cannot run. That is precisely the failure the rubric warns about: "a wrong
script is worse than prose, because it fails silently and looks official."

**Evidence.** Three of five proposed interfaces in
`with_skill/scratch/.delegation-review/classification.json` read from files that do not
exist and that no step creates: `--topics .work/topics.json` (s2, L21) and
`--stats .work/stats.json` (s5 L54, s7 L76). The fixture holds two files, `SKILL.md` and
`topics.txt`. Worse, `source_stats.py`'s declared stdout carries `"url": "..."` (L33) and
`render_index.py` renders a source-URL column (L77), but fixture step 2 saves the page to
`sources/<slug>.html` and records no URL anywhere. The Defender concedes the gap. What the
concession does not reach is *why the skill let it through*: `render_report.py`'s validator
(`scripts/render_report.py:60-85`) checks ids, classes and presence of `proposed_script`,
and has no notion of input provenance, so it exited 0 on the first try and the report went
to the user as clean. The gate at Step 4 then asks "apply all 7?" with no signal that two
of the seven cannot be implemented as specified.

**Better way.** Add an input-provenance check to `render_report.py`, between Step 3 and the
gate, so the user sees it before approving. Every path token in `proposed_script.interface`
must resolve to one of: (a) a path that exists in the target tree today, (b) the declared
`stdout`/`--out` of an earlier step's proposed script, or (c) a new
`requires_new_artifact` field on the classification entry naming what must be created and
by which step. Anything else is a validation error, exit 1, same as an unclassified id.
Render the (c) entries as an "Unmet inputs" section above the table. On this run that check
fails on `.work/topics.json`, `.work/stats.json`, and the `url` field, which is exactly the
set the baseline found by hand as its Defect 3.

### Objection 2 — the skill never looks at the target's real input data before stamping a step SCRIPT, and both SCRIPT labels in this run are false as written

**Problem.** Step 2 classifies from prose alone. A step whose spec admits two defensible
implementations is not deterministic, it only looks deterministic, and labelling it SCRIPT
converts an open question into a silent decision made later by whoever writes the script.
The rubric already carries the right instrument, the secondary test "could you write the
unit test for this step's output right now?", but nothing in the skill makes a run actually
execute that test against real data, so the run answered it from intuition and got it
wrong twice.

**Evidence.** s1 is SCRIPT with `why`: "Same input gives same list every run; a unit test
can be written today" (classification.json L7). It cannot. The baseline ran both readings
against the real `topics.txt` and got 5 topics versus 4, with the literal reading emitting
`retrieval-augmented-generation` twice so that step 2 overwrites its own output file
(`without_skill/outputs/report.md` L45-63). s4 is SCRIPT with "No run should ever differ"
(L40). It does: four defensible counting methods on one 195-word article body give 197
THIN against 210/226/232 ok, flipping the verdict on the identical file (L65-80). The
with-skill report *saw the ambiguous data* and shipped the label anyway: it notes
`topics.txt` holds "1 exact duplicate and 1 case-only duplicate, exactly the case where two
runs can disagree" (`with_skill/outputs/report.md` L54) and still classified the step as
a pure function whose runs never differ. The baseline closed both questions with roughly
forty lines of throwaway Python inside a *smaller* token budget (42,305 against 56,793).
The Defender's answer files this as "unmeasured, and it favours the baseline"; I am arguing
it is not merely unmeasured, it is a missing step in the skill.

**Better way.** Add to Step 2, for every candidate SCRIPT or HYBRID step that consumes
target-supplied data: run the step's rule against the real input under at least two
defensible readings before assigning the class. Identical answers, classify normally.
Divergent answers, record a `spec_ambiguity` object on the entry holding the readings, the
observed divergence on real data, the consequence, and a recommended default, and require
the class rationale to reference it. `render_report.py` renders these as a "Decisions that
block scripting" section. This is cheap, it is the rubric's own secondary test made
executable, and it is the single largest quality gap between the two arms.

### Objection 3 — the Step 4 gate has no slot for the decisions that actually block scripting, so an "apply all" answer approves an undefined thing

**Problem.** Step 4 is hard-coded to two questions and instructs "Send both questions below
in one call," and AskUserQuestion caps at four options per question. There is structurally
nowhere for "which reading of step 1 do you mean?" to go. So on the write path the user
answers "Apply all 7", Step 5 derives expectations "from the semantics of the step" when
the semantics are undecided, Step 6 implements whichever reading the author picked, Step 7
goes green against the matching fixture, and Step 8 rewrites the SKILL.md. The user
approved a row, not a semantics, and now owns a script that silently drops a topic or
clobbers a file. Combined with CC5 (no run in this suite was ever fed a gate answer
contradicting the recommendation), the gate's ability to catch this is untested as well as
absent.

**Evidence.** SKILL.md Steps 4-8 contain no mechanism for recording a semantic choice; the
only fields that survive to Step 5 are the row selection and the residue flag. Step 5's
own rule, "Re-read `.delegation-review/classification.json` from disk here, because the
recorded decisions outrank chat memory," proves the design intent that decisions live in
that file, yet the ambiguity decisions are the one class of decision it has no field for.
The baseline, with no skill at all, produced exactly this artifact unprompted:
`without_skill/outputs/gate.md` records "two decisions needed before scripts are written",
dedupe order and word-count method, each with the default chosen and why
(`without_skill/outputs/report.md` L137-146).

**Better way.** Make the ambiguity decisions a gate question, asked before Question 1,
conditional on any entry carrying `spec_ambiguity` from Objection 2. One question per
ambiguity, options being the readings, with the recommended default marked and the
consequence in the option description. Write the answer back into
`classification.json` so Step 5's re-read-from-disk rule carries it. Then amend Step 5 to
derive expectations from the recorded decision and never from the author's own reading of
the prose. If the user declines to decide, the affected row drops out of the apply set
rather than being implemented on a guess.

### Objection 4 — the shipped report renderer states a benefit that the skill's own rewrite rule contradicts, on every run

**Problem.** The concession that the "~202 tokens" figure denominates displaced prose stops
at this run's wording. The figure is not this run's wording. It is the headline `**Verdict:**`
line that `render_report.py` emits for every target `scriptify` ever reviews, it is the one
line users quote back, and it sums SCRIPT **and** HYBRID steps, claiming as "removed" the
tokens the skill's own Step 8 explicitly keeps.

**Evidence.** `scripts/render_report.py:89-97`: `mech` is every step whose class is in
`NEEDS_SCRIPT` (SCRIPT plus HYBRID), `tok = sum(s["approx_tokens"] for s in mech)`, printed
as "delegating them removes ~{tok} tokens of per-run reasoning." SKILL.md Step 8 says the
opposite for the HYBRID half: "Turn each HYBRID step into 'run the script, then apply
judgment to its output', because the judgment prose stays." In this run the HYBRID steps
are s2, s3, s5 and s6, worth 27+32+33+27 = 119 of the claimed 202 tokens. So 59% of the
headline benefit is prose the skill promises to retain. The remaining 83 tokens are static
body prose, not reasoning, and no measured after-cost exists anywhere in this workspace,
which the Defender concedes.

**Better way.** Two edits to `render_report.py`. First, drop "removes" and "per-run
reasoning": emit "N of M steps are mechanical (SCRIPT/HYBRID); ~X tokens of step prose
become script invocations." Second, if a number stays, split it: report SCRIPT tokens as
displaced and HYBRID tokens as restructured, because they are different quantities. Pin
both in `tests/test_render_report.py` with a case asserting that HYBRID tokens never appear
in a displaced-prose total. Ten-line fix, removes a false claim from every future run.

### Objection 5 — assertion 6 is the only assertion that separates the arms, and on this fixture it rewards the less coherent design

**Problem.** The Judge extracted the concession that assertion 6 encodes `scriptify`'s own
`interface`/`exit` schema. The concession does not go far enough, because on this fixture
the assertion does not merely fail to measure quality independently, it *inverts* against
it. An assertion that a better design fails and a worse design passes is worse than no
assertion, and it is the entire 7/7 versus 6/7 margin.

**Evidence.** The failing arm proposed `record_source.py`, which "writes
`sources/manifest.json` mapping slug to URL, fetch time, and byte size. Makes step 7's URL
column real" (`without_skill/outputs/report.md` L105-108). The passing arm proposed
`source_stats.py` emitting a `url` field with no producer anywhere in the workflow, and
`render_index.py` rendering a URL column from a `.work/stats.json` that no step writes
(Objection 1). On the dimension the assertion claims to care about, whether the proposal is
concrete enough to implement, the arm that failed had the implementable pipeline and the
arm that passed did not. With CC1 (designer, Defender and grader are one agent), CC2 (n=1)
and CC4 ("earns its cost" never operationalized), the 7/7 result cannot carry the weight of
"the skill earned its cost here." Precedent that substance assertions belong in this suite:
eval-8 already asserts "step 2 is identified as superseded by or duplicative of step 3",
which is a report-substance check, not a format check.

**Better way.** Replace assertion 6 with three format-neutral checks that are true facts
about this fixture and that either arm can pass on merit:
(a) the report states that dedupe-before-slugify and slugify-before-dedupe give different
results on the actual `topics.txt`, and names the file-overwrite consequence;
(b) the report either pins the word-count extraction method for step 4 or flags that step 4
does not determine one;
(c) the report notes that no step records a source URL, so step 7's URL column has no
producer, and no proposed script assumes one exists.
Keep an interface check if wanted, but phrase it as the property rather than the schema:
"each SCRIPT/HYBRID row specifies inputs, outputs and failure behaviour precisely enough to
implement without further questions." On the proposed set the with-skill run fails (a)
partially, (b) and (c), and the baseline passes all three. That inversion is the finding,
and it is worth more than the current pass rate.

## Phase 4 — Advocate's Case

### Part 1 — The steelman

**S1. The destructive failure mode did not occur, and that is the whole point of the
fixture.** Three tool-gated steps, three HYBRID labels, three `why` fields naming the
specific gating reason, and zero proposed scripts that make the call. `fetch_plan.py`
plans paths and verifies completeness. `source_stats.py` builds an option list.
`render_index.py` renders a block for Claude to hand to the MCP append. No curl, no
requests, no urllib anywhere in `classification.json`. The Adversary disputes none of
this across five objections. The scenario was built to catch a silent, destructive
rewrite, and the run did not produce one.

**S2. The run caught a bug in the skill's own tooling, using the exact prose the skill
put there for that purpose.** `inventory.py` reports `s5 ... tools=-` (report.md L23-27);
s5 is the notion MCP step. SKILL.md Step 1 says "Read the target SKILL.md yourself before
you classify, because the inventory maps the steps without reading what they mean." The
run did, caught the miss, and disclosed it in the report (L30) and in transcript-notes
(L12). This is the script-first design working with its safety valve intact: a skill that
delegates aggressively still names the one place a human read is mandatory, and on this
run that instruction is the only reason s5 was classified correctly at all. A pure-script
pipeline would have shipped `tools=-` as truth.

**S3. Report-only held, verifiably.** `facts.json` `target_tree_diff` is empty on all
three axes. `skill_md_changed: false`. The gate was recorded rather than skipped, with the
reasoning that an explicit user instruction outranks the skill's "(Recommended)" default.
Note what this means for Objections 1 through 3: the Adversary's own framing is that those
are write-path defects. The mechanism that stopped every one of them from reaching this
user is the Step 4 gate the Adversary attacks in Objection 3. The gate held on the one run
we have.

**S4. Completeness is structurally guaranteed, not lucky.** `render_report.py:82-84`
rejects a classification that omits any inventory id; L71-72 rejects an empty `why`;
L74-79 rejects a SCRIPT or HYBRID row missing any of `name`, `interface`, `stdout`, `exit`.
Seven of seven rows carry all four fields, and the validator exited 0 on the first try. The
baseline also covered all seven steps, but nothing in the baseline would have caught it if
it had not. That difference is invisible when both arms happen to succeed and decisive
across many runs, which is exactly the kind of property a single draw cannot show.

**S5. The with-skill report is not a subset of the baseline's.** It found a defect the
baseline missed: "No step defines the 'house voice' or where briefs get written. s6 names a
voice the skill never specifies, and gives no output path for the briefs" (report.md L72).
That is the same class of defect as the url gap, an artifact referenced with no producer,
and it is the one that blocks the baseline's own optional `check_briefs.py` from being
implementable. So the run demonstrably had the capacity to spot missing-producer defects
and exercised it. The correct diagnosis is not "the skill cannot see these," it is "the
skill has no step that checks for them systematically." That narrows Objection 1 from a
capability indictment to a missing checkpoint.

**S6. The `.work/` intermediates are a consequence of HYBRID decomposition, not
carelessness.** Splitting a step into "script prepares, Claude acts, script digests"
necessarily creates a handoff artifact. The fixture has no intermediates because it is a
monolithic prose workflow; any correct decomposition of it must introduce some. The
proposed shape is right. What is missing is the declaration. That distinction matters for
what the fix should be, and I return to it in A1.

### Part 2 — Answers to each objection

#### A1 — Objection 1: I accept the problem and the evidence. I dispute the severity and the better way.

The `.work/*.json` files and the `url` field have no producer. Verified, conceded, not
arguable.

**The severity claim overstates the causal chain.** The Adversary writes that the script
"passes the smoke test at Step 7 because the fixture was authored to match." SKILL.md
Step 5 forbids exactly that: "derive the test expectations from the semantics of the step,
what the prose says the step must catch. **Never derive them from script output.**" Step 7
reinforces it: "On FAIL, fix the script, not the expectation." More concretely, Step 5
requires creating fixtures under `.delegation-review/fixtures/<script-name>/`. To build a
fixture for `fetch_plan.py --topics .work/topics.json`, the author must materialize a
`.work/topics.json` and decide what is in it and who writes it. The missing producer becomes
unavoidable at that moment. The write path is not blind here; it has a forcing function.

**But I concede the part that matters:** a forcing function that fires at Step 5, after the
user answered "apply all 7" at Step 4, is too late to inform the approval. That is a real
ordering defect. Surfacing provenance before the gate is correct and I support it.

**I dispute the better way as specified, on two grounds.**

First, exit 1 is the wrong severity. Requiring every path token to resolve to an existing
path or an earlier step's declared stdout would reject correct HYBRID decompositions on
essentially every target scriptify is designed for, because a skill worth scriptifying is
by definition one with no scripts and no intermediates yet. Turning the common case into a
validation failure trains users to route around the check. The Adversary's own option (c),
a required `requires_new_artifact` field rendered as an "Unmet inputs" section above the
table and echoed at the gate, delivers the same information with no false-failure mode.
Take (c), drop the exit 1.

**Second, and this is a defect in the proposed check rather than a preference: as written it
does not catch the url bug.** The rule governs "every path token in
`proposed_script.interface`." The url field does not appear in any `interface`. It appears
inside `stdout` for s3 (`classification.json` L33) and as a rendered column description in
s7's `stdout` (L77). It is a JSON field name, not a path token. So the check catches
`.work/topics.json` and `.work/stats.json` and misses the one defect the Adversary himself
calls "worse." A provenance check has to cover declared output fields, not just argv paths,
or it fires on the benign case and stays silent on the severe one.

#### A2 — Objection 2: I accept the evidence. I dispute the problem's framing and the better way.

**The claim "both SCRIPT labels are false as written" does not survive the rubric's own
test.** The rubric's operational form is: "would two different Claude runs produce
meaningfully different output on this step, **and should they?** If runs should not
differ, SCRIPT." For s1, two runs might differ on dedupe order, and they absolutely should
not. That is the textbook definition of SCRIPT. The ambiguity is an argument **for**
scripting s1, not against the label. Same for s4: pick a counting method and the step is a
pure function; the fact that prose leaves it unpinned is precisely the run-to-run variance
a script exists to kill.

The secondary test the Adversary invokes, "could you write the unit test for this step's
output right now?", also answers yes. You can write it for either reading. What you cannot
do is know which reading the author meant, and that is a question resolved **once, at
authoring time, by asking the user**. It does not vary with context per run. That is the
rubric's condition for a decision, not its condition for CLAUDE.

**Decisive corroboration: the baseline reached the same class on both steps.** Step 1
"Script (full)", step 4 "Script (full)" (`without_skill/outputs/report.md` L12, L15). The
arm the Adversary holds up as the counterexample assigned the identical labels after
running the probes. So the probes did not change a class. They produced evidence and a
recorded decision. The delta is "flag the ambiguity," not "relabel the step," and the
objection's headline claims the latter.

What is genuinely wrong is the `why`. "Same input gives same list every run" is a false
statement about the current prose, and it should have read "once the dedupe order is
pinned." That is a defect in one field, not in the classification.

**I dispute the better way as too expensive and non-general.**

- Scope: every step that consumes target data is 7 of 7 here. "At least two defensible
  readings" per step is an unbounded generative task added to a skill whose premise is
  moving work out of per-run prose reasoning.
- No termination condition. The baseline's own transcript proves it: three counting methods
  agreed and gave "no flip yet" (`without_skill/outputs/transcript-notes.md` L20), so the run
  edited the probe to add a fourth until one disagreed (L21-24). The search stopped when it
  found a disagreement, not at a defined bound. Excellent instinct for a one-off
  investigation, unusable as a repeatable skill step.
- It only works when the target ships sample data. `topics.txt` happens to exist. Most
  targets are skills whose inputs arrive at their own run time, so there is nothing to probe
  and the step silently no-ops. The rubric already flags this hazard: "Authoring-time steps
  differ from run-time steps."

**Cheaper fix that captures the value:** at Step 2, when a SCRIPT or HYBRID step's prose
admits more than one implementation, require the entry to carry the **pinned
interpretation** and its consequence, as a `decides` field. Probe with real data when the
target supplies it; pin regardless when it does not. One bounded field, works with or
without sample data, fixes the actual defect here (an unqualified `why`), and feeds the
gate.

#### A3 — Objection 3: I accept the evidence. I dispute that it is independent of A2, and I dispute the better way.

The gate has no field for a semantic decision. True.

**But the objection is largely downstream of Objection 2 and mostly dissolves with A2's
fix.** Step 4's own >4-row form already offers "Apply a subset, list row ids in Other," and
SKILL.md states the gate exists "so the user can drop rows." A user who is shown that s1's
dedupe order is undecided can already drop s1 with the machinery that exists today. What
was missing is not a gate slot, it is the report never telling them. Put the pinned
interpretation in the report per A2 and the existing gate handles the rest.

**I dispute the better way on cost and on its own cited precedent.** "One question per
ambiguity, asked before Question 1" puts an unbounded number of AskUserQuestion calls ahead
of the actual decision. AskUserQuestion caps at four options, and SKILL.md already notes it
must split rows and residue across separate questions to fit. A target with five
ambiguities opens with five interrogation prompts before the user sees the gate that
matters. That inverts the design intent of a single low-friction checkpoint defaulting to
"apply all."

The precedent cited argues for my version, not the Adversary's. The baseline recorded its
two decisions as a **document with defaults**, `without_skill/outputs/gate.md`, not as
interactive questions. That is the shape that worked. Mirror it: render a "Decisions that
block scripting" section in the report, then add **one** gate question, "the report pinned
N interpretations: accept all (Recommended) / review in Other / drop the affected rows."
Bounded, one call, same information, and the answer still writes back into
`classification.json` so Step 5's re-read-from-disk rule carries it.

#### A4 — Objection 4: conceded in full. I dispute nothing, and the proposed fix does not go far enough.

`render_report.py:90-97` sums `approx_tokens` over `NEEDS_SCRIPT` and prints "removes ~{tok}
tokens of per-run reasoning" while SKILL.md Step 8 promises the HYBRID judgment prose stays.
119 of 202 tokens on this fixture, 59%. It ships in the headline verdict line of every run.
It is false, it is cheap to fix, and I would rank it first for repair rather than fourth.

**One correction the objection misses, in the same direction.** The number is also wrong for
the SCRIPT half. Step 8 replaces the step prose with an invocation line plus retained
"rationale, branching, and gotcha sentences verbatim." s7 is 24 tokens of prose; its
replacement, `Run exactly: python3 scripts/render_index.py --stats .work/stats.json --format
table` plus exit semantics, is comparable in length. Net displacement for SCRIPT steps is
(step tokens minus invocation tokens), not step tokens, and on short steps that is near
zero. So splitting the figure into "SCRIPT displaced / HYBRID restructured" still leaves the
SCRIPT number overstated.

**Go further than the proposed fix: drop the token claim from the verdict line entirely and
report step counts only.** A headline number that needs three caveats to be true is worse
than no number, because the verdict line is the one line users quote. Keep the per-step
`Tokens` column, which is an honest measurement of step size and makes no benefit claim.

#### A5 — Objection 5: I accept the evidence as facts. I dispute the inversion inference and the better way.

**The inversion claim requires treating two different properties as one.** Assertion 6 says
"classified SCRIPT **with concrete argv/exit-code interfaces**." The Adversary re-reads its
subject as "whether the proposal is concrete enough to implement." Those are not the same
property, and a proposal can have either without the other. The baseline had pipeline
coherence without interface specificity. The with-skill run had interface specificity with
one coherence gap. Calling that an inversion collapses the distinction.

**The assertion measured what it claimed, correctly.** I re-ran the grep: across the entire
baseline report, `python3 `, `exit `, `usage:`, `--json` and `argv` return zero hits.
`record_source.py` is described as "writes `sources/manifest.json` mapping slug to URL,
fetch time, and byte size" with no argv, no exit codes, and no stated behavior on a failed
fetch, a duplicate slug, or a missing directory. `parse_topics.py` "hard-fails on a slug
collision" with no exit code, message, or stdout shape. The grading evidence line is a
reproducible grep result, not a judgment call.

**Blast radius runs the other way from the objection's framing.** The url gap affects one
field in one proposed script's declared stdout and one rendered column. The missing
interface spec affects 5 of 5 proposed scripts. And consider what each does to the write
path, which is what "concrete enough to implement" is ultimately about: Step 5 builds the
manifest from the declared argv and exit codes. With none specified, Step 5 has nothing to
write a manifest entry against and the pipeline cannot start. The with-skill proposal can
proceed and hits one wrong field. The arm that failed the assertion is the one that cannot
be handed to the write path at all.

**I dispute replacing assertion 6, and I accept adding (a), (b) and (c).** The proposed
checks are good: fixture-specific, pre-registrable, gradeable on both arms on merit. Add
them. But deletion loses the only check on implementability-as-specified, and it loses it
on an argument the Defender's own concession does not support: Judge Q1 established that
assertion 6 **encodes** scriptify's schema, not that the underlying property is fake. The
Adversary supplies the format-neutral rewording himself, "each SCRIPT/HYBRID row specifies
inputs, outputs and failure behaviour precisely enough to implement without further
questions," then files it as optional. Make that the assertion. Keep it, reword it,
add (a)(b)(c) alongside. Result: 9 or 10 assertions, both arms re-gradeable, no information
destroyed, and the inversion question gets settled by measurement instead of by argument.

The eval-8 precedent supports this. I verified it: eval-8 carries both substance assertions
("step 2 is identified as superseded by or duplicative of step 3") **and** structural ones
("the report contains a row for every one of the 5 workflow steps"). It adds substance
checks to format checks. It does not trade one for the other.

**Standing caveat on this objection.** Under CC2 every figure here is one draw. That
constrains the Adversary's inference as much as the Defender's: "the baseline found four
defects with forty lines of Python inside a smaller budget" is also n=1. It is a reason to
run repeats before rewriting the assertion set around a single observation.

## Phase 5 — Adversary's Rebuttal

Four sustained, one dropped. Two of the four are sustained on narrower ground than I filed
them, and I say where. The Advocate landed three hits that change my position: my
provenance check does not catch the defect I called worst, my "both SCRIPT labels are
false" headline does not survive the rubric's own test, and Objection 3 is downstream of
Objection 2 in a way I did not see.

### Objection 1 — SUSTAINED. The Advocate broke my fix; here is one that works, and I defend exit 1.

**The catch is correct and I am adopting it.** `url` appears in `stdout` for s3
(`classification.json` L33) and in s7's rendered-column description (L77). It is a JSON
field name, not a path token. My rule scanned `interface` only, so it catches
`.work/topics.json` and `.work/stats.json` and stays silent on the one I called worse.
Conceded without reservation.

**Replacement fix: stop parsing free text, make provenance declared.** The failure in my
version was that it inferred a data contract from prose written for humans. Instead add two
required fields to `proposed_script` on every SCRIPT and HYBRID entry:

- `consumes`: list of the things the script reads, at field granularity where it reads
  fields (`sources/*.html`, `stats.url`, `stats.words`).
- `produces`: list of the things it writes, same granularity (`topics[].slug`,
  `stats.words`, `sources/manifest.json`).

`render_report.py` then does set arithmetic, no text parsing: every element of `consumes`
must appear in an earlier step's `produces`, or exist in the target today, or be listed in
`requires_new_artifact` naming which target step must start producing it. On this run
`render_index.py` must declare `consumes: ["stats.url", ...]`, no step produces
`stats.url`, and the check fires. It catches `.work/*.json` and the url gap by the same
mechanism, which mine did not.

**I do not accept softening exit 1, and the argument for softening rests on a conflation.**
The Advocate says the rule "would reject correct HYBRID decompositions on essentially every
target," because a skill worth scriptifying has no intermediates yet. That is true of
*introducing* an intermediate, which my rule permits via `requires_new_artifact`. It fires
only on an *undeclared* one. Introducing intermediates is the common case; failing to
declare them is the bug. Three further reasons the hard failure is right:

1. Consistency. `render_report.py` already exits 1 on a missing `why` (L71-72) and on a
   SCRIPT row missing `stdout` (L74-79). Undeclared provenance is metadata of exactly that
   kind. A soft section is a special case with no principle behind it.
2. The soft version is what we already ran. A report that renders clean and carries an
   advisory section is this run: the report *did* name the missing brief path and the
   undefined house voice in prose (report.md L72), the validator exited 0, and the gate
   asked "apply all 7?" anyway. Advisory text did not stop it. A soft check reproduces the
   observed outcome.
3. Nobody is trained to route around it. The party that fixes the error is Claude, not the
   user, and SKILL.md Step 3 already scripts the loop: "Fix classification.json per the
   stderr messages. Re-run the command." Cost of compliance is one field.

**On severity, and on S3.** The Advocate argues in S3 that the Step 4 gate is what stopped
these write-path defects from reaching the user. It is not. CC5 records that every gate
answer in this suite took the recommended option or the one the prompt dictated, and this
run's gate answer was dictated by "Report only for now, don't change anything." The gate
transcribed a user instruction. It has never been observed refusing anything. The write
path is untested in this iteration, which is a reason to harden it before it runs, not a
reason to call it safe.

**I accept S5 and it narrows my claim.** The run found the missing-producer defect for the
brief path and the house voice. So the capability is there and the checkpoint is not. My
objection is a missing-checkpoint claim, not a capability indictment, and I withdraw any
implication otherwise.

### Objection 2 — SUSTAINED on narrower ground. I withdraw the label claim. The surviving defect is worse than an unqualified `why`.

**Conceded: the classes are right.** "Would two runs differ, and *should* they?" answers no
for s1 and s4, so SCRIPT is correct, and ambiguity argues for scripting rather than against
it. The baseline reached "Script (full)" on both steps after running its probes
(`without_skill/outputs/report.md` L12, L15), so the probes produced evidence and a
decision, not a reclassification. My headline "both SCRIPT labels are false as written"
was wrong and I withdraw it.

**What the Advocate's account misses: the run did not leave the question open, it answered
it, and it answered it the destructive way.** The Advocate diagnoses the residue as one
false `why` field that "should have read 'once the dedupe order is pinned'." Check the
contract, not the `why`. The proposed script's specification reads "strip blanks, dedupe,
slugify" (`classification.json` L7, report.md L40). That is dedupe-before-slugify, the
baseline's reading A: 5 topics, with `retrieval-augmented-generation` emitted twice, so
step 2 writes `sources/retrieval-augmented-generation.html` and then overwrites it
(`without_skill/outputs/report.md` L45-63). The declared stdout compounds it:
`"dropped":{"blank":N,"duplicate":N}` would report 1 duplicate dropped while silently
emitting a duplicate slug. The baseline pinned reading B and said so at its gate. Same
class, opposite contract, and only one of the two contracts loses a topic file.

So the with-skill run's report named the ambiguity in prose, "exactly the case where two
runs can disagree on whether the title-case twin is the same topic" (report.md L54), and
its proposed contract answered that disagreement in the direction that clobbers a file,
with no statement that a choice had been made. That is not a wording defect. Under
`--out`-free Step 6 that contract is what gets implemented.

**This is why `decides` alone is insufficient.** A field that records the pinned
interpretation documents whatever the author picked. Here the author picked the harmful
reading while looking straight at the data that shows it is harmful. Pinning without
evaluating the consequence turns a silent bug into a documented one. The field must carry
the consequence, not just the choice.

**I accept the termination-condition hit and I am bounding the probe.** The Advocate is
right that the baseline's search ran until it found a disagreement
(`without_skill/outputs/transcript-notes.md` L20-24) and that "generate defensible readings
until one disagrees" is unbounded and unusable as a repeatable step. Bounded replacement,
a fixed three-shape checklist applied once per SCRIPT or HYBRID step, no generation:

- **Unordered composition.** The step names two or more transformations and the prose does
  not fix their order. The readings are the orderings the prose admits, which is
  enumeration, not generation. If the target ships sample data, run them and record the
  divergence; if not, record the readings and the consequence. Cap at 3 readings; more than
  3 is itself the finding, and the step goes to the user as underspecified.
- **Undefined derived quantity.** The step thresholds or compares a quantity it never
  defines how to derive ("under 200 words" over raw HTML). No probe needed and none
  possible without data; the missing definition is the finding.
- **Unnamed artifact or producer.** Feeds Objection 1's `consumes`/`produces` check.

That terminates, it is three checks rather than an open-ended investigation, and it
degrades correctly when the target ships no sample data: flag and pin, do not probe. It
also answers the "authoring-time versus run-time" hazard, because the checklist runs at
authoring time against whatever the target actually carries.

**Merged fix I am asking the Judge to consider:** the Advocate's `decides` field, made
mandatory when any of the three shapes fires, and required to carry three things: the
readings, the pinned choice, and the consequence of the choice on the target's real data
where data exists. Their field, my trigger and my required contents.

### Objection 3 — DROPPED.

Two things in A3 convinced me. First, the drop mechanism already exists: the >4-row gate
form offers "Apply a subset, list row ids in Other," so a user shown that s1's dedupe order
is undecided can already drop s1 today. The gap is that the report never tells them, which
is Objection 2's fix, not a new gate slot. I filed a structural defect where the real one is
informational.

Second, my own cited precedent argues against me. The baseline recorded its two blocking
decisions in `without_skill/outputs/gate.md` as a document with defaults, not as interactive
questions. I cited that as proof the gate needs question slots; it is proof the report needs
a section. The Advocate's bounded form, one section in the report plus a single gate question
of "accept all pinned interpretations (Recommended) / review in Other / drop the affected
rows," carries the same information at one AskUserQuestion call instead of N, and it
respects the four-option cap the skill already fights.

I ask only that the two pieces the Advocate already committed to survive into the Judge's
record, since they were the load-bearing parts of my version: the answer writes back into
`classification.json` so Step 5's re-read-from-disk rule carries it, and "drop the affected
rows" stays a first-class option rather than an Other free-text answer.

### Objection 4 — SUSTAINED, and I adopt the Advocate's stronger fix over mine.

The extension is correct and I checked it. Step 8 replaces step prose with an invocation
line plus retained rationale, so net displacement is (step tokens minus invocation tokens).
s7 is 24 tokens; `Run exactly: python3 scripts/render_index.py --stats .work/stats.json
--format table` plus exit semantics is comparable. My split fix would have left the SCRIPT
half overstated. Drop the token figure from the verdict line entirely, keep the per-step
`Tokens` column, which measures step size and claims no benefit.

**New substance: deleting the number leaves the skill with no benefit claim at all, and
that is the finding to hand up.** CC4 concedes "earns its cost" was never operationalized
and no measured after-cost exists in this workspace. With the verdict line's number gone,
`scriptify` ships zero quantified justification anywhere. That is the honest state and it
should be visible rather than papered over. Two concrete follow-ups:

1. Pin the removal. Add a case to `tests/test_render_report.py` asserting the verdict line
   contains no token figure, so it cannot silently return in a later edit. The current
   `NEEDS_SCRIPT` sum has survived because nothing tests the line.
2. Get one real number, once. Take a target with sample inputs, run it end to end before
   delegation and after, record actual tokens and wall clock for both. One measurement on
   one target closes the gap CC4 left open and would let the verdict line carry a
   defensible figure again. Until then the skill's case rests on variance and interface
   rigour, which is a real case, and it should be argued as that rather than as tokens.

### Objection 5 — SUSTAINED on the additive remedy. I withdraw "inverts".

**Conceded.** Interface specificity and pipeline coherence are two properties, and my
"inverts" framing collapsed them. Assertion 6 measured the property it names, and the grep
behind the baseline's failure is reproducible rather than a judgment call. I withdraw the
inversion claim.

**One correction to the blast-radius argument, because it is circular in the direction
Judge Q1 already flagged.** The Advocate argues the baseline's proposal "cannot be handed to
the write path at all," since Step 5 builds the manifest from declared argv and exit codes.
That measures the baseline against `scriptify`'s pipeline, which the baseline was not
running and had no reason to feed. Step 5 reads `classification.json`, not the report, so a
with-skill run that wrote its interfaces as prose would feed Step 5 identically. "Cannot
start our pipeline" is a statement about our pipeline. The reworded, format-neutral version
the Advocate accepts fixes this, which is why I am content.

**Where we now agree, and it is most of it.** Keep assertion 6 in the reworded form, "each
SCRIPT/HYBRID row specifies inputs, outputs and failure behaviour precisely enough to
implement without further questions," and add (a), (b) and (c). I withdraw deletion. I ask
for one addition the Advocate did not address: **regrade both arms against the full set and
publish the new scores.** Adding assertions without regrading leaves the 7/7 versus 6/7
headline standing on the old set, and that headline is what a reader takes away. My
prediction, on the record and falsifiable: with (a)(b)(c) added, the with-skill arm fails
(b) and (c) outright and (a) partially, the baseline passes all three, and the margin
reverses or levels. If it does not, that result answers this objection against me more
convincingly than any argument here.

**On the standing n=1 caveat: accepted, with one distinction that matters for the Judge.**
n=1 constrains claims about *behaviour*, so "the baseline reliably out-analyses the skill"
is unsupported and I do not assert it. It does not constrain claims about *artifacts on
disk*. `.work/stats.json` having no producer, `stats.url` having no producer, the verdict
line summing HYBRID tokens, and `render_report.py` having no provenance check are properties
of committed files, verifiable by reading them, and repeats would not change any of them.
Objections 1 and 4 need no further runs. Objections 2 and 5 involve behaviour and would
genuinely benefit from repeats before anyone concludes which arm analyses better.

## Phase 6 — Advocate's Surrebuttal

Two of the four sustained objections I now concede outright, including one where I was the
party arguing for the softer remedy and was wrong. Two I accept the remedy on while
disputing the severity characterization the Judge is being asked to record. I also bring
one defect neither side found, because it widens Objection 1's remedy in a way that makes it
worth more.

### A1' — Objection 1: CONCEDED, including exit 1. Plus a defect that widens the fix.

**The repaired check satisfies me.** Declared `consumes`/`produces` at field granularity
plus set arithmetic removes the failure I identified: it catches `stats.url` by the same
mechanism it catches `.work/stats.json`, because provenance stops being inferred from prose
written for humans and becomes a declared contract. That is a strictly better design than
what I was defending.

**I concede exit 1, and I name what convinced me.** Not the consistency argument, though it
is sound. Argument 2. The soft version is not hypothetical, it is this run: report.md L72
does name the missing brief path and the undefined house voice in prose, `render_report.py`
exited 0 regardless, and Step 4 went on to offer "Apply all 7 (Recommended)". My A1 proposal
was an advisory section rendered above the table rather than below it, and nothing in that
change touches the gate's default. An advisory that does not move the default reproduces the
observed outcome, and the observed outcome is the thing being complained about. My
"false-failure mode" concern also does not survive: with `requires_new_artifact` available,
declaring is always in reach, so the rule fires on an absent required field, which is what
the validator already does three times over.

**New substance: provenance is not the only cross-entry contract the validator cannot see,
and the same check should cover both.** SKILL.md Step 2 instructs "Give the fragments that
share a script the same `proposed_script.name`." Nothing verifies that entries sharing a name
declare compatible contracts. On this run they do not. I grouped `classification.json` by
script name:

    SHARED: source_stats.py
       s3 | exit: 0 sources found / 1 sources dir empty / 2 usage
       s4 | exit: 0 no thin sources / 1 at least one thin source / 2 usage
       exits identical: False

    SHARED: render_index.py
       s5 | exit: 0 rendered / 1 stats empty or missing required fields / 2 usage
       s7 | exit: 0 rendered / 1 stats empty or missing required fields / 2 usage
       exits identical: True

One script, two incompatible exit vocabularies. Exit 1 means "sources dir empty" in s3 and
"at least one thin source" in s4. Exit 0 means "sources found" in one and "no thin sources"
in the other, so a run with sources present and one thin source is exit 0 under s3's contract
and exit 1 under s4's. The consequence is not cosmetic: SKILL.md Step 8 says "Key the
branching off script exit codes" and "Write each branch as `exit 1 → …`", so an ambiguous
exit 1 propagates into the rewritten target SKILL.md as a wrong branch. `render_index.py`
shows this is not inevitable; s5 and s7 agree exactly. So the defect is real, specific, and
avoidable, and neither the Defender nor the Adversary caught it.

**Therefore widen the remedy.** The same validation pass that does `consumes`/`produces` set
arithmetic should assert that all entries sharing a `proposed_script.name` declare an
identical `exit` vocabulary, or declare their modes explicitly. Same exit 1, same place in
the pipeline, one extra rule, and it catches a class of defect that ships straight into the
rewritten SKILL.md.

**On S3, I concede the strong form.** CC5 is decisive: no gate answer in this suite ever
contradicted the recommendation, and this run's answer was dictated by the prompt. I cannot
claim the gate refused anything, and I withdraw "the gate is what stopped these defects."
What I keep, explicitly labelled as weak: the rule "Never write into the target without an
explicit pick" made "report only" terminal rather than advisory, and `facts.json` shows an
empty tree diff. That is evidence the stop path works, not evidence the gate exercises
judgment. The Adversary is right that the write path is untested and that this argues for
hardening it before it runs.

### A2' — Objection 2: remedy ACCEPTED, severity characterization DISPUTED.

**I accept the bounded three-shape checklist and the merged `decides` field.** The checklist
repairs the termination problem properly: enumerating the orderings a sentence admits is
enumeration, not generation; a cap of 3 with overflow as its own finding terminates; the
undefined-derived-quantity shape needs no data at all; and "flag and pin, do not probe" when
the target ships no sample data answers the authoring-time hazard I raised. I also accept
that `decides` must carry the consequence and not only the choice. Documenting a pick without
evaluating it is a weaker artifact than the baseline's gate.md, which gave both. The
Adversary's trigger and required contents are better than my field alone, and I withdraw my
version in favour of the merged one.

**I dispute "its proposed contract answered that disagreement in the direction that clobbers
a file."** The rebuttal says "Check the contract, not the `why`," and then cites
`classification.json` L7 and report.md L40. L7 is the `why` field. In report.md L40 that text
sits in the table's **Why** column, not the **Proposed script interface** column. The actual
proposed contract for s1 is:

    interface: python3 scripts/normalize_topics.py topics.txt --json
    stdout:    {"topics":[{"raw":"...","slug":"..."}],"dropped":{"blank":N,"duplicate":N}}
    exit:      0 topics found / 1 no usable topics / 2 usage

Nothing there fixes an order. Under reading B the same schema holds: `topics` carries 4
entries with distinct slugs and `dropped.duplicate` is 2. The stdout is fully satisfiable by
either reading, and if it leans at all it leans B, since emitting `raw` alongside `slug` per
entry is the shape you design when you expect a many-to-one collapse.

**And the phrase in the `why` is a paraphrase of the fixture, not an independent pin.** The
target's own step 1 reads "Drop blank lines, drop duplicates, and normalize each remaining
topic to a lowercase slug." The `why` restates that in the target's order. The run echoed the
source; it did not adjudicate between readings and choose the harmful one.

**Why the distinction matters to the Judge, and it is not a quibble.** "The run pinned the
destructive reading while looking at the data" is a judgment error, and the fix for a
judgment error is a better classifier. "The run recorded no pin at all and passed the
fixture's ambiguity through untouched" is an omission, and the fix is a required field. Only
the second is true here, and the second is exactly the remedy both of us have now agreed on.
Recording it as the first would overstate what a `decides` field is repairing and would
imply the classification step needs rework it does not need. The class was right, the
contract was order-neutral, and the gap was a missing decision. That is the finding.

### A4' — Objection 4: CONCEDED in full. One methodological requirement on the follow-up.

Drop the token figure from the verdict line, keep the per-step `Tokens` column, pin the
removal with a case in `tests/test_render_report.py`. I agree with all of it, including the
Adversary's honest observation that removal leaves `scriptify` with no quantified benefit
claim anywhere, and that this should be visible rather than papered over.

**New substance on follow-up 2.** "Run a target end to end before and after delegation" as
specified measures one quantity when the debate needs two. There is a one-time authoring cost
(what scriptify itself costs to run, 56,793 tokens on this scenario) and a recurring
per-run delta on the delegated target. The verdict line's claim is about the recurring delta.
CC4's "earns its cost" is about the authoring cost against the recurring delta multiplied by
how many times the target actually runs. A before/after on the target yields only the
recurring delta, so on its own it still cannot answer the question this debate was convened
to ask. **The measurement should report a break-even run count**, authoring cost divided by
per-run saving, because that single number is what tells a user whether to scriptify a skill
they run twice a year versus twice a day. It is the same experiment plus one division, and it
converts an unanswerable framing into a decidable one.

### A5' — Objection 5: circularity warrant CONCEDED, conclusion re-grounded, reading of the regrade DEFENDED.

**The circularity charge is correct as to my warrant and I withdraw that phrasing.** "The
baseline's proposal cannot be handed to the write path at all" measures the baseline against a
pipeline it was not running and had no reason to feed. Step 5 reads `classification.json`, not
the report, so the comparison was scriptify-relative. Conceded.

**The conclusion survives on pipeline-neutral grounds, and I restate it there.** On the
reworded standard we both accept, "precisely enough to implement without further questions,"
the baseline still falls short for any implementer, not merely for Step 5: `record_source.py`
"hard-fails on a slug collision" with no exit code and nothing for a caller to branch on;
`parse_topics.py` emits `[{topic, slug, path}]` with no stated behaviour on an empty
`topics.txt`. Those questions are unanswerable from the baseline report by anyone. So the
warrant was circular, the finding is not.

**I concede the prediction in advance rather than waiting to lose it.** I read (a), (b) and
(c) against both artifacts and the Adversary's forecast is accurate. On (a) the with-skill
report names the ambiguous data at L54 but never states that the two orderings give 5 topics
versus 4 and never names the overwrite, so partial at best; the baseline gives both at L45-63.
On (b) the with-skill run pins no extraction method and flags no gap; the baseline pins one at
gate.md. On (c) the with-skill run does not note the missing URL producer and its
`source_stats.py` assumes the field exists; the baseline states the defect and proposes the
producer. I will also predict something he did not: **the reworded assertion 6 fails both
arms**, because `.work/stats.json` with no declared producer is itself a further question. On
a 10-assertion set that puts the with-skill arm near 6 and the baseline near 9. The margin
does not level, it reverses. I would rather that be on the record from my side than extracted
later.

**What I defend is how that number should be read, and this is my last substantive point.**
(a), (b) and (c) are not three independent properties. They are three instances of one:
did the run empirically interrogate the fixture's prose and data for underspecification.
Weighting that as three of ten makes a single property 30% of the score, while the
tool-gating rule this scenario was built to test is 3 of 10 and passes unchallenged by any
objection in this debate. The honest headline after a regrade is therefore not "the skill
lost." It is: **the suite measured one property, it now measures two, and this run is strong
on the first and weak on the second.** Both halves have to ship or the regrade misleads in
the opposite direction from the current one.

**Which yields a concrete request. Run the regrade twice.** Once against the artifact as it
stands, establishing the gap. Once after Objection 2's bounded checklist and Objection 1's
`consumes`/`produces` check land in the skill, because a run carrying that checklist would
hit (a), (b) and (c) by construction: the unordered-composition shape fires on step 1, the
undefined-derived-quantity shape fires on step 4, and the unnamed-artifact shape fires on the
URL. A regrade of the current skill tells the user their skill is behind a no-skill baseline
on a property nobody was measuring. A regrade after the fix tells them whether the fix closes
it, which is the decision they actually face. The first number alone invites the wrong
conclusion, which is to drop the skill rather than to add three checks to Step 2.

**On the n=1 distinction: accepted, and it extends to the regrade.** The artifact-on-disk
claims are settled by reading committed files and need no repeats. Objections 1 and 4 are
closed on that basis. But the regrade of (a), (b) and (c) is a behaviour measurement, so the
reversal it produces will itself be a single draw. It is sufficient to justify adding the
checklist. It is not sufficient to conclude the baseline analyses better than the skill, and
the Judge should record it with that bound attached.

### What stands for the artifact after four phases

Stated plainly, since the credit side needs to reach the Judge alongside the debits. No
objection in this debate challenged any of the following: three of three agent-runtime-tool
steps classified correctly with tool-specific reasons and zero curl reimplementation, which
is the destructive failure this scenario exists to catch; `inventory.py` reporting `tools=-`
on the notion MCP step and the skill's mandatory human read catching it; validator-enforced
completeness across all seven ids; and the run finding the undefined house voice and missing
brief path, a defect the baseline missed, which the Adversary accepted in Phase 5 and which
narrowed his own objection from a capability claim to a missing-checkpoint claim. The
`.work/` intermediates being the correct shape of a HYBRID decomposition is now common
ground too, since `requires_new_artifact` exists precisely to permit introducing them.

The defects are real and every remedy in this debate is a bounded edit to Step 2, to
`render_report.py`, or to the assertion set. None of them is a reason to doubt the
classification engine. All of them are reasons to make it declare more of what it already
knows.

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
