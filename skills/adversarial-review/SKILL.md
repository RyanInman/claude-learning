---
name: adversarial-review
description: >-
  Run a lightweight fresh-eyes adversarial review of an existing plan, design doc, code
  change, or proposal: one independent subagent that has never seen the conversation attacks
  the artifact, scores every problem on real-world impact from 1 to 10, and the report raises
  only findings that score 8 or above - real problems, never nitpicks. Use whenever the user
  wants a fast second opinion that only flags what matters - "adversarial review this",
  "fresh eyes on this plan", "what would actually hurt here", "only tell me the big problems",
  "quick red-team, no nitpicks", "sanity check this before I commit", "is anything here a
  dealbreaker" - or when they want an outside perspective without a full debate or retest
  loop. Do NOT use when the user asks for a neutral judge or to argue both sides (use
  debate-review). Do NOT use for line-by-line diff review or when no artifact exists yet.
---

# Adversarial Review

A lightweight adversarial review: one fresh subagent, one impact score per finding, one
short report. The red-teaming literature agrees on four rules. NIST AI 600-1, OWASP, and
Microsoft's 100-product retrospective all state them. Start from downstream impact, not
attack technique.
Keep the subagent independent of the author. Make every finding reproducible. Grade
outcomes, not cleverness. This skill keeps those four rules and drops the ceremony.

The 8-of-10 floor is the whole design. A review that lists twelve problems teaches the user
to skim. A review that lists two problems, each worth real money or real rework, gets the
user to act.

## Workflow

### Step 0 - Intake

Collect three facts before you spawn the subagent. Mine the conversation first. Ask the user only
for what is missing. When you know all three, proceed without a pause.

1. **The artifact.** File paths for the plan, design doc, diff, or proposal. If the proposal
   is inline in the conversation, write it to a file first. The subagent must read fixed
   text, never the conversation.
2. **Downstream impact.** One or two sentences: who or what consumes this, and what happens
   when it fails. Impact lives downstream of the artifact, so the subagent cannot score
   without this.
3. **Out of scope.** Anything the user does not want judged: style, an unrelated system, or
   a decision already made. Without this, the subagent spends its findings on things the
   user cannot act on.

If the artifact is under about 30 lines or the decision is cheaply reversible, offer an
inline critique instead. If the user agrees, stop here.

### Step 1 - Attack

Spawn one fresh subagent. Give it only the brief below, the artifact path, and the three
intake facts. Never paste conversation history, the author's rationale, or a prior review.
A subagent that inherits the author's framing inherits the author's blind spots.

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
unverified. The band from 6 to 7 is where your verification most often moves a
score up or down.

### Step 2 - Verify and score

For each candidate the subagent returned:

1. **Verify against the artifact.** Re-read the cited section. Drop any finding that
   misreads the artifact or attacks something out of scope. Note each drop with its reason,
   because a report padded with false positives teaches the user to ignore it.
2. **Re-score on the same 1-to-10 rubric.** The subagent scored blind. You know the
   context and correct in both directions. A 6 that hits a constraint the subagent
   could not see becomes an 8. A 9 that assumes a fact the artifact rules out becomes a 4.
   Record the final score and, when it moved, one clause saying why. Lower a score only
   when the artifact text rules the scenario out. You share the author's context, so
   your instinct is to explain problems away. "It seems unlikely" is not a
   reason. A cited line is.
3. **Apply the floor.** Raise only findings with a final score of 8 or above. Put each
   finding scored 5 to 7 on one line at the end of the report. The user then sees it
   existed without reading it. Drop everything under 5.
4. **Mark certainty.** Tag each raised finding **Confirmed** or **Plausible**. Confirmed
   means the reasoning holds against the artifact alone. Plausible means it depends on a
   fact outside the artifact, and the report names that fact.

### Step 3 - Report

Write the report to `adversarial-review/report.md` next to the artifact. If that directory
rejects new files, write it to the scratchpad. Then present it inline. Use exactly this
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

If nothing survives at 8 or above, state that in the verdict. Keep the below-the-floor
line, because "nothing serious" is a finding the user paid for.

Present the report and stop. The user decides what to fix. Never apply fixes before the
user decides, because the review's product is evidence, not action. If the user asks to retest
after a fix, re-run each raised finding's failure scenario against the revised artifact.
Report each as fixed or still failing.

## Gotchas

- **The floor is the feature.** Do not raise a 7 "just so they know".
  Every sub-8 item in the raised list dilutes the ones that matter, and the below-the-floor
  line already preserves it.
- **Cleverness is not impact.** An ingenious multi-step bypass that yields a cosmetic
  glitch is a 3. Score the outcome, because the user pays for consequences, not technique.
- **No downstream impact, no review.** If the user cannot state what failure costs in
  Step 0, that gap is the first finding. The artifact's purpose is underspecified. Report
  that gap. Then stop.
- **No context leakage.** Keep conversation history out of the brief, because the
  subagent's value is that it never heard the author's reasoning.
- **Attack the system, not the text.** Real failures start at the boundaries the artifact
  assumes clean: the input, the operator, the dependency. A review confined to what the
  text says misses them.
- **Do not inflate to fill the report.** An empty raised list is a valid result, because
  the user paid to learn whether anything serious exists.

## Example

User request:

> fresh eyes on `docs/session-cache-design.md` before I open the PR - only the stuff that would actually hurt

One raised finding from that run, verbatim:

> ### Cache never invalidates on password change, so a revoked session stays valid for up to 24h
> - **Impact:** 9/10 - Confirmed - a user who changes their password after a credential leak stays logged in on the attacker's device for a full TTL
> - **Failure scenario:** Section 3 sets session TTL to 24h and Section 5 lists the only invalidation trigger as explicit logout. A user resets their password from a new device; the old session's cache entry is untouched. Any device holding the old session token keeps full access until the TTL expires.
> - **Root cause:** Section 5, "Invalidation", enumerates logout only. Password change and admin revoke are absent.
> - **Smallest fix:** Store a `credentials_version` on the user row, embed it in the cached session, and treat a mismatch as a miss.
