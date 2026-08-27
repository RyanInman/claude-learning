---
name: brainstorming
description: Turns a vague build request into an agreed plan: checks whether the request is genuinely ambiguous, interviews the user with 3-7 batched multiple-choice questions via AskUserQuestion, then emits a plan with EARS requirements, a build order, and a marked assumptions log. Use whenever the user asks for something to be built, added, changed, or designed and real decisions are left open - "let's build X", "add a feature for Y", "help me design this", "we need a dashboard/importer/API for..." - or any request where two competent engineers would build different things from the same sentence. Also use when the user wants an idea scoped or asks for a spec before code. Do NOT use when the change is describable in one sentence with no open decisions, when an approved plan already exists (follow it), or when diagnosing a bug. Prefer the brainstorming skill for open-ended back-and-forth, mockups, or diagrams; use this one for the fewest possible questions, batched multiple choice, and a spec-shaped plan.
---

# Brainstorming

Turn a vague request into a plan both sides agree on, using as few questions as the request actually needs.

Language models under-ask by default. Preference training rewards a complete, confident answer over an incomplete clarifying question, so the trained reflex is to guess at the fork and keep going. Benchmarks put the rate at which models ask when they should near 13%. This skill overrides that reflex — but only where a question would change what gets built, because the opposite failure, interrogating someone about a one-line change, drives them away just as fast.

## Step 0: Before starting

Collect these before you ask the user anything, because a question whose answer is already in the conversation wastes the user's turn and reads as inattention:

- What the user wants built, in their words.
- Which files, systems, or products it touches.
- Any constraint already stated: deadline, stack, existing pattern to follow, thing not to break.
- Whether a spec, ticket, or plan for this already exists.

Mine the conversation history and the repository first. Read the code the request touches. If every item above is already known, say nothing about this step and move to Step 1.

## Step 1: Detect the ambiguity before asking about it

Silently write 2-3 different competent readings of the request. Do not show them yet. Each reading must be a thing someone could actually build.

Then compare them on three axes:

1. **Artifact** — do the readings produce different files, screens, or endpoints?
2. **Behavior** — would a test pass under one reading and fail under another?
3. **Cost** — do the readings differ by more than roughly 2x in work?

A fork on any axis is material. A fork on none is cosmetic.

Example. Request: "add export to the reports page."

- Reading A: a CSV download button on the existing report table.
- Reading B: a scheduled email that sends the report as a PDF weekly.
- Reading C: an API endpoint other systems pull from.

These differ on all three axes. Ask.

Counter-example. Request: "the date column should show relative time like '3 days ago'."

- Reading A: format the existing date field with a relative formatter.
- Reading B: same, plus a tooltip with the absolute date.

These differ only in a detail you can propose in the plan. Do not run an interview.

## Step 2: The skip gate

Skip the interview and go straight to a short plan when any of these holds:

- No material fork survived Step 1.
- You can describe the finished change in one sentence, naming the files.
- The user already gave a spec, a ticket, or a detailed prompt covering the forks.
- The user said to just build it.

When you skip, do not use the Step 6 plan template. A rename does not survive a Won't-have section, and a requirement that restates the request in EARS costume is a sentence the user skims past. Write four lines instead:

- The reading you chose, in one sentence.
- The files or symbols you will touch.
- Any call you made on the user's behalf, marked ASSUMED.
- How you will check it worked.

Then start. Do not ask for approval on the skip path, because a change describable in one sentence costs less to correct after the fact than to pre-approve.

## Step 3: Ask, in batches, by theme

Ask 3-7 questions total across the whole interview. Below 3 you have not covered the forks. Above 7 the user starts answering carelessly to make it stop.

Use `AskUserQuestion`. Send one theme per call, questions batched inside it. Move general to specific across calls.

The five themes, in order:

| Theme | Resolves |
|---|---|
| Scope and users | Who uses it, what is in and out of this change |
| Data and integrations | Where data comes from, what it touches, what format |
| Edge cases and errors | Empty, huge, malformed, concurrent, failed |
| Non-functionals | Speed, scale, security, offline, accessibility |
| Success criteria | How the user will know it works |

Skip any theme the request already settles. Most requests need two or three themes, not five.

Rules for each question:

