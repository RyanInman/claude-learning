# Micro-testing a wording

Read this before spending a full eval round on a change to how a rule is worded. A paired eval run answers "does this skill work." It costs six subagents and several minutes, and it cannot tell you which of two sentences did the work. A micro-test can, for a fraction of the cost.

Use it when you are choosing between two phrasings, when `skillit:review` hands you a 6-7 finding with a named test attached, or when you are about to add guidance and do not yet know whether the failure it targets is real.

## Contents

- [The procedure](#the-procedure)
- [Reading the results](#reading-the-results)
- [What a micro-test cannot do](#what-a-micro-test-cannot-do)

---

## The procedure

**1. Write the control first.** The control is the same prompt with no guidance at all. Run it before anything else, because if the control does not exhibit the failure, there is nothing to fix — stop, and do not add the words. Guidance against a failure that does not occur is pure recurring cost, and it crowds out the rules that matter.

**2. Put the guidance in its real context.** The system prompt is the full skill, or the full prompt template, as the model will actually see it. Guidance tested in isolation behaves differently from the same guidance buried on line 90 of a body, because position and surrounding instructions both change how strongly it binds.

**3. Give the user message a task that tempts the failure.** A task the model would pass anyway measures nothing. Include the competing incentive — the deadline, the sunk cost, the instruction to be thorough — that makes cutting the corner attractive.

**4. Run five or more reps per variant, one fresh context each.** A single sample lies. Use a subagent per rep, or a raw API call if you have one.

**5. Read every flagged match yourself.** Score with a script if you like, but a template echo and a quoted counter-example both look like hits to a regex. Automated counts overstate failure and success in roughly equal measure, so the count is a filter for your reading, not a result.

## Reading the results

**Variance is the metric, not just the mean.** When guidance lands, the reps converge on the same shape. Five different interpretations across five reps means the wording is not binding, even when four of them happen to pass — you got lucky, and run six will not be. Tighten the form before adding words.

Compare three numbers: control, variant A, variant B. A variant that beats the other variant but not the control is worse than saying nothing, which happens more often than authors expect — a prohibition aimed at a shaping problem can produce more of the unwanted content than no guidance at all.

Record what you ran in the skill's workspace so the next iteration does not re-litigate a settled question.

## What a micro-test cannot do

It verifies wording. It does not verify the skill.

A discipline skill still needs pressure scenarios, because the failure it prevents only appears under pressure a micro-test does not reproduce. Any skill still needs the paired baseline eval, because that is what decides whether the skill earns its recurring cost. Micro-tests sit before both — they make the expensive runs test a wording you already have reason to believe in.
