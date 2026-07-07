# Beginner Guide: The Reasoning Behind the Four Areas

Read this when you want the fuller explanation for any of the four areas, or
when the user asks "why?" and deserves more than a one-liner. It's written so
you can quote or paraphrase pieces of it directly to a beginner.

## Contents

1. Prompt quality
2. Keeping context clean
3. Model selection
4. Plan mode

---

## 1. Prompt quality

Claude Code responds to the same things that make a good request to a
colleague: **specificity, evidence, and scope.** A beginner's prompt is usually
weak in one of these, and naming which one is the most useful thing you can do.

**The three ingredients of a strong prompt:**

- **Outcome** — what should be true when it's done? "Login stops crashing on
  `+` emails" is an outcome. "Fix login" is not.
- **Location** — where should Claude look? A file path (`auth/session.py`) or a
  clear area ("the checkout flow") saves a round of blind searching. In Claude
  Code, `@path/to/file` pulls a specific file in reliably.
- **Done signal** — how will they know it worked? "…and add a test for it" or
  "…the page should load without the 500 error" defines success.

**Paste evidence, don't paraphrase it.** If something is broken, the actual
error message, stack trace, or failing test output is the highest-signal thing
they can provide. Describing a bug in prose makes Claude reconstruct what's
already sitting in their clipboard.

**One task per ask.** "Fix the test, update the README, and rename the module"
produces worse results on all three than three separate asks. Small asks →
focused work → reviewable changes.

**Ask for understanding before changes, in unfamiliar code.** Some of the best
beginner prompts change nothing: "Trace what happens to an order from checkout
to fulfillment — which files touch it?" Getting a map first makes the next
prompt far better.

**Iterating beats restarting.** If the first try is 80% right, say what's wrong
("good, but it should use exponential backoff") rather than re-writing from
scratch.

**Weak → strong example:**

- Weak: `fix the login bug`
- Strong: `Users get a 500 when logging in with an email containing a "+". The
  error is in auth/session.py. Fix the email validation so plus-addressing
  works, and add a test case for it.`

The strong version names the symptom, the location, the definition of done, and
asks for verification — each element saves Claude a round of guessing.

---

## 2. Keeping context clean

The context window is Claude's working memory: everything discussed, every file
read, every command output shares one finite space, and **quality degrades as
it fills.** "Context rot" is the number-one reason long sessions get worse.

The good news for beginners: three habits cover almost everything.

- **`/clear` at task boundaries.** Finished one thing and moving to something
  unrelated? Clear. Dragging stale context into a new problem actively hurts —
  and they pay tokens for it. CLAUDE.md and skills survive a clear, so nothing
  important is lost.
- **`/compact` for continuity in a long task.** When one task runs long and the
  window is filling, `/compact` replaces the history with a dense summary so
  they can keep going. Do it around 60–80% full — waiting until it's nearly full
  means the summary itself is written by an already-degraded session. They can
  steer it: `/compact focus on the auth changes and the failing test`.
- **Scope to the subfolder.** On a big repo, launching Claude Code from the
  specific directory they're working in avoids loading a pile of irrelevant
  context (and picks up the local CLAUDE.md if there is one).

Two nice-to-knows if they're ready: `/context` shows what's filling the window
(check it when answers feel off), and handing a big exploration job to a
subagent lets that reading burn its own context instead of the main session's.

**Rule of thumb to give them:** *compact for continuity, clear for a clean
slate.*

---

## 3. Model selection

Matching the model to the task is the easiest speed-and-cost lever a beginner
has. There are three tiers:

| Tier | Character | Reach for it when |
|---|---|---|
| **Haiku** | Fastest, cheapest | Quick lookups, simple edits, boilerplate, routine renames |
| **Sonnet** | Fast, strong all-rounder | Everyday coding — the sensible default |
| **Opus** | Deepest reasoning, slower, priciest | Architecture, gnarly multi-file refactors, subtle bugs, big-context work |

**Guidance to pass on:**

- **Default to Sonnet.** When unsure, this is the answer.
- **Escalate to Opus** only when the task genuinely needs deeper thinking — they
  will feel the difference on complex planning and cross-cutting changes, and
  it's worth the extra cost there.
- **Drop to Haiku** for mechanical work where speed matters and the task is
  low-risk.
- Switch with `/model`; confirm what's actually running with `/status`. A
  surprising number of "why is this slow / shallow?" moments are just being on a
  different model than they thought.
- `/effort` tunes thinking depth *within* a model — higher for hard problems,
  default for routine work.

Model names change over time; `/model` always shows the current lineup.

---

## 4. Plan mode

Plan mode makes Claude analyze the code and propose an approach while touching
**zero files** until the person approves. They enter it with **Shift+Tab** (or
`/plan`).

**The rule of thumb:**

- **Use plan mode when** the change spans multiple files, when they're unsure of
  the approach, or when they don't know the code well.
- **Skip it when** they can describe the exact change in one sentence — a
  one-line fix, a simple rename.

**Why it matters more on legacy / large codebases:** in code nobody fully
remembers, a blind edit can land in the right-looking spot in the wrong place,
and it reads as correct. Planning first catches that for almost no cost. So on a
big or unfamiliar codebase, plan mode tends to become a habit — lean toward yes.

One more helpful detail: plan-mode quality depends on how well the project is
described to Claude (its CLAUDE.md). If a beginner's plans come back vague, a
better CLAUDE.md is often the real fix — but that's a next-step lesson, not a
first-session one.
