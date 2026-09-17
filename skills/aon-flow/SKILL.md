---
name: aon-flow
description: Turns loose requirements into a test-carrying implementation plan file, drafted in plan mode and written on approval. Scans the repo for specs, mockups, tickets, and screenshots, confirms which are authoritative, interviews with 3-7 batched AskUserQuestion questions, inventories the tests that already cover the request, then writes a markdown plan file under plans/ with acceptance criteria, a test plan, a UAT checklist, and a build order. Use whenever the user wants a plan before code - "aon-flow", "plan this out", "write me an implementation plan", "spec this before we build", "turn this ticket into a plan", "what tests do we need for this" - or pastes a ticket, drops a design image, or describes a feature in a few loose sentences and asks what to build. Also use to revise a plan file that already exists. Do NOT use to execute a plan or run red-green-refactor (use the tdd skill), for a conversation-only plan with no file (use brainstorming), or to debug a failing test (use diagnose).
---

# aon-flow

Take an under-specified build request and leave a plan file on disk whose structure carries
the tests. Any executor picks it up afterwards: the `tdd` skill, a subagent, or the user.

This skill does not write code and does not run tests. It interviews inside plan mode, so no
file in the target codebase changes while the user answers. The plan file is the one file it
creates, and it lands after the user approves.

## Step 0: Before starting

Collect these before you ask the user anything. A question the conversation already answers
wastes the user's turn:

- What the user wants built, in their words.
- Which files, systems, or screens it touches.
- Any constraint already stated: deadline, stack, pattern to follow, thing not to break.
- Whether a plan file, ticket, or spec for this already exists.
- The test runner and test directories the repo uses.

Mine the conversation history, the attached files, and the repo first. Read `package.json`
scripts, the CI config, and the test directories to identify the runner. Never ask the user
which runner the repo uses, because the repo answers faster and more exactly than a person.

Accept the request in whatever shape it arrives: a pasted ticket, a voice-note transcript,
three loose sentences, or an image with one line of text. Turn each ambiguity into a
question in Step 4 rather than a silent guess. Do not ask the user for a template.

## Step 1: Enter plan mode

Call `EnterPlanMode` before the scan. Plan mode guarantees no file in the target codebase
changes while you interview, so the user can answer freely.

Plan mode blocks every write, the plan file included. So draft the plan in Step 7, present
it through `ExitPlanMode` in Step 8, then write the file once the user approves.

## Step 2: Scan the repo for resources

Run the bundled scanner at `scripts/scan_resources.py`, under the base directory printed in
this skill's invocation header:

```
python3 BASE_DIR/scripts/scan_resources.py . --limit 20
```

It prints one candidate per line as `group`, `path`, `bytes`, `modified`, tab separated and
balanced across three groups: `spec`, `image`, `plan`. The cap is 20 because a longer list
turns the next question into homework.

Exit code 1 with `no candidates found` means the repo holds no candidates. That is a branch,
not a broken script. Do not rerun it.

Scan before you ask. A resource the user forgot they wrote is the cheapest requirement in
the run.

Read the paths, not the files, at this point. Then present the plausible hits in an
`AskUserQuestion` call and let the user mark which are authoritative. Group the options by
what each resource decides: visual truth, behavior truth, prior plan.

When the scan prints nothing relevant, ask the user for paths. Do not proceed
resource-blind, because a plan built without the mockup restates the request instead of
sharpening it.

When the scan returns a `plan` hit that covers this same request, stop and offer to revise
it. See Step 7.

## Step 3: Read what the user confirmed

Read every confirmed resource. Read images through the Read tool rather than skipping them,
because a screenshot carries layout, copy, and state that prose restates badly.

Record each resource's path. The plan cites them in its Resources section, so a reader can
check the source of any requirement.

## Step 4: Interview

Use `AskUserQuestion`. Send one theme per call. Batch that theme's questions inside the call.

Ask 3-7 questions across the whole run. Below 3 the forks stay open. Above 7 the user
answers carelessly to make it stop.

| Theme | Resolves |
|---|---|
| Scope | What is in and out of this change, who uses it |
| Acceptance criteria | How the user will know it works |
| Edge cases | Empty, huge, malformed, concurrent, failed |
| UAT | What a person must click through by hand before sign-off |

Skip any theme the request or the resources already settle. Most requests need two themes.

Rules for each question:

- **Ask only about forks.** Would a different answer change the plan? If not, delete the
  question.
- **Offer concrete options.** Two to four options naming real outcomes. "Standard approach"
  tells the user nothing.
- **Ask the user only what they alone can answer.** You own library choice, file layout, and
  every fact the repo holds. The user owns product and preference decisions.
- **Recommend when you have grounds.** Put your recommended option first and mark it,
  because a user with no strong opinion wants a default, not homework.

## Step 5: Inventory the tests

