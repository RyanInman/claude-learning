---
name: prompt-helper
description: Beginner-friendly planning helper for Claude Code that runs ONLY when the user explicitly invokes it with the /prompt-helper slash command. Do not load or trigger this skill automatically from natural-language requests, keyword matches, or inferred intent — it activates solely on the explicit /prompt-helper command. When invoked, it takes a plain-English description of what the user wants to do and returns four things in beginner terms: a scored assessment of their prompt with a stronger rewrite, advice for keeping the context window clean (starting with running /clear before the task), a model-selection recommendation (Haiku / Sonnet / Opus), and a call on whether plan mode is worth using. Useful at the start of a session to set up a good result, or mid-session when things feel off.
---

# Prompt Helper

A friendly pre-flight check for people new to Claude Code. Someone describes a
task in their own words; you hand back a short, encouraging plan that sets them
up to get a good result on the first try. No jargon, no metrics dashboards —
just four clear pieces of advice they can act on immediately.

This skill runs only when the user types **`/prompt-helper`**. It won't fire on
its own from a matching request — it waits to be called. It's meant to run
**before** the real work starts (though it's just as useful when a beginner is
stuck mid-task). Think of it as a two-minute chat with a patient senior engineer
who asks "okay, what are you trying to do?" and then points you in the right
direction.

## What you produce

Cover these four areas in order. Keep each one short: a few sentences, plain
language, warm tone. Add a one-line *why* so the person learns the reasoning
behind each rule.

**Always open with the same reminder: run `/clear` before starting.** A clean
context is the cheapest win in Claude Code, and it's the easiest thing to
forget. Lead every run of this skill with it, then move into the four areas.

1. **Prompt check + rewrite.** Score how they described the task, then match
   your help to the score: affirm a strong prompt, close the gaps on a decent
   one, or build a robust prompt together when it's thin.
2. **Keeping context clean.** One or two habits that fit their task, starting
   with the `/clear` reminder above.
3. **Which model.** Haiku, Sonnet, or Opus, with a one-line reason.
4. **Plan mode: yes or no.** A clear call, and why.

Close with one encouraging line. If they take away a single command, make it
`/clear`.

## Workflow

### 1. Understand the task

Get a rough sense of what they're trying to do. If their description is very
vague ("help me use Claude Code," "I want to fix my app"), ask one friendly
question just to land on a concrete task — a bug, a feature, a file. Save the
detailed questions for step 2, where they do the most good. If they already
named a task, move straight on.

### 2. Assess the prompt and rewrite it

A strong beginner prompt has the same qualities as a good request to a
colleague: specificity, evidence, and scope. Measure their phrasing against
these best practices, and build the rewrite from them:

- **Name the outcome.** Say what should be true when it's done. "Login stops
  crashing on `+` emails" gives Claude a target; "fix login" leaves it guessing.
- **Point at the location.** A file path or a clear area ("the checkout flow")
  saves a round of blind searching. In Claude Code, `@path/to/file` pulls a
  specific file straight into context.
- **State the done signal.** "…and add a test that covers it" or "…the page
  should load without the 500" tells Claude how to know it succeeded.
- **Paste the evidence directly.** A real error message, stack trace, or
  failing test output is the highest-signal input they have. Describing a bug in
  prose forces Claude to reconstruct what's already on their clipboard.
- **Keep it to one task per ask.** Bundling three jobs into one prompt weakens
  all three. Separate asks stay focused and produce reviewable changes.
- **In unfamiliar code, ask for a map first.** A prompt that changes nothing —
  "trace how an order flows from checkout to fulfillment; which files touch
  it?" — makes the next prompt far sharper.
- **Plan to iterate.** If the first result lands 80% of the way, telling Claude
  what's off ("good, but use exponential backoff") gets there faster than
  rewriting from scratch.

`references/beginner-guide.md` has the fuller "Prompt quality" section with a
worked weak→strong comparison if the person wants more depth.

**Score the prompt against the rubric in `references/prompt-rubric.md`.** It
scores five criteria — outcome (30), location (25), done signal (20), scope
(15), and evidence (10) — on the person's original wording, and sorts the result
into three bands. Read it now and apply it; the short version of the bands:

- **80% or higher — already strong.** Affirm the prompt, name the one or two
  things it does well, skip the question-and-rewrite loop, and move on to
  context, model, and plan mode. Keep it short.
- **40% to 79% — solid start with clear gaps.** Name the missing criteria, ask
  targeted questions to fill just those (see below), then rewrite from their
  answers.
- **Below 40% — needs a real build.** Build a robust prompt with them from the
  ground up, walking the rubric criteria one at a time as friendly questions.

Tell the person the score in plain, kind language ("about 85% of the way there"
or "let's build this one up together"). The reference has the full table, the
partial-credit and conditional-evidence rules, and three worked examples.

**Asking the targeted questions (the 40–79% and below-40% bands).** Drawing the
missing pieces out of the person is what turns a thin prompt into a strong one.
Ask about the specific criteria the rubric flagged as missing. In the middle
band, that's usually two or three questions; in the below-40% band, walk the
whole rubric. Keep each question short and concrete. Useful things to probe for:
- **The real outcome.** "When this works, what can a user do that they can't
  now?" or "what's the behavior you're after?"
- **The location.** "Do you know which file or part of the app this lives in?"
  (It's fine if they don't — that itself tells you to start with a map.)
