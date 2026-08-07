---
name: debate-review
description: >-
  Run a structured four-role debate review of an existing plan, design doc, code change, or
  proposal: a Defender explains it, a fresh-eyes Adversary attacks it, a fresh-eyes Advocate
  steelmans it, and a neutral Judge weighs both sides, brokers compromises, and hands the final
  recommendation to the user to decide. Use whenever the user wants a decision pressure-tested
  before committing — "debate review this plan", "red-team this design", "poke holes in this
  proposal", "play devil's advocate", "is this approach solid?", "argue both sides", or any ask
  for an adversarial or multi-perspective review of something that already exists. Do NOT use for
  routine line-by-line review of a diff (use a code-review skill) or when there is no artifact
  yet to defend — creating the plan comes first, debating it comes after.
---

# Debate Review

A single reviewer critiques with a single bias: too harsh, so everything looks wrong, or too
agreeable, so everything looks fine. This skill splits the review into four roles so attack,
defense, and judgment never come from the same head. It defines the *structure* of the review,
not the style — the same debate works on a migration plan, an architecture doc, a refactor
proposal, or a code change.

## Roles

| Role | Played by | Knows | Stance |
|------|-----------|-------|--------|
| **Defender** | Main agent (usually authored the artifact) | Full conversation context | Confident in the artifact but wants the best solution; explains decisions and defends them loosely, not dogmatically |
| **Adversary** | Fresh subagent | Artifact + transcript only | Believes the artifact is good but not yet best; hunts real problems and gaps, proposes better ways; changes mind only on convincing proof |
| **Advocate** | Fresh subagent | Artifact + transcript only | Steelmans the artifact; believes the Defender already has the best plan and errs toward keeping it; changes mind only on convincing proof |
| **Judge** | Fresh subagent | Artifact + transcript only | Neutral; weighs both sides, proposes compromises, writes the final report and recommendation. The user decides — the Judge only recommends |

The fresh-eyes constraint is the whole point: if the Adversary or Advocate inherits the
conversation history, they inherit the author's framing and the debate collapses into agreement.
Spawn them as subagents whose only inputs are their role brief, the artifact, and the transcript.
The main agent plays the Defender because it usually wrote the artifact and holds the context to
defend it. That same context is why the main agent never writes the Judge's sections.

## Setup

1. Identify the artifact: file paths for the plan, design doc, or code. If the proposal is inline, write it
   out to a file first, because every role must read the same fixed text.
2. Copy `assets/transcript-template.md` to `debate-review/transcript.md` next to the artifact.
   If that directory does not accept new files, put the transcript in the scratchpad. The
   transcript is append-only: each phase fills its own section, and it
   doubles as each role's memory between phases.
3. Read `references/roles.md` for the verbatim role briefs to paste into each subagent prompt.

## Phases

Run in order — each phase reads everything before it. Two phases run their agents in parallel:
phase 2's three question sets and phase 8's three reactions. Parallel agents return their
content in their replies instead of editing the transcript, because concurrent edits to one file
lose each other's writes. The Defender transcribes every returned set verbatim.

1. **Opening statement** — Defender explains the artifact's goal and each key decision's why. ≤400 words.
2. **Clarifying questions** — Adversary, Advocate, and Judge each submit up to 3 questions
   (questions only, no arguments yet). Defender answers all of them in one section.
3. **Adversary's case** — up to 5 objections. Each one: the problem, the evidence, and a proposed
   better way. Objections must pass the nitpick filter (see Gotchas).
4. **Advocate's case** — the steelman, plus a direct answer to each Adversary objection.
5. **Adversary's rebuttal** — respond to the Advocate. Explicitly drop any objection the
   Advocate answered convincingly, and say what convinced you.
6. **Advocate's surrebuttal** — final defense. Explicitly concede any point where the Adversary's
   proof holds, and say what convinced you.
