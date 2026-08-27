---
name: interview
description: Interviews the user about a skill they want, then writes a 12-section skill brief and hands it to the authoring skill they choose. Use whenever someone wants a skill but the requirements are still fuzzy - "I want a skill for X but I'm not sure what it needs", "help me scope a skill", "interview me about this skill", "ask me questions first", "spec a skill before we write it", "what should this skill actually do", "figure out the requirements", or "turn this into a skill" when the workflow is only half described. Reach for it before skillit:create whenever the intent is vaguer than one clear job with a known output. Do NOT use when requirements are already settled and the user only wants the skill written (use skillit:create), to audit an existing skill (use skillit:review), or to stress-test a code design or plan (use grill-me or brainstorming).
---

# Skill Interviewer

Turn a fuzzy "I want a skill for X" into a brief an author can build from without guessing.

The interview exists because the expensive mistakes in a skill are decided before the first line: the skill was the wrong container, it straddled two jobs, its description never fires, or it never beat baseline. Each of those costs a full rewrite to find later and one question to find now.

You produce one file: `skill-brief-<name>.md`. You do not write the SKILL.md.

## Workflow

### Step 0: Before starting

Mine the conversation and every referenced file before asking anything. Re-asking what the user already said erodes trust in the interview, and users answer worse after the third question they consider redundant.

Extract whatever is already present:

1. The task the skill should do, and any example run in the transcript.
2. Corrections the user made to earlier attempts, because a correction names a baseline failure directly.
3. Input and output samples, file paths, tool names, commands.

Then name the target skill and pick its brief path. If the transcript already answers every slot in the brief, say so, fill the brief, run Step 4, and skip to the handoff. The gate matters most on this path, because nothing here was confirmed with the user. The interview is a gate, not a mandatory ritual.

### Step 1: Read the question bank

Read `${CLAUDE_SKILL_DIR}/references/question-bank.md`. It holds the verbatim questions and answer options for all five phases, plus the recommended default and the tradeoff behind each option.

### Step 2: Run the phases

Ask with `AskUserQuestion`, batched by phase, at most four questions per call. Give every question a recommended option first, labeled `(Recommended)`, and state the tradeoff in its description. A recommendation with a stated tradeoff turns a click into a decision; a bare recommendation invites rubber-stamping, and a rubber-stamped answer is worse than no answer because it looks settled.

When `AskUserQuestion` is unavailable, ask the same questions as numbered plain text, one batch per phase, and treat a single reply that covers several as answered.

| Phase | What it must settle |
|---|---|
| 1. Job and container | The one job in a single sentence. Whether a skill is the right container at all. |
| 2. Baseline failure | What Claude gets wrong today without the skill. This is the ROI gate. |
| 3. Triggering | Trigger phrases in the user's own words. Which sibling skill must not fire instead. |
| 4. Output shape | Fixed template, template with judgment slots, or free-form. What run 50 shares with run 1. |
| 5. Determinism and evals | Repeating mechanical steps that belong in a script. Domain gotchas. Three eval prompts. |

Use free text, not tiles, for the trigger phrases and the gotchas. Both are worthless paraphrased: description matching is keyword-based, so the user's exact wording is the asset, and a gotcha rewritten in your words loses the domain fact that made it worth capturing.

**Stop rule.** Stop when every required slot in the brief has a non-placeholder answer, or after ten turns that put a question to the user, tile or free text, whichever comes first. Eight is the cold-start floor, not a target: the three conditional follow-ups (Q1.3, Q2.2, Q4.2) cannot share a turn with their predicate. The remaining two turns are reserved for the follow-ups that add no new slot - Q1.1's read-back and Q2.1's single push - so a prompt that needs both still has a legal path. Record anything still unsettled in the brief's Open Questions section. Reason: answer quality degrades across a long interview, so an eleventh turn buys guesses dressed as answers. When the cap binds it binds on turns, not questions, so dropping a question that shares a turn with another recovers nothing - the only drop that buys a turn is Q4.2, so take the user's template as a free-text field inside Q4.1's turn instead. Never drop Q5.2, because gotchas are the one input the author cannot derive without the user. Do not aim for a question count - a count is met by padding.

### Step 3: Write the brief

Copy `${CLAUDE_SKILL_DIR}/assets/skill-brief-template.md` and fill every slot. Use the template exactly - the authoring skill reads the brief by section, so a renamed or dropped heading silently strips that input.

Write the Open Questions section last and rank it lowest-confidence first, naming what would settle each one. This section is the highest-value part of the brief: it points the author's attention at the parts most likely to be wrong, which is the one thing a finished brief cannot do for itself.