Find the tests that already cover the request. Name each one by file and test name. State
which requirement it already proves.

Then propose the tests that close the gap. Each proposed test names its file, its
Given/When/Then, and the requirement it proves.

When the repo has no test harness, write a starter test plan instead: which tier (unit,
integration, end-to-end), the runner to add, and the first failing test to write.

Put manual sign-off steps in the UAT checklist, not the test plan. A runner cannot assert a
visual match, a copy tone, or a flow crossing two systems, so a person checks those.

## Step 6: Resolve conflicts out loud

When a user answer contradicts a resource you read, raise it in an `AskUserQuestion` call
naming both sides and their paths. Do not pick a winner silently, because a plan built on
the losing side of an unstated conflict fails review after the work is done.

Example option pair: "Follow your answer — the 3-column grid. `mockups/orders.png` shows 4
and is stale." / "Follow the mockup — 4 columns. Your answer was about the old design."

This conflict question counts toward the 3-7 budget.

## Step 7: Draft the plan

Draft the full plan text. Its path is `plans/<slug>-plan.md`, where `<slug>` names the
change in two to four words, like `order-export-plan.md`.

When a plan file for this request already exists, revise it in place. Read it first, ask
only about what changed since it was written, then draft a rewrite for the same path. Never
write a second file with a new slug for the same change, because two plans for one change
leave the executor to guess which is live.

Read `references/plan-file.md` for the section template and a filled example. Follow it
exactly, because the user reached for this skill to get a plan that looks the same on run 50
as on run 1.

Mark every fact CONFIRMED or ASSUMED. CONFIRMED means the user said it. ASSUMED means you
filled it in. An unmarked assumption reads as a user decision and gets built as one.

## Step 8: Present, then write the file

Call `ExitPlanMode` carrying the drafted plan, and name the path the file will take. Ask the
user to approve, correct, or cut.

On approval, write the file to `plans/<slug>-plan.md` and report the path. On a correction,
fold it in and present again. Write no other file, and start no implementation work,
because execution belongs to the `tdd` skill, a subagent, or the user.

## Gotchas

| Failure | What it looks like | Fix |
|---|---|---|
| Resource-blind plan | The plan restates the request and cites nothing | Run Step 2 before the interview, because a mockup in the repo outranks anything the user can recall on the spot |
| Skipping the images | You read the spec and ignore `design.png` | Read images through the Read tool, because layout and copy survive the image and not the prose |
| Duplicate plan files | `orders-plan.md` and `order-export-plan.md` describe one change | Revise the existing file under its original path, because two plans for one change leave the executor guessing which is live |
| Asking what the repo knows | You ask which test runner the repo uses | Read `package.json` and the CI config in Step 0, because the repo answers faster and more exactly than the user |
| Test plan with no anchors | "Add unit tests for the new code" | Name the file, the Given/When/Then, and the requirement each test proves, because an unanchored test line cannot be handed off |
| Reused tests unnamed | The plan proposes 8 new tests beside 6 that already pass | Name the existing tests and what they already prove, so the user can see the real gap |
| Silent conflict | The plan follows the user and buries the mockup mismatch | Ask the Step 6 conflict question, because the losing side surfaces at review, after the work is done |
| Unmarked assumption | The plan states a requirement the user never gave | Mark every line CONFIRMED or ASSUMED, because an unmarked assumption reads as a user decision |
| Building inside the skill | You start editing source after the user approves the plan | Stop once the file lands, because execution belongs to `tdd`, a subagent, or the user |
| Interrogation | Nine questions about a two-file change | Cap at 7 and skip the themes the resources settle, because a long interview buys careless answers |

## Worked example

**Input:** "we need csv export on the orders screen, I think there's a mockup somewhere"

**Step 2, scan:** prints `image mockups/orders-export.png`, `spec docs/orders-api.md`, and
`plan docs/plans/reporting-plan.md`. One `AskUserQuestion` call asks which are
authoritative. The user marks the mockup and the API doc; the old reporting plan covers a
different change.

**Step 3:** reads both. The mockup shows an export button in the table toolbar and a column
picker in a dropdown. The user never mentioned a column picker.

**Step 4, one call, Scope theme:** three questions — does the export include the column
picker from the mockup, does it export the filtered rows or all rows, and what is the row
ceiling. Answers: yes, filtered rows, no ceiling stated.

**Step 5:** finds `tests/orders/table.test.ts` already proving the filter state, so the plan
reuses it for the filtered-rows requirement. Proposes four new tests, runner `vitest`, read
from `package.json`.

**Step 7:** drafts the plan for `plans/orders-csv-export-plan.md`. The row ceiling is marked
ASSUMED at 50,000 rows, with a note that a higher volume forces a streaming export.

**Step 8:** `ExitPlanMode` carrying the draft, the target path, the four new tests, and the
one assumption. The user approves, and the file lands at that path.