7. **Judge's interim** *(conditional)* — per objection, the strengths and weaknesses of each side,
   then a concrete compromise proposal for every point still contested. Before spawning the Judge,
   the main agent checks phases 5–6: if every objection was dropped or conceded, skip phases 7–8
   and go straight to the final report, because there is nothing left to broker.
8. **Reactions to compromises** *(conditional, parallel)* — Advocate and Adversary each accept or
   reject every compromise, one reason apiece. The Defender adds the feasibility view: which
   compromises it would actually implement, which not, and why. The two subagents return their
   reactions in their replies; the Defender transcribes both, then writes its weigh-in.
9. **Judge's final report** — full report (format below) plus a recommendation. Present it to the
   user. The user decides. Never apply changes on the Judge's word alone.

Continuity: if the harness can message an existing agent, keep the same Adversary, Advocate, and
Judge agents across their phases. If not, respawn with the same role brief and the current
transcript — the transcript is the memory, so the debate continues either way.

## Final report format

The Judge's phase 9 brief in `references/roles.md` carries the full report format, because
the Judge writes the report from its role brief alone and never reads SKILL.md. The sections:
agreed changes, contested points, compromises and their fate, the Judge's recommendation, and
the user's decision options.

## Gotchas

- **Nitpick filter.** An Adversary objection must change an outcome — correctness, cost, risk, or
  maintainability. Style preferences and "I'd have done it differently" don't qualify. Five weak
  objections bury one strong one.
- **Proof, not rhetoric.** Roles change their mind on evidence — a counterexample, a benchmark, a
  failure scenario, a precedent — never on confident restatement. A concession must name the proof
  that earned it. Unearned agreement defeats the purpose of separated roles.
- **No context leakage.** Never paste conversation history into the Adversary, Advocate, or Judge
  prompts. Their value is what fresh eyes see.
- **Fixed rounds.** Exactly one rebuttal cycle (phases 5–6). If disagreement survives phase 6, it
  becomes a contested point for the Judge — not an extra round. Debates that loop don't converge,
  they exhaust.
- **Overkill check.** If the artifact is tiny or the decision is cheaply reversible, tell the user
  a full debate is more ceremony than the decision warrants. Offer a single-pass review instead.

## Example

User request:

> I wrote up a plan to migrate our auth from Redis sessions to JWTs, it's in jwt-migration-plan.md. Before I pitch it to the team I want it pressure-tested hard. Run a debate review on it and tell me what survives.

One Adversary objection from that run's transcript, verbatim. Phase 3 produced five, and every objection takes this shape:

> **Objection 4 — Single-release cutover whose only rollback is an untested redeploy is an avoidable gamble on the auth path of a 40k-DAU product.**
>
> - **Problem:** Auth middleware is the one component where a bad deploy takes down every request. The plan removes session middleware in the same release that introduces JWT middleware, with no feature flag; rollback is "redeploy previous release" — 15–30 min of full outage-or-degradation for all users, and that path is untested. The Defender classifies this as "a gap, not a deliberate accepted risk," i.e. the plan's author agrees it is unhandled.
> - **Evidence:** Defender's answer to Adversary Q2/Judge Q3: no feature flag, rollback untested, previous-release redeploy is the only path.
> - **Better way:** Not dual-stack-forever — a bounded transition inside the same two sprints. Ship one release where session middleware remains in the code behind a config flag while `/login` starts issuing JWTs and the JWT middleware runs first (fall through to session check). Rollback becomes a config flip (seconds, no redeploy), and the flag plus dead session code is deleted in a cleanup release once JWT auth has soaked for a week. Redis is still running until next quarter anyway, so keeping the session path warm for days costs nothing. Test the rollback flip in staging before cutover. This converts a 15–30 min untested rollback into a tested seconds-long one for roughly a day of work.

## Files

- `references/roles.md` — verbatim role briefs (subagent prompts) with placeholders to fill.
- `assets/transcript-template.md` — pre-structured transcript with all 9 phase sections.