### Step 4: Validate

Run exactly:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check_brief.py <path-to-brief>
```

Exit 1 lists the missing or still-placeholder slots. Fill them from the transcript, write `none` where there is nothing to record, or move them into Open Questions with a reason - except section 4, section 7's `Form:`, and section 6's `Should fire:`. The first two are forced choices and must name a listed value; the third cannot be empty because the draft description has nothing to tune on - supply candidate phrasings yourself and mark them as yours. Then rerun. Do not hand off a brief that exits 1.

### Step 5: Hand off

Show the user the filled brief, then ask with `AskUserQuestion` which authoring path they want:

- **skillit:create** - full authoring loop with paired evals against baseline. The default when the brief names a measurable baseline failure. It reads sections 1 through 11 as settled, including the container in section 2, and asks only about section 12, so pass the brief path explicitly.
- **A lighter authoring skill** (`write-a-skill`, `fable-super-skill`) - drafts the folder without the eval harness. Neither has a brief branch of its own, so pass the brief path and say explicitly to read sections 1 through 11 as settled input.
- **Stop here** - the user takes the brief elsewhere.

Then invoke what they chose, passing the brief path. If the answer to Phase 1's container question was not "skill", skip this step: say which container fits and why, and offer the matching route (a `CLAUDE.md` line, `rule-context-builder` for a path-scoped rule, `update-config` for a hook).

## Worked example

**Input:** "I keep asking Claude to summarize our Sentry errors for standup and it comes out different every time. Make that a skill."

**Interview yield (abridged):** the transcript already held the task and the inconsistency complaint, so Phase 2 needed no question. Phase 4 revealed the real requirement - a fixed five-line format the team scans in ten seconds. Phase 5 surfaced that every past run re-wrote the same Sentry query.

**The Phase 4 call that produced it** — one question, recommended option first, tradeoff in every description:

```
Question: What must the standup blurb look like from run to run?
Header:   Output form
  [Fixed template (Recommended)] Every run produces the same sections in the
      same order. This is what makes run 50 look like run 1, and you named
      run-to-run drift as the problem.
  [Template with judgment slots] Fixed skeleton, depth left to Claude. Fits a
      report whose length depends on how much broke.
  [Free-form] No fixed shape. Only right when the deliverable genuinely differs
      every time, which contradicts the complaint you opened with.
```

Answer: fixed template. Follow-up Q4.2 asked for the five lines, which went into the brief verbatim.

**Brief excerpt:**

```markdown
## 1. One job
Turn the last 24h of Sentry issues into the team's fixed five-line standup blurb.

## 3. Baseline failure
Without the skill, Claude: varies the format every run - sometimes prose, sometimes
a table, issue counts sometimes omitted. Evidence: user's own complaint, three runs.

## 7. Output shape
Form: fixed template
Template or example output: paged / degraded-not-paged / new-since-yesterday /
top offender / anything to babysit
What run 50 must share with run 1: the same five lines in the same order

## 9. Script candidates
Fetch + group last-24h issues by culprit -> scripts/fetch_standup_issues.py
```

**Handoff:** skillit:create, because the baseline failure is measurable and the fixed template gives evals something to check.

## Gotchas

- **A described task is not a baseline failure.** Users answer Phase 2 by restating what they want done. Push once: "what does Claude get wrong today when you ask for this?" If there is no answer after one push, record that in Open Questions and say plainly that the skill may not beat baseline - a skill that ties baseline is pure recurring token cost.
- **"Everything about X" means two skills.** When the one-job sentence needs an "and", propose splitting into siblings with distinct trigger keywords. A straddling skill confuses triggering for both jobs.
- **A guarantee is a hook, not a skill.** "It should never push to main" is enforced once as a hook and free forever; as skill prose it is a request re-issued every turn. Route it out in Phase 1 rather than briefing a skill that cannot deliver it.
- **"Flexible output" contradicts wanting a skill.** Users say the output should stay flexible, then complain that runs differ. Ask what run 50 must share with run 1 - that question separates real latitude from an unstated template.
- **Do not draft the SKILL.md body.** Writing it inside the interview skips the authoring skill's eval loop and doubles the work when the user picks a different authoring path. Two rationalizations show up in testing, and both are wrong: the user said "just write it" (answer: write the brief, then offer authoring as the handoff they pick), and the brief came out so complete that authoring looks like a formality (answer: completeness is what makes the handoff cheap, not what makes it unnecessary). Red flag: you are about to open a path ending in `SKILL.md`, or you are typing frontmatter.
