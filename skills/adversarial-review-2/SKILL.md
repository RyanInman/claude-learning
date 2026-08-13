---
name: adversarial-review-2
description: >-
  Run a disciplined red-team review of an existing plan, design doc, code change, or proposal:
  write a short charter naming what failure would actually cost, attack the artifact with three
  parallel fresh-eyes adversaries assigned distinct lenses, verify and severity-grade every
  finding on outcomes, and re-test the exact failing scenarios after fixes land. Use whenever
  the user wants a rigorous, severity-graded attack — "adversarial review 2 this",
  "red-team this properly", "attack this and grade the findings", "what would actually break
  and how bad", "stress test this before we commit" — or when a prior review missed real
  problems and they want systematic coverage instead of cleverness. Do NOT use for a
  conversational back-and-forth attack with rebuttals (use adversarial-review) or when the
  user asks for a neutral judge or to argue both sides (use debate-review). Do NOT use for
  routine line-by-line diff review (use a code-review skill) or when no artifact exists yet —
  write the plan first, attack it after.
---

# Adversarial Review 2

Red-team discipline applied to artifact review. The published red-teaming literature (NIST,
OWASP, Microsoft's 100-product retrospective) converges on one lesson: a good adversarial
review is defined by discipline, not cleverness. Discipline means five things, and each is a
stage below: an explicit charter tied to real-world impact, diverse and independent attackers,
reproducible findings, outcome-based severity grading, and a closed remediate-and-retest loop.

This is the systematic sibling of `adversarial-review`: no debate, no rebuttals. Three
adversaries attack in parallel, the main agent verifies and grades, the user decides, and
fixed findings get re-tested.

## Workflow

### Step 0 — Intake

Collect these facts before starting. Mine the conversation first; ask the user only for what
is missing. If everything is known, proceed silently.

- The artifact: file paths for the plan, design doc, or code. If the proposal is inline,
  write it to a file first, because every adversary must read the same fixed text.
- The deployment context: who or what consumes this, and what happens downstream when it
  fails. Impact lives downstream, not in the artifact.
- Any known constraints invisible in the artifact: deadlines, past incidents, rejected
  alternatives.

Overkill check: if the artifact is tiny or the decision is cheaply reversible, say that four
subagents is more ceremony than the decision warrants, and offer an inline critique instead.
Stop here if the user agrees.

### Stage 1 — Charter

Write the charter to `adversarial-review-2/charter.md` next to the artifact (fall back to the
scratchpad if that directory rejects new files). The charter is the review's threat model: it
tells every adversary what failure costs, so findings anchor to impact instead of cleverness.
If you cannot fill the harm categories, stop and ask the user — attacking without a threat
model is the literature's most-cited failure mode.

The charter has four sections and fits on one page:

- **Artifact and context** — what is under review and where it runs or applies.
- **Harm categories, ranked** — 3 to 5 failure modes that matter, worked backward from
  downstream impact ("users see wrong prices", "on-call gets paged nightly", "migration is
  irreversible"). Not attack techniques — harms.
- **Out of scope** — what the review will not judge (style, unrelated systems), so
  adversaries do not spend findings there.
- **Success criterion** — what a finding must do to count: change a decision about
  correctness, cost, risk, or maintainability.

### Stage 2 — Attack

Spawn three fresh-eyes adversary subagents in parallel, each with a distinct lens taken from
the charter's ranked harm categories (assign the top three; merge or split categories so each
adversary owns one coherent lens). Distinct lenses are the point — three identical attackers
find the same three problems, three diverse ones cover the space.

Each adversary receives only the brief below, the artifact, and the charter. Never paste
conversation history, because an adversary that inherits the author's framing inherits the
author's blind spots — independence is what fresh eyes buy.

Fill `{ARTIFACT}`, `{CHARTER}`, and `{LENS}` in this brief:

```
You are an ADVERSARY in a red-team review. Read {ARTIFACT} and {CHARTER}. You have never seen
this artifact before — everything you know comes from those two files, deliberately.

Your lens: {LENS}. Attack the artifact through this lens only; other lenses have their own
adversaries. Attack the whole system the artifact describes — its integrations, inputs,
operators, and failure paths — not just the text in isolation, because simple attacks on the
end-to-end system succeed more often than clever attacks on one component.

Return up to 4 findings, strongest first, each in exactly this format:

### Finding: <one-line title naming the harm>
- **Category:** <harm category from the charter>
- **Failure scenario:** <concrete and reproducible: the specific inputs, state, or sequence,
  then what goes wrong, then the downstream impact. A reader must be able to re-run this
  scenario against a revised artifact and check whether it still fails.>
- **Root cause:** <the weakness in the artifact that permits the scenario, cited by
  section or line>
- **Suggested fix:** <the smallest change that closes the root cause>

The charter's success criterion is your filter: a finding must plausibly change a decision
about correctness, cost, risk, or maintainability. Style preferences and "I would have done
it differently" are noise that buries real findings. An elegant edge case with trivial impact
loses to a blunt problem with real impact — grade yourself on harm, not cleverness. If your
lens turns up fewer than 4 real findings, return fewer; padding discredits the rest.

Return only the findings, no preamble, because your reply is merged verbatim into the report.
```

### Stage 3 — Verify and grade

Merge the three replies. For each finding, in order:

1. **Verify against the artifact.** Re-read the cited section. Kill any finding that misreads
   the artifact or attacks something out of scope, and record the kill with its reason,
   because a report padded with false positives teaches the user to ignore it.
2. **Deduplicate.** Two adversaries hitting the same root cause is one finding with two
   scenarios — keep the stronger scenario, note the overlap as corroboration.
3. **Sweep the seams.** The lenses partition the space, and real gaps live between the
   partitions — every lens assumes some other lens owns the boundary. Check the artifact
   yourself against this five-item seam list, and add findings the adversaries missed:
   boundaries (time windows, size limits, edges of ownership), degradation (one person out,
   one dependency slow, one resource short), transitions (handover, cutover, in-flight work
   crossing a boundary), reversibility (rollback and abort criteria), and observability (how
   anyone would know the thing is failing).
4. **Grade severity** on the rubric below. Severity comes from the failure scenario's
   worst plausible outcome, never from how clever the attack is.

Severity rubric (outcome-based):

| Grade | Meaning |
|-------|---------|
| **Critical** | Harm you cannot walk back (data loss or corruption, security breach, irreversible migration, users harmed or misled at scale) — or the artifact fails its own stated goal from day one |
| **High** | The artifact's core outcome fails or costs major rework, but recovery is possible |
| **Medium** | Degraded outcome or recurring friction; workarounds exist |
| **Low** | Real but small impact; fix when next touching the area |

Then rank all findings in one strict total order — no ties, because the ranking is the
report's main signal and a flat band of six Highs carries none. Certainty weighs into rank:
a guaranteed, recurring failure outranks a conditional catastrophe that hinges on an
unverified fact, even when the conditional one holds the higher grade.

Mark each surviving finding **Confirmed** (you reproduced the reasoning against the artifact
and it holds) or **Plausible** (it depends on a fact outside the artifact — name that fact as
a verification item).

### Stage 4 — Report

Write the report to `adversarial-review-2/report.md` with exactly these sections, because a
fixed format makes run 50 comparable to run 1:

- `## Verdict` — first, because it is what a decision-maker acts on: one bottom-line
  sentence (does the artifact achieve its stated goal as written, and what class of harm is
  live), then the minimum-changes path — the smallest set of fixes that clears the top
  findings, collapsing findings that share a root cause into one fix.
- `## Summary table` — one row per finding in rank order: rank, ID, title, category,
  severity, Confirmed/Plausible.
- `## Findings` — rank order, each in the Stage 2 finding format plus its grade,
  Confirmed/Plausible status, and any corroboration note.
- `## Killed findings` — each killed finding's title and the reason, one line apiece.
- `## Verification items` — the outside-the-artifact facts that Plausible findings depend
  on, so the user can check them.
- `## Retest list` — one line per Confirmed finding: a single falsifiable check ("revised
  design invalidates on catalog price change within N seconds — yes/no"), not the scenario
  copied verbatim, because the findings section already holds the full scenarios and a
  duplicate doubles the report.

Present the report and stop. The user decides what to fix — never apply fixes before they
rule, because the review's job is evidence, not action.

### Stage 5 — Retest

When the user says fixes have landed, close the loop: run every check on the retest list
against the revised artifact (the full scenario behind each check lives in the findings
section). A fix is confirmed only by its original failing scenario passing, not by the diff
looking right, because that is the difference between a review and a snapshot. Also skim the
changed sections for regressions the fixes introduced. Report three lists: fixed, still
failing, new findings. New or still-failing items go back onto the retest list.

## Gotchas

- **No charter, no review.** Findings without a threat model anchor to what the adversary
  finds clever, not what failure costs. If harm categories will not come into focus, that
  itself is the first finding: the artifact's purpose is underspecified.
- **Cleverness is not severity.** The temptation is to grade an ingenious attack path High.
  Grade the outcome: an elegant bypass that yields trivial impact is Low; a blunt, obvious
  path to data loss is Critical.
- **Attack the system, not the text.** The artifact's weakest points are usually its
  boundaries — the inputs it assumes clean, the operator it assumes careful, the service it
  assumes up. A review confined to what the text says misses where real failures start.
- **Severity inflation — and its mirror.** A report that grades everything High teaches the
  user to trust nothing, so force the strict total rank. The mirror error: a report whose
  findings sum to "this fails on day one" but whose headline reads "no Critical findings"
  buries its own conclusion — that is what the plan-defeating clause in the Critical row is
  for. The verdict must say plainly what the findings collectively mean.
- **The retest is not optional ceremony.** A review without Stage 5 is a point-in-time
  snapshot: the literature's most common weak-review pattern. Offer the retest explicitly
  when presenting the report, and keep the retest list self-contained so a later session can
  run it cold.
- **No context leakage.** The adversaries' value is independence. Conversation history,
  the author's rationale, and prior review results all stay out of the adversary prompt.

## Example

User request:

> red-team queue-migration-plan.md properly before I take it to the team, I want severities on everything

One finding from that run's report, verbatim:

> ### Finding: Dual-write phase silently drops messages when the new broker rejects a publish
> - **Category:** Message loss during cutover
> - **Severity:** Critical — Confirmed
> - **Failure scenario:** During phase 2 (dual-write), the producer publishes to the old
>   broker, then to the new broker inside the same request handler. The plan's pseudocode
>   wraps only the second publish in try/except and logs the error. If the new broker is
>   unreachable for 10 minutes during business hours (the plan itself budgets for "brief
>   instability while the cluster warms"), every message in that window exists only on the
>   old broker — but phase 3 cuts consumers over to the new broker and phase 4 decommissions
>   the old one after "24h of clean dual-write metrics". The dropped messages are never
>   replayed and the metric that gates phase 4 does not count publish failures, so the gate
>   passes. Result: silent, permanent message loss discovered only when downstream
>   reconciliation runs at month-end.
> - **Root cause:** Section 4, "Dual-write", treats new-broker publish failure as a
>   log-and-continue event, and Section 6's cutover gate measures consumer lag, not publish
>   success ratio.
> - **Suggested fix:** Buffer failed new-broker publishes to a replay table keyed by message
>   ID, drain it before phase 3, and add publish-success-ratio ≥ 99.99% over 24h to the
>   phase 4 gate.
