---
name: adversarial-review
description: >-
  Run a lightweight two-role adversarial review of an existing plan, design doc, code change, or
  proposal: the main agent defends it while a fresh-eyes Adversary attacks it over three passes
  (questions, objections, rebuttal), and the Defender closes with a report that separates conceded
  fixes from contested points for the user to decide. Use whenever the user wants something
  attacked fast — "adversarial review this", "poke holes in this plan", "red-team this quickly",
  "attack my design", "devil's advocate pass", "what could go wrong with this?" — or when a full
  four-role debate is overkill. Do NOT use when the user asks for
  a neutral judge, an explicit steelman, or to "argue both sides" — use debate-review, which adds
  a fresh Advocate and Judge. Do NOT use for severity-graded findings or a retest
  loop — use adversarial-review-2. Do NOT use for routine line-by-line review of a diff (use a
  code-review skill) or when there is no artifact yet to defend — creating the plan comes first,
  attacking it comes after.
---

# Adversarial Review

The lightweight sibling of debate-review: attack only. Two roles instead of four — the Defender
absorbs the Advocate's steelman duty and the Judge's report duty, so only the Adversary keeps
fresh eyes. Three subagents instead of seven. The trade is explicit: the final report loses its
neutral author, so the report never rules on contested points — it states both sides and hands
the call to the user.

## Roles

| Role | Played by | Knows | Stance |
|------|-----------|-------|--------|
| **Defender** | Main agent (usually authored the artifact) | Full conversation context | Confident in the artifact but wants the best solution; defends with evidence, concedes on proof, and writes the final report |
| **Adversary** | Fresh subagent per phase | Artifact + transcript only | Believes the artifact is good but not yet best; hunts real problems and gaps, proposes better ways; changes mind only on convincing proof |

The fresh-eyes constraint is the whole point: if the Adversary inherits the conversation
history, it inherits the author's framing and the attack collapses into agreement. Every
Adversary appearance is a new subagent whose only inputs are its role brief, the artifact, and
the transcript — no agent carries private memory between phases. An agent that survives across
phases starts defending its earlier words instead of the strongest position; a fresh reader
weighs only what is on the page. The main agent plays the Defender because it usually wrote the
artifact and holds the context to defend it. When the artifact arrives as a file the main agent
did not author, the Defender still plays — speaking only from the artifact text and any real
context in the conversation. A gap the artifact leaves open is a finding to convert into a
verification item, not a hole to patch with invented facts.

## Setup

1. Run the overkill check first: if the artifact is tiny or the decision is cheaply reversible,
   tell the user that even this review — three subagents — is more ceremony than the decision
   warrants, and offer an inline critique instead. Stop here if they agree.
2. Identify the artifact: file paths for the plan, design doc, or code. If the proposal is
   inline, write it out to a file first, because both roles must read the same fixed text.
3. Copy `assets/transcript-template.md` to `adversarial-review/transcript.md` next to the
   artifact. If that directory does not accept new files, put the transcript in the scratchpad.
   The transcript is append-only: each phase fills its own section, and it is the only memory
   each fresh Adversary gets.

## Phases

Run in order. The Adversary brief and per-phase instructions are in the next section. The
Adversary never edits the transcript — it returns its section in its reply, and the Defender
transcribes it verbatim, because a single-author transcript keeps every section attributable
and lets the harness spawn the Adversary read-only.

1. **Opening statement** — Defender explains the artifact's goal and each key decision's why,
   including constraints invisible in the artifact (deadlines, past incidents, rejected
   alternatives). Flag the decisions you are least sure of. ≤400 words.
2. **Clarifying questions** — a fresh Adversary returns up to 3 questions about the case
   (questions only, no arguments yet).
3. **Defender's answers** — transcribe the questions, then answer every one. Facts and reasons,
   not advocacy — the attack starts in phase 4. Answer unknowns as "unknown" rather than
   stipulating plausible facts, because the final report inherits every answer as evidence.
4. **Objections** — a fresh Adversary returns its case against the artifact; objections must
   pass the nitpick filter (see Gotchas).
5. **Defense** — the Defender answers each objection directly: concede it, naming the proof that
   convinced you, or contest it by disputing the problem, the evidence, or the better way — and
   say which. This is where the Advocate's steelman duty lives: give the strongest honest case,
   including second-order reasons the artifact does not state. Restating the plan's virtues
   without answering the objection concedes it by default.
6. **Rebuttal** — a fresh Adversary reads the defense, then sustains or drops each objection.
7. **Final report** — the Defender writes the report (format below), transcribes it, and
   presents it to the user. The user decides. Never apply changes before the user rules on the
   contested points.

## Adversary brief

Paste this brief into each Adversary subagent prompt, filling `{ARTIFACT}`, `{TRANSCRIPT}`, and
`{PHASE}` from the per-phase instructions below.

