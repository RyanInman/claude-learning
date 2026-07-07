# Prompt Quality Rubric

Read this to score a beginner's prompt and decide how much help to give. Score
the person's **original wording, as written, before any of your help** — scoring
an improved version inflates every prompt to the top band and defeats the point.

## The scoring table

Award the points for each criterion the prompt already satisfies, then total
them into a percentage.

| Criterion | Points | Earn the points when the prompt… |
|---|---|---|
| Outcome | 30 | says what should be true when it's done, beyond "fix it" or "make it work" |
| Location | 25 | names a file, folder, or clearly bounded area to look in |
| Done signal | 20 | states how success is checked — a test, a screen, a specific output |
| Scope | 15 | targets one task rather than bundling several |
| Evidence | 10 | includes the actual error, stack trace, or failing output |

**Partial credit is fine.** A vague gesture at an area ("somewhere in the auth
code") earns roughly half the Location points; a precise path (`auth/session.py`)
earns full marks. Use judgment rather than treating each row as all-or-nothing.

**Evidence is conditional.** It only applies when something is broken. For a task
with no error to paste — a new feature, a refactor, a rename — mark Evidence as
not applicable and score out of 90. The percentage is then points-earned ÷
points-applicable.

## The three bands

**80% or higher — already strong.** Tell the person plainly that their prompt is
in good shape and name the one or two things it does well. Skip the
question-and-rewrite loop. Offer at most one small polish if something is
genuinely missing, then move on to context, model, and plan mode. Keep this part
short so someone who came in prepared feels recognized.

**40% to 79% — solid start with clear gaps.** Name the specific criteria the
prompt is missing, ask targeted questions to fill just those (usually two or
three), then hand back a rewrite built from their answers.

**Below 40% — needs a real build.** The prompt is too thin to rewrite by
guessing, so build a robust one with the person from the ground up. Walk through
the rubric criteria one at a time as friendly questions, gather each piece, and
assemble a complete, copy-paste-ready prompt that would now score high. Keep the
tone encouraging — a thin first prompt is the normal starting point, and this is
the part that makes the biggest difference to their result.

Tell the person the score in plain, kind language ("this is already about 85% of
the way there" or "let's build this one up together"). The number orients them;
the help is the point.

## Worked examples

**Example A — scores ~30% (below 40%, build it up).**
> "fix my login it's broken"

Outcome: 0 (says "broken" without a target behavior). Location: 0. Done signal:
0. Scope: 15 (one task). Evidence: 0. Total 15/100 → 15%. This one gets the
full guided build: ask what "broken" looks like, where login lives, what fixed
would look like, and whether there's an error to paste.

**Example B — scores ~75% (middle band, close the gaps).**
> "Users get a 500 logging in with a `+` email. It's in auth/session.py. Fix the validation."

Outcome: 30. Location: 25. Done signal: 0 (no test or check named). Scope: 15.
Evidence: 5 (mentions the 500 but pastes no trace). Total 75/100 → 75%. Ask two
questions — how they'll confirm the fix, and whether they can paste the actual
error — then rewrite.

**Example C — scores ~95% (strong, affirm and move on).**
> "Users get a 500 logging in with a `+` email — stack trace below. The bug is in the validation in auth/session.py. Fix it so plus-addressing works and add a test covering the `+` case. [trace pasted]"

Outcome: 30. Location: 25. Done signal: 20. Scope: 15. Evidence: 10. Total
100/100 → 100%. Tell them it's an excellent prompt, note that it names the
symptom, location, done signal, and evidence, and move straight to model and
plan mode.
