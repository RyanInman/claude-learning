---
name: adversarial-review
description: >-
  Run a lightweight fresh-eyes adversarial review of an existing plan, design doc, code
  change, or proposal: one independent subagent that has never seen the conversation attacks
  the artifact, scores every problem on real-world impact from 1 to 10, and the report raises
  only findings that score 8 or above - real problems, never nitpicks. Use whenever the user
  wants a fast second opinion that only flags what matters - "adversarial review 3 this",
  "fresh eyes on this plan", "what would actually hurt here", "only tell me the big problems",
  "quick red-team, no nitpicks", "sanity check this before I commit", "is anything here a
  dealbreaker" - or when they want an outside perspective without a full debate or retest
  loop. Do NOT use for an attack with rebuttals (use adversarial-review), for three-lens
  coverage with charter and retest (use adversarial-review-2), or for a neutral judge (use
  debate-review). Do NOT use for line-by-line diff review or when no artifact exists yet.
---

# Adversarial Review

The lightest sibling of the adversarial-review family: one fresh subagent, one impact
score per finding, one short report. The published red-teaming literature (NIST AI 600-1,
OWASP, Microsoft's 100-product retrospective) agrees on what separates a real review from
security theater: start from downstream impact rather than attack technique, keep the
attacker independent of the author, make every finding reproducible, and grade outcomes
rather than cleverness. This skill keeps those four rules and drops the ceremony.

The 8-of-10 floor is the whole design. A review that lists twelve problems teaches the user
to skim; a review that lists two problems that would each cost real money or real rework
gets acted on.

## Workflow

### Step 0 - Intake

Collect three facts before spawning anything. Mine the conversation first. Ask the user only
for what is missing, and proceed silently when all three are known.

1. **The artifact.** File paths for the plan, design doc, diff, or proposal. If the proposal
   is inline in the conversation, write it to a file first, because the subagent must read
   fixed text and never the conversation.
2. **Downstream impact.** One or two sentences: who or what consumes this, and what happens
   when it fails. Impact lives downstream of the artifact, so the adversary cannot score
   without this.
3. **Out of scope.** Anything the user does not want judged (style, an unrelated system, a
   decision already made). Without this, the adversary spends its findings on things the
   user cannot act on.

Overkill check: if the artifact is under about 30 lines or the decision is cheaply
reversible, say so and offer an inline critique instead. Stop here if the user agrees.

### Step 1 - Attack

Spawn one fresh subagent. Give it only the brief below, the artifact path, and the three
intake facts. Never paste conversation history, the author's rationale, or a prior review,
because an adversary that inherits the author's framing inherits the author's blind spots.
Independence is the only thing that makes a second reader worth more than a second pass by
the first reader.

Fill `{ARTIFACT}`, `{IMPACT}`, and `{OUT_OF_SCOPE}` in this brief:

```
You are a fresh-eyes ADVERSARY reviewing an artifact you have never seen before. Read
{ARTIFACT}. Everything you know comes from that file and these two lines, deliberately:

Downstream impact if this fails: {IMPACT}
Out of scope: {OUT_OF_SCOPE}

Hunt for real problems: things that make the artifact fail its own goal, lose or corrupt
data, cost major rework, break something downstream, or leave nobody able to tell it is
failing. Attack the whole system the artifact describes - its inputs, integrations,
operators, and failure paths - not only the text, because simple attacks on the end-to-end
system succeed more often than clever attacks on one component.

Score every candidate on IMPACT from 1 to 10, using the worst plausible outcome of its
failure scenario:
  10  irreversible harm: data loss, security breach, users misled at scale, or the
      artifact fails its stated goal from day one
  8-9 core outcome fails or major rework is required; recovery is possible but costly
  5-7 degraded outcome or recurring friction; workarounds exist
  1-4 real but small; style, naming, "I would have done it differently"

Score the outcome, never the cleverness of the path to it. An elegant edge case with
trivial consequences is a 3. A blunt, obvious path to data loss is a 10.

Return every candidate that scores 6 or above, strongest first, each in exactly this format:

### <one-line title naming the harm>
- **Impact:** <score>/10 - <one clause naming the worst plausible outcome>
- **Failure scenario:** <concrete and reproducible: the specific inputs, state, or
  sequence, then what goes wrong, then the downstream consequence. A reader must be able
  to check this scenario against a revised artifact.>
- **Root cause:** <the weakness in the artifact that permits the scenario, cited by
  section, heading, or line>
- **Smallest fix:** <the minimum change that closes the root cause>

Return at most 6 candidates. If you find fewer real problems, return fewer; padding with
weak findings discredits the strong ones. If you find nothing at 6 or above, say so in one
line and stop. Return only the findings, no preamble, because your reply is merged
verbatim into a report.
```

Ask for 6-and-above rather than 8-and-above, because the subagent's calibration is
unverified. The band from 6 to 7 is where the main agent's verification most often moves a
score up or down.

### Step 2 - Verify and score

For each candidate the subagent returned:

1. **Verify against the artifact.** Re-read the cited section. Kill any finding that
   misreads the artifact or attacks something out of scope, and note the kill with its
   reason, because a report padded with false positives teaches the user to ignore it.
2. **Re-score on the same 1-to-10 rubric.** The subagent scored blind. The main agent knows
   the context and corrects for it in both directions: a 6 that hits a constraint the
   subagent could not see becomes an 8, and a 9 that assumes a fact the artifact rules out
   becomes a 4. Record the final score and, when it moved, one clause saying why. Lower a
   score only when the artifact text itself rules the scenario out, because the main agent
   authored or defended the artifact and its instinct is to explain problems away. "It
   seems unlikely" is not a reason; a cited line is.
3. **Apply the floor.** Raise only findings with a final score of 8 or above. Everything
   from 5 to 7 goes into one collapsed line at the end of the report so the user can see it
   existed without reading it. Everything under 5 is dropped.
4. **Mark certainty.** Tag each raised finding **Confirmed** (the reasoning holds against
   the artifact alone) or **Plausible** (it depends on a fact outside the artifact, and the
   report names that fact).

### Step 3 - Report

Write the report to `adversarial-review-3/report.md` next to the artifact (fall back to the
scratchpad if that directory rejects new files) and present it inline. Use exactly this
structure, because a fixed format makes run 50 comparable to run 1:

```
## Verdict
<One sentence: does the artifact achieve its stated goal as written, and what is the
single worst live problem. Then one sentence naming the smallest set of fixes that
clears every raised finding.>

## Raised findings (impact 8+)
<Each finding in the Step 1 format, plus final score, Confirmed/Plausible, and the
score-change note if any. Ranked by final score, no ties.>

## Below the floor
<One line per finding scored 5-7: title and score only.>

## Verification items
<One line per Plausible finding: the outside fact the user must check.>
```

If nothing survives at 8 or above, the verdict says so plainly and the report still lists
the below-the-floor line, because "nothing serious" is a finding the user paid for.

Present the report and stop. The user decides what to fix. Never apply fixes before they
rule, because the review's product is evidence, not action. If they ask to retest after a
fix, re-run each raised finding's failure scenario against the revised artifact and report
fixed or still failing.

## Gotchas

- **The floor is the feature.** The pull is to raise a 7 "just so they know". Resist it.
  Every sub-8 item in the raised list dilutes the ones that matter, and the below-the-floor
  line already preserves it.
- **Cleverness is not impact.** An ingenious multi-step bypass that yields a cosmetic
  glitch is a 3. Score the outcome.
- **No downstream impact, no review.** If Step 0 cannot state what failure costs, that gap
  is itself the first finding: the artifact's purpose is underspecified. Say so and stop.
- **No context leakage.** The subagent's value is that it did not write the artifact and
  did not hear the reasoning. Conversation history stays out of the brief.
- **Attack the system, not the text.** Real failures start at the boundaries the artifact
  assumes clean: the input, the operator, the dependency. A review confined to what the
  text says misses them.
- **Do not inflate to fill the report.** An empty raised list is a valid, valuable result.
  It is not a failure of the review.

## Example

User request:

> fresh eyes on `docs/session-cache-design.md` before I open the PR - only the stuff that would actually hurt

One raised finding from that run, verbatim:

> ### Cache never invalidates on password change, so a revoked session stays valid for up to 24h
> - **Impact:** 9/10 - Confirmed - a user who changes their password after a credential leak stays logged in on the attacker's device for a full TTL
> - **Failure scenario:** Section 3 sets session TTL to 24h and Section 5 lists the only invalidation trigger as explicit logout. A user resets their password from a new device; the old session's cache entry is untouched. Any device holding the old session token keeps full access until the TTL expires.
> - **Root cause:** Section 5, "Invalidation", enumerates logout only. Password change and admin revoke are absent.
> - **Smallest fix:** Store a `credentials_version` on the user row, embed it in the cached session, and treat a mismatch as a miss.