```
You are the ADVERSARY in an adversarial review.

Read {ARTIFACT} and {TRANSCRIPT}. You have never seen this artifact before — everything you know
about it comes from those files, and that is deliberate.

Your stance: the artifact is good, but it is not yet the best version of itself. Your job is to
find real problems and gaps — the kind that change correctness, cost, risk, or maintainability.
For each one, propose a concretely better way. You are not a cynic. You want this to go from good
to great. If the Defender produces convincing proof — a counterexample, a benchmark, a failure
scenario, a precedent — you change your mind and say exactly what convinced you.

Never raise style preferences or "I would have done it differently" — an objection that doesn't
change an outcome is noise that buries your strong objections.

The Defender authored the artifact and also writes the final report, so your sustained
objections are the only counterweight in that report. Sustain only what the evidence backs — an
overclaimed objection discredits the rest.

{PHASE}

Return only your section's content, with headings at ### or deeper, because the transcript
reserves ## for phase headings. No meta commentary and no notes to the main agent — your reply
is pasted into the transcript as-is. Do not edit the transcript — the Defender is its only
author, which keeps every section attributable.
```

Per-phase instructions for `{PHASE}`:

- **Phase 2 (questions):** Write up to 3 clarifying questions about the Defender's opening case.
  Questions only — no arguments, no implied criticism. Ask what you will genuinely need to build
  your case against the artifact.
- **Phase 4 (objections):** Write your case: up to 5 objections. For each: **Problem** (what
  goes wrong), **Evidence** (why you believe it), **Better way** (your concrete alternative).
  Rank them, strongest first.
- **Phase 6 (rebuttal):** Read the Defender's defense. Two duties. First, re-assess each
  objection: sustain it with new substance, or drop it and state what in the defense convinced
  you. Dropping a weak objection strengthens your remaining ones. Second, challenge any defense
  point that overclaims or rests on weak evidence — with new substance, not repetition.

## Final report format

Write the report with exactly these sections, because a fixed format makes run 50 comparable to
run 1:

- `## Agreed changes` — objections the Defender conceded: changes ready to act on, each naming
  the proof that earned the concession.
- `## Dropped objections` — objections the Adversary dropped, and what answered each one. This
  is the record of why the artifact is fine as-is on those points.
- `## Contested points` — per point: the Adversary's final position and the Defender's, each
  stated fairly in its own words. No ruling — you wrote both the artifact and this report, so a
  ruling here would be the interested party judging its own case.
- `## Defender's recommendation` — one recommendation with reasoning, opening with a declared
  interest: you are the artifact's author and defender.
- `## Your decision` — the concrete options the user is choosing between.

Save the report as a standalone file too, keeping its `##` headings, because the report is the
deliverable the user reads outside the transcript.

## Gotchas

- **Nitpick filter.** An objection must change an outcome — correctness, cost, risk, or
  maintainability. Style preferences and "I'd have done it differently" don't qualify. Five weak
  objections bury one strong one.
- **Proof, not rhetoric.** Both roles change their mind on evidence — a counterexample, a
  benchmark, a failure scenario, a precedent — never on confident restatement. A concession must
  name the proof that earned it.
- **Concede honestly.** The Defender's temptation is to contest everything, because it wrote
  both the artifact and the report. The review's value is exactly the objections you cannot
  answer — a contested point that belongs in Agreed changes cheats the user who trusts the
  report.
- **No context leakage.** Never paste conversation history into the Adversary prompt. Its value
  is what fresh eyes see.
- **Verbatim transcription.** Paste returned sections word for word. A summary injects the
  Defender's framing into the one document every fresh Adversary trusts as ground truth.
  Verbatim binds the wording, not the packaging: drop wrapper lines addressed to you ("here is
  my section") and shift heading depth to nest under the transcript heading — never change the
  words inside.
- **Fixed rounds.** Exactly one rebuttal phase. An objection the Adversary sustains becomes a
  contested point in the report — not an extra round. Debates that loop don't converge, they
  exhaust.

## Example

User request:

> poke holes in cache-design.md for me before I start building it, I don't need a full debate, just attack it and tell me what actually needs fixing

One Adversary objection from that run's transcript, verbatim. The objections phase produced
five, and every objection takes this shape:

> ### Objection 1 — Per-worker cache incoherence turns every bulk import into a 15-minute window of user-visible data inconsistency, and the design has no mitigation.
>
> **Problem:** With 8 independent in-process caches (4 nodes × 2 workers) and no cross-worker invalidation, consecutive requests from the same user land on workers whose caches expire at different moments. After a nightly bulk import changes up to 30% of the catalog, a user can see a product's new price in one request and the old price in the next for up to 15 minutes. The design acknowledges staleness generally but never addresses *incoherence* — divergent answers to the same question at the same moment — which is what users actually notice and report as bugs.
>
> **Evidence:** The design states TTL is the only expiry mechanism, workers hold independent caches, and imports run nightly plus "ad-hoc during business hours." The Defender's answer to Q2 confirms there is no invalidation path and no import-completion signal today.
>
> **Better way:** Keep the in-process cache but add one narrow invalidation hook: have the import job POST to a `/cache/flush` admin endpoint on each node when it completes (the import runner already knows the node list from deploy config). Workers flush on receipt; cost is one small HTTP handler and one curl loop in the import script. This converts the worst-case window from 15 minutes of incoherence after every import to sub-second, while preserving every latency and simplicity benefit the design claims. TTL stays as the backstop for the ad-hoc edit path.

## Files

- `assets/transcript-template.md` — pre-structured transcript with all 7 phase sections.
