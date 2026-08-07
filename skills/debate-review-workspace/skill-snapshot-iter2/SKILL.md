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
| **Adversary** | Fresh subagent per phase | Artifact + transcript only | Believes the artifact is good but not yet best; hunts real problems and gaps, proposes better ways; changes mind only on convincing proof |
| **Advocate** | Fresh subagent per phase | Artifact + transcript only | Steelmans the artifact; believes the Defender already has the best plan and errs toward keeping it; changes mind only on convincing proof |
| **Judge** | Fresh subagent | Artifact + transcript only | Neutral; weighs both sides, rules on each contested point or proposes a compromise, writes the final report and recommendation. The user decides — the Judge only recommends |

The fresh-eyes constraint is the whole point: if the Adversary or Advocate inherits the
conversation history, they inherit the author's framing and the debate collapses into agreement.
Every Adversary and Advocate appearance is a new subagent whose only inputs are its role brief,
the artifact, and the transcript — no agent carries private memory between phases. An agent that
survives across rounds starts defending its earlier words instead of the strongest position; a
fresh reader weighs only what is on the page. The main agent plays the Defender because it
usually wrote the artifact and holds the context to defend it. That same context is why the main
agent never writes the Judge's section.

## Setup

1. Run the overkill check before anything else: if the artifact is tiny or the decision is
   cheaply reversible, tell the user a full debate — seven subagents — is more ceremony than the
   decision warrants, and offer a single-pass review instead. Stop here if they agree.
2. Identify the artifact: file paths for the plan, design doc, or code. If the proposal is inline, write it
   out to a file first, because every role must read the same fixed text.
3. Copy `assets/transcript-template.md` to `debate-review/transcript.md` next to the artifact.
   If that directory does not accept new files, put the transcript in the scratchpad. The
   transcript is append-only: each phase fills its own section, and it is the only memory each
   fresh subagent gets.
4. Read `references/roles.md` for the verbatim role briefs to paste into each subagent prompt.

## Phases

Run in order. Phases 2, 4, and 5 each spawn a fresh Adversary–Advocate pair in parallel, in one
message. Subagents never edit the transcript — each returns its section in its reply, because
parallel edits to one file lose each other's writes. The Defender transcribes every returned
section verbatim before starting the next phase, because the next pair reads only the transcript.

1. **Opening statement** — Defender explains the artifact's goal and each key decision's why. ≤400 words.
2. **Clarifying questions** *(parallel pair)* — Adversary and Advocate each return up to 3
   questions about the case (questions only, no arguments yet).
3. **Defender's answers** — transcribe both question sets, then answer every question in one
   section. Facts and reasons, not advocacy — the debate proper starts in phase 4. Answer
   unknowns as "unknown" rather than stipulating plausible facts, because the Judge's rulings
   inherit every answer as evidence.
4. **Cases** *(parallel pair, fresh)* — a new Adversary returns up to 5 objections. Each one: the
   problem, the evidence, and a proposed better way; objections must pass the nitpick filter (see
   Gotchas). A new Advocate returns the steelman. Neither sees the other's case: the Advocate
   builds the affirmative case instead of guessing at objections — engagement comes in phase 5.
5. **Rebuttals** *(parallel pair, fresh)* — a new Adversary and a new Advocate each read both
   phase-4 cases and rebut the opposite role's points. Each also re-assesses its own side's case:
   sustain a point with new substance, or drop it and name the proof that convinced you.
6. **Judge's report** — a fresh Judge reads the artifact and the full transcript, then returns the
   final report (format below) plus a recommendation. Transcribe it and present it to the
   user. The user decides. Never apply changes on the Judge's word alone.

## Final report format

The Judge's brief in `references/roles.md` carries the full report format, because the Judge
writes the report from its role brief alone and never reads SKILL.md. The sections: agreed
changes, dropped objections, contested points, rulings, the Judge's recommendation, and the
user's decision options.

## Gotchas

- **Nitpick filter.** An Adversary objection must change an outcome — correctness, cost, risk, or
  maintainability. Style preferences and "I'd have done it differently" don't qualify. Five weak
  objections bury one strong one.
- **Proof, not rhetoric.** Roles change their mind on evidence — a counterexample, a benchmark, a
  failure scenario, a precedent — never on confident restatement. A concession must name the proof
  that earned it. Unearned agreement defeats the purpose of separated roles.
- **No context leakage.** Never paste conversation history into the Adversary, Advocate, or Judge
  prompts. Their value is what fresh eyes see.
- **Verbatim transcription.** Paste returned sections word for word. A summary injects the
  orchestrator's framing into the one document every fresh agent trusts as ground truth.
- **Fixed rounds.** Exactly one rebuttal phase. A point that survives both rebuttals becomes a
  contested point for the Judge — not an extra round. Debates that loop don't converge, they
  exhaust.

## Example

User request:

> I wrote up a plan to migrate our auth from Redis sessions to JWTs, it's in jwt-migration-plan.md. Before I pitch it to the team I want it pressure-tested hard. Run a debate review on it and tell me what survives.

One Adversary objection from that run's transcript, verbatim (the run predates the current phase numbering, so its cross-references differ). The case phase produced five, and every objection takes this shape:

> **Objection 4 — Single-release cutover whose only rollback is an untested redeploy is an avoidable gamble on the auth path of a 40k-DAU product.**
>
> - **Problem:** Auth middleware is the one component where a bad deploy takes down every request. The plan removes session middleware in the same release that introduces JWT middleware, with no feature flag; rollback is "redeploy previous release" — 15–30 min of full outage-or-degradation for all users, and that path is untested. The Defender classifies this as "a gap, not a deliberate accepted risk," i.e. the plan's author agrees it is unhandled.
> - **Evidence:** Defender's answer to Adversary Q2/Judge Q3: no feature flag, rollback untested, previous-release redeploy is the only path.
> - **Better way:** Not dual-stack-forever — a bounded transition inside the same two sprints. Ship one release where session middleware remains in the code behind a config flag while `/login` starts issuing JWTs and the JWT middleware runs first (fall through to session check). Rollback becomes a config flip (seconds, no redeploy), and the flag plus dead session code is deleted in a cleanup release once JWT auth has soaked for a week. Redis is still running until next quarter anyway, so keeping the session path warm for days costs nothing. Test the rollback flip in staging before cutover. This converts a 15–30 min untested rollback into a tested seconds-long one for roughly a day of work.

## Files

- `references/roles.md` — verbatim role briefs (subagent prompts) with placeholders to fill.
- `assets/transcript-template.md` — pre-structured transcript with all 6 phase sections.
