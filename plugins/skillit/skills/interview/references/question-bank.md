# Question Bank

Verbatim questions and answer options for the five interview phases. Every question lists its recommended option first with the tradeoff that justifies it, because an option whose tradeoff is unstated gets picked for its position rather than its fit.

Skip any question the transcript already answers. Adapt wording to the user's vocabulary — a user who says "thing that checks my PRs" should not be asked about "invocation surfaces."

## Contents

- [Phase 1 — Job and container](#phase-1--job-and-container)
- [Phase 2 — Baseline failure](#phase-2--baseline-failure)
- [Phase 3 — Triggering](#phase-3--triggering)
- [Phase 4 — Output shape](#phase-4--output-shape)
- [Phase 5 — Determinism, gotchas, evals](#phase-5--determinism-gotchas-evals)
- [Calibrating for the audience](#calibrating-for-the-audience)

---

## Phase 1 — Job and container

**Q1.1 — the one job.** Free text: "In one sentence, what should Claude be able to do after this exists?" Read the answer back as a single sentence and get confirmation. If the sentence needs an "and", flag the split now.

**Q1.2 — container.** Tiles, header `Container`:

| Option | Description to show |
|---|---|
| A skill (Recommended) | A multi-step procedure, or one that needs bundled scripts, or one that matters only in one corner of the work. Loads on trigger and stays in context for the session. |
| A CLAUDE.md line | An always-true convention — naming, style, one gotcha. Costs tokens every turn of every session, so only a rule that applies everywhere earns the space. |
| A path-scoped rule | A rule true only for certain files. Loads when Claude touches a matching path, so it costs nothing the rest of the time. |
| A hook | A guarantee that must hold every time, with no exceptions. Enforced once by the harness instead of re-requested as prose every turn, so it cannot be talked out of. |

Only "a skill" continues the interview. For the others, name the route and stop.

**Q1.3 — skill type**, asked only when Q1.2 answered "a skill". Tiles, header `Skill type`. This selects which sections the skill needs, so a wrong answer produces a brief with the wrong required parts:

- **Technique** — a method with steps (a debugging loop, a migration). Needs one worked example and a Gotchas section.
- **Discipline** — enforces a rule under pressure (test-first, no force-push). Needs the specific loopholes closed.
- **Pattern** — a way of thinking (when to reach for X). Needs recognition cues and counter-examples.
- **Reference** — API, schema, or command docs. Needs findability and a table of contents, not examples.

## Phase 2 — Baseline failure

This phase decides whether the skill is worth building, so do not skip it even when the user seems certain.

**Q2.1 — the failure.** Free text: "When you ask Claude to do this today, without any skill, what does it get wrong?" Accept concrete answers only: wrong format, missed step, wrong file, invented API, different result each run.

If the answer restates the task ("it should summarize the errors"), push exactly once: "that is what you want it to do — what does it actually do wrong when you ask?" One push, then move on. A second push reads as an interrogation and buys nothing.

**Q2.2 — evidence**, asked only when Q2.1 produced a concrete failure. Tiles, header `Evidence`:

- **Seen it repeatedly (Recommended)** — the failure is reproducible, so evals can measure it and the skill has a target to beat.
- **Seen it once** — may be a one-off; the first eval iteration will confirm or clear it.
- **Expecting it, not observed** — record as unverified. The brief will say so, because an unmeasured baseline is the most common reason a finished skill turns out to tie baseline.

## Phase 3 — Triggering

**Q3.1 — trigger phrases.** Free text, and keep the answer verbatim: "Give me every way you might phrase this request — 6 to 10 of them, however you would actually type it, including the sloppy versions." Description matching is keyword-based, so a paraphrase discards the asset.

If the user offers fewer than four, add candidates yourself and mark them as yours in the brief, because a description tuned on invented phrasings triggers on invented requests.

**Q3.2 — anti-triggers.** Free text or tiles depending on what is installed: "Which requests look like this one but should get something else instead?" Name the sibling skill for each. Overlapping siblings are the main source of false-positive firing, and a named sibling turns into a negative trigger in the description.

## Phase 4 — Output shape

**Q4.1 — form.** Tiles, header `Output form`:

- **Fixed template (Recommended when the user complained about inconsistency)** — every run produces the same sections in the same order. This is what makes run 50 look like run 1, which is usually the reason someone wants a skill.
- **Template with judgment slots** — fixed skeleton, content depth left to Claude. Fits reports whose length depends on findings.
- **Free-form** — no fixed shape; Claude decides per run. Only right when the deliverable genuinely differs every time, such as design feedback.

**Q4.2 — the template itself**, asked only for the first two answers. Free text: "Paste a good example of the output, or list its sections in order." An example output is worth more to the author than any description of the format.

**Q4.3 — run 50.** Free text: "What must run 50 look like next to run 1?" This is the question that exposes an unstated template behind a "keep it flexible" answer.

**Q4.4 — degrees of freedom.** Tiles, header `Freedom`, only when the skill involves operations rather than prose:

- **Low — exact commands** for fragile operations where one wrong flag breaks the run.
- **Medium — parameterized** when a preferred pattern exists but inputs vary.
- **High — text guidance (Recommended for judgment work)** when many approaches are valid and the right one depends on context. Over-specifying judgment work is railroading and fails on inputs the author did not foresee.

## Phase 5 — Determinism, gotchas, evals

**Q5.1 — repeating mechanical work.** Free text: "Is there a step you do the same way every single time — a command, a query, a parse, a format conversion?" Each one is a script candidate. Compiling it into `scripts/` once removes it from every future run's token cost and removes the variance with it.

**Q5.2 — gotchas.** Free text, kept verbatim: "What does someone new to this get wrong — a fact about your setup that Claude could not guess from the code?" This is the highest-signal content in any skill, and it is the only content the author cannot derive without the user.

**Q5.3 — eval prompts.** Offer three drafted from Q3.1's phrasings and ask for corrections rather than asking the user to invent them. Cover one plain case, one edge case, and one near-miss that should exercise the anti-triggers. Reason: a near-miss eval catches an over-broad description, which no plain-case eval can.

## Calibrating for the audience

Users span a wide range of familiarity with this vocabulary. Read the cues in how they phrase the request:

- "Progressive disclosure", "frontmatter", "eval" — safe with a technical user who has used these terms.
- "Template", "trigger phrase", "script" — safe with anyone.
- Replace "degrees of freedom" with "should Claude follow exact steps here, or use its judgment?" unless the user has already used the term.

When unsure, define the term in the option description rather than assuming. A question the user does not understand returns a random answer that then looks settled in the brief.