- **Ask only about forks.** Before writing a question, answer this: would a different answer change the plan or the code? If not, delete the question. Ranking questions by whether the answer changes the outcome is the whole selection principle.
- **Offer concrete options, not open prompts.** Two to four options the user can recognize, each naming a real outcome. An option like "standard approach" tells the user nothing; "one CSV per report, downloaded in the browser" tells them everything.
- **Keep options balanced.** Do not write three weak options around your preferred one. A leading question returns your own opinion with the user's name on it.
- **Never ask what the user cannot answer, and never ask what you can look up.** The user owns product and preference decisions. You own technical ones — library choice, file layout, algorithm — and every fact already sitting in the repo: row counts, schema, versions, whether a symbol is exported. A question whose answer is in the code spends the user's turn on work you skipped.
- **Recommend when you have grounds.** Put your recommended option first and mark it, because a user with no strong opinion wants a default, not homework.

Read `references/question-themes.md` for worked option sets per theme when you need a starting point.

## Step 4: Keep an assumptions log

Every fact in your plan is either CONFIRMED — the user said it — or ASSUMED — you filled it in. Mark each one. Never let an assumption reach the plan unlabeled, because an unlabeled assumption is indistinguishable from a requirement and gets built as one.

A decision you made is not an assumption. When you pick a library, a limit, a window, or a threshold, put it in the requirements and the build order where the reader will act on it. Reserve ASSUMED for facts you could not verify and the user might reverse, and say what changes if the guess is wrong. Readers scan the two differently: the plan body is what gets built, the log is what might be wrong, so a decision filed in the log gets skimmed past.

## Step 5: Stop

Stop asking when the next question would not change the plan, when you have spent 7 questions, or when the user shows impatience. Then say what you still do not know and what you assumed for it, rather than asking again.

## Step 6: Emit the plan

Present the plan in the conversation. Do not write a spec file unless the user asks for one.

Read `references/plan-format.md` for the template and a filled example. Its shape:

1. **Outcome** — one paragraph, written as though the change already shipped and you are telling a user what they can now do.
2. **Requirements** — EARS syntax, grouped Must / Should / Could / Won't.
3. **Acceptance criteria** — Given/When/Then, only for requirements that could plausibly fail. A criterion that restates its requirement in different words tests nothing and pads the plan, so skip it.
4. **Non-functional requirements** — only the ones that constrain the build.
5. **Build order** — numbered steps, each naming the files it touches and how to verify it.
6. **Assumptions and open questions** — the Step 4 log, CONFIRMED and ASSUMED marked.
7. **Out of scope** — what you are deliberately not building.

Two rules govern the content, because a plan can satisfy the template and still be unusable:

**Name real things.** Every requirement names the actual table, endpoint, file, or symbol it governs. "The system shall aggregate the main transactional record" is a placeholder wearing a requirement's clothes — nobody can test it or build from it. Read the schema and use the real name. Where you cannot, write the name you are guessing and mark it ASSUMED.

**Order the work so it can stop early.** Sequence the steps so the user still has something that runs if they halt after any one of them. A plan that only pays off at step 9 gives them no way to cut scope once the estimate lands.

Then ask the user to approve, correct, or cut. Start building only after they answer.

## Gotchas

| Failure | What it looks like | Fix |
|---|---|---|
| Under-asking | You picked a reading silently and built the wrong thing | Step 1 forces the competing readings into the open |
| Over-asking | Five questions about a rename | The Step 2 skip gate |
| Leading question | Options are your preference plus decoys | Write each option as a real outcome someone would pick |
| Sycophancy | You ask "this looks right?" and the user agrees with your framing | Ask the user to choose between options, never to confirm yours |
| Silent assumption | The plan states a requirement the user never gave | Mark every line CONFIRMED, ASSUMED, or OPEN |
| Unanswerable question | You ask the user which caching layer to use | Route technical questions to yourself; ask the user only decisions |
| Premature convergence | You generate one reading, then question its details | Generate the readings before writing any question |
| Ceremony over substance | The plan satisfies the template but names no file and gives no order | Name real things; give a stoppable build order |
| Asking what the repo knows | You ask the user how many rows a table has | Read the schema; ask the user only what the code cannot tell you |

## Worked example

**Input:** "we need some kind of notification thing for when orders fail"

**Step 1, silent readings:** (A) in-app banner for the ops team on the orders screen; (B) email or Slack alert to an on-call rotation; (C) webhook other systems subscribe to. Different artifacts, different behavior, roughly 3x cost spread. Material fork — ask.

**Step 3, one AskUserQuestion call, Scope and users theme:**

- Who needs to know when an order fails? → Ops team watching the dashboard / On-call engineer away from the screen / Both / The customer
- How fast do they need to know? → Within seconds / Within the hour / Next business day
- Which failures count? → Payment declines only / Any failed order / Any order stuck over N minutes

**Answers:** on-call engineer, within seconds, any failed order.

That collapses the fork to reading B and settles the trigger. A second call on Data and integrations asks two more — which channel receives the alert, and what the message must carry — and that is enough. Five questions total, then the plan.
