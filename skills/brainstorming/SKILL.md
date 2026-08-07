---
name: brainstorming
description: "Turns an idea into an approved design and implementation plan through one-question-at-a-time dialogue in plan mode, with an optional browser-based visual companion for mockups, diagrams, and side-by-side options. Use before any creative work - creating features, building components, adding functionality, or modifying behavior - whenever the user says \"let's build X\", \"add a feature\", or \"help me design/plan this\", even when the change seems too simple to plan. Do NOT use when an approved plan already exists (follow the plan) or to diagnose bugs."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and plans through natural collaborative dialogue.

Run this skill in plan mode. Enter plan mode with the EnterPlanMode tool before asking the first question. Plan mode blocks file edits until the user approves the plan, and that block is the gate this skill relies on.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design, then the plan. Get user approval through plan mode.

<HARD-GATE>
Do not write code, scaffold a project, or take any implementation action until the user approves the plan and you write the plan file. This applies to every project, because "simple" projects hide the most wrong assumptions.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short — a few sentences for a truly simple project. Present it and get approval every time.

## Checklist

Create a task for each of these items. Complete them in order:

1. **Enter plan mode** — use the EnterPlanMode tool if plan mode is not already active
2. **Explore project context** — check files, docs, recent commits
3. **Offer the visual companion just-in-time** — not upfront. The first time a question would be clearer shown than told, offer it in its own message. If the user approves, the companion's browser tab opens for them. If no visual question ever arises, never offer it. See the Visual Companion section below.
4. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
5. **Propose 2-3 approaches** — with trade-offs and your recommendation
6. **Present design** — in sections scaled to their complexity, get user approval after each section
7. **Draft the plan** — assemble the approved design and implementation steps (see Plan Document below)
8. **Plan self-review** — quick inline check for placeholders, contradictions, ambiguity, scope (see below)
9. **Present plan for approval** — use the ExitPlanMode tool. The user approves or requests changes
10. **Write plan file** — after approval, save to `docs/plans/<name>-plan.md` and commit

**The terminal state is the approved plan written to `docs/plans/<name>-plan.md`.** Do not invoke any implementation skill during brainstorming. Implementation starts only after you write the plan file, and it follows the plan.

## The Process

**Understanding the idea:**

- Explore the current project state first (files, docs, recent commits)
- Assess scope before asking detailed questions. If the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag that immediately. Don't spend questions refining a project that needs decomposition first.
- If the project is too large for a single plan, help the user decompose it into sub-projects. Ask: what are the independent pieces, how do they relate, and in what order does the user build them? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own plan → implementation cycle.
- For a project that fits a single plan, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Ask one question per message. If a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- YAGNI ruthlessly - remove unnecessary features from every approach and design

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into units that each have one clear purpose and communicate through well-defined interfaces. Make each unit understandable and testable on its own
- For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with. You reason better about code you can hold in context at once. Your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where an existing-code problem affects the work — a file grown too large, unclear boundaries, tangled responsibilities — include targeted improvements in the design. That is how a good developer improves code they work in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## Plan Document

After the user approves the design sections, assemble the plan. Cover:

- **Goal** — what the change accomplishes and how to tell it worked
- **Design** — chosen approach, alternatives considered, why
- **Implementation steps** — ordered, each with a verification check ("add parser → verify: unit test passes")
- **Testing** — how the work gets verified overall
- **Out of scope** — what this plan deliberately excludes

Scale detail to the work: a config change gets a few lines per section; a new subsystem gets the full treatment.

**Plan self-review:**
Before presenting the plan, look at it with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation pass, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix any issues inline. No need to re-review — fix and move on.

**Approval gate:**
Present the plan with the ExitPlanMode tool. Plan mode blocks file edits until the user approves, so this is the review gate — do not substitute a plain-text "does this look good?" message. If the user requests changes, revise the plan and present it again through ExitPlanMode.

**After approval:**

- Write the plan to `docs/plans/<name>-plan.md`, where `<name>` is a short kebab-case topic (e.g., `docs/plans/csv-export-plan.md`)
  - (User preferences for plan location override this default)
- Commit the plan file to git
- Follow the plan steps in order. Check each step's verification before you move on

## Visual Companion

A browser-based companion for showing mockups, diagrams, and visual options during brainstorming. Available as a tool — not a mode. When the user accepts the companion, it becomes available for questions that benefit from visual treatment. It does not mean every question goes through the browser.

**Offering the companion (just-in-time):** Do not offer it upfront. Wait until a question would genuinely be clearer shown than told — a real mockup, layout, or diagram question, not merely a UI *topic*. The first time that happens, offer it then, as its own message:
> "This next part might be easier if I show you — I can put together mockups, diagrams, and comparisons in a browser tab as we go. It's still new and can be token-intensive. Want me to? I'll open it for you."

**Send this offer as its own message.** Only the offer — no clarifying question, summary, or other content. Wait for the user's response. If they accept, start the server with `--open` so their browser opens to the first screen automatically. If they decline, continue text-only and don't offer again unless they raise it.

**Per-question decision:** Even after the user accepts, decide for each question whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**

- **Use the browser** for content that IS visual — mockups, wireframes, layout comparisons, architecture diagrams, side-by-side visual designs
- **Use the terminal** for content that is text — requirements questions, conceptual choices, tradeoff lists, A/B/C/D text options, scope decisions

A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is a conceptual question — use the terminal. "Which wizard layout works better?" is a visual question — use the browser.

If they accept the companion, read the detailed guide before proceeding:
`visual-companion.md`, next to this SKILL.md in the skill's own directory. Do not
resolve it against the working directory, because the skill can be installed
anywhere.

## Example

User: "let's build a little CLI that dedupes my photo library, shouldn't take long"

First response (after entering plan mode and exploring the project):

> Quick scope question before design: what counts as a duplicate? A) byte-identical files only, B) same image at different resolutions or formats, C) visually similar shots (burst photos, slight crops). This decides whether we need hashing only or image comparison.

The exchange continues one question at a time until the design is clear. The terminal state is an approved plan at `docs/plans/photo-dedupe-plan.md`. No code is written during this exchange.

## Gotchas

- Present the plan through ExitPlanMode, never as a plain-text "does this look good?" message, because only plan mode blocks file edits until the user approves.
- Do not skip the design for a "simple" project, because unexamined assumptions cost the most on projects that look trivial.
- A UI topic is not automatically a visual question. Ask conceptual questions in the terminal, because a mockup adds nothing to a text decision and costs tokens.
- Resolve `visual-companion.md` against the skill's own directory, not the working directory, because the skill can be installed anywhere.