- **The done signal.** "How will you check it worked — a test, a page that
  loads, a specific output?"
- **The evidence.** "Is there an error message or failing test you can paste
  in?"
- **The scope.** If they described several things, "which one do you want to
  tackle first?"

On mobile, prefer the tappable question tool for these so they can answer with a
tap instead of typing. When the prompt already scored 80% or higher, skip this
loop entirely and acknowledge the strong prompt as described above.

Then give them:
- A quick, kind read on what their current phrasing does well and which of the
  best practices above it was missing. Frame a weak prompt as normal and easy to
  fix — most beginners start here, and the fix is the whole point.
- A rewritten prompt they can copy-paste, built from their answers. Show it in a
  code block. Where a detail is still unknown, fill in a plausible placeholder
  and label it so they can correct it.

### 3. Advise on context hygiene

Context is Claude's working memory, and answers get worse as it fills up. Pick
the one or two habits that fit their task. Always include the first one:

- **Run `/clear` before you start.** A fresh session gives Claude a clean slate,
  so old, unrelated history can't muddy the new task. This is the habit to
  repeat at the start of every piece of work.
- Long single task? Use `/compact` around 60–80% full to keep going without
  losing the thread.
- Big codebase? Launch Claude from the specific subfolder you're working in.

`references/beginner-guide.md` has the fuller explanation if they want it.

### 4. Recommend a model

Default recommendation is **Sonnet** — it's the sensible all-rounder. Adjust
only when the task clearly calls for it:
- **Haiku** — quick, mechanical, low-stakes work (renames, boilerplate, simple
  lookups).
- **Sonnet** — everyday coding, the default. When unsure, pick this.
- **Opus** — deep reasoning: architecture decisions, tricky multi-file
  refactors, subtle bugs, anything spanning a lot of code.

Give the one-line reason so they learn the pattern. Tell them they switch with
`/model` and can check what's running with `/status`.

### 5. Call plan mode

Plan mode (**Shift+Tab**, or `/plan`) makes Claude propose an approach and touch
zero files until they approve. The rule of thumb:
- **Use it** when the change spans multiple files, when they're unsure of the
  approach, or when they don't know the code well. On a large or legacy
  codebase, that's most real changes — so lean toward yes.
- **Skip it** when they can describe the exact change in one sentence (a
  one-line fix, a rename).

Give a clear yes/no for their task, with the reason.

## Example

**Input:** "I want to make my login stop crashing when people use weird emails.
Can you help me set this up?"

**Output (first turn — draw out the details):**

> Great task to start with. A couple of quick questions and we'll turn this into
> a prompt that lands on the first try:
>
> - What kind of "weird emails" trigger it — do you have an example, or an error
>   message you could paste in?
> - Do you know which file or part of the app handles login?
> - How will you check it's fixed — is there a test, or a screen that should
>   just work?

*(Ask these with the tappable question tool on mobile. Once they answer — say
they reply "emails with a + sign, it's in auth/session.py, and I'd want a
test":)*

**Output (second turn — the plan):**

> Perfect, that's everything we need.
>
> **First, run `/clear`.** Starting fresh gives Claude a clean slate for this
> task. Make it a habit at the start of every new piece of work.
>
> **Your prompt.** Your first version named the goal. It didn't say where to
> look or how to know it's fixed, so Claude would have spent time hunting. Here's
> a stronger one built from your answers:
>
> ```
> Users get a crash when logging in with an email that contains a "+".
> The login logic is in auth/session.py. Fix the email validation so
> plus-addressing works, and add a test that covers it.
> ```
>
> **Which model.** Go with **Sonnet** — everyday bug-fixing is right in its
> wheelhouse. Switch with `/model` if you're on something else.
>
> **Plan mode?** You can skip it here. The fix fits in one sentence and touches
> one file, so just ask directly. Save plan mode (Shift+Tab) for changes spread
> across several files.
>
> You've got this. If the first result is 80% right, tell Claude what's off and
> let it adjust.

## Gotchas

- **Score the original wording, before your help.** The rubric measures what the
  person handed you. Scoring the improved version defeats the purpose and inflates
  every prompt to 80%+.
- **A high score means step back.** When a prompt clears 80%, affirm it and move
  on. Running the full question-and-rewrite loop on an already-strong prompt
  wastes the person's time and signals their good work went unnoticed. Keep the
  rest of the run brief.
- **Match the answer to a beginner's level, because overload kills confidence.**
  Pick what this task needs and leave the rest out. They can go deeper later.
- **Invent concrete details when rewriting a vague prompt, then flag them,**
  because a specific example teaches far better than "add a file path here." A
  labeled assumption is easy for them to correct.
- **Lean toward plan mode on unfamiliar or large code, because that's exactly
  where a blind edit goes wrong** — the cost of planning is tiny next to the
  cost of a bad multi-file change.
- **Don't fabricate metrics.** This skill plans ahead in plain language. It has
  no token counts or cache stats — that's what session-review is for, and it
  runs *after* a session.

## Reference files

- `references/prompt-rubric.md` — the scoring rubric for step 2: the five-criterion
  table, the partial-credit and conditional-evidence rules, the three bands, and
  worked examples. Read it whenever you assess a prompt.
- `references/beginner-guide.md` — the plain-English explanation behind each of the
  four areas (prompt quality, context habits, model choice, plan mode), with
  more examples. Read it when you need the fuller reasoning or the user wants
  to understand the "why" in more depth.
