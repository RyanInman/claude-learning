# Adversarial Review 2 — Report: Follow-the-sun on-call rotation plan

Artifact: `oncall-rotation-plan.md` · Charter: `charter.md` · Three fresh-eyes adversaries
(lenses: unhandled incidents, coverage/routing, goal-defeat/sustainability) plus a seam sweep.

## Verdict

As written, the plan fails its stated goal from day one: the two shift windows leave a
6-hour nightly hole (20:00–02:00 ET) with no owner, and every overnight-window Sev1 must
wake a US-based incident commander — so US-East keeps getting paged overnight by the plan's
own text, while the single success metric ("zero overnight pages") can go green anyway by
displacing pages into escalations, calls, and suppressed alerts. Two Critical findings are
structural contradictions, not operational risks.

Minimum-changes path (clears the top findings with 4 fixes):

1. Redefine the schedule in UTC to tile all 24 hours with a named owner per hour, deleting
   the "closest" rule — closes F1 and F7.
2. Reconcile the IC contradiction: train at least one Krakow IC before go-live, or amend the
   goal/metric to carve out and count IC pages — closes F2 and half of F6.
3. Extend the escalation policy two tiers within the on-duty region (primary → secondary →
   manager), and define a minimum-staffing fallback schedule for Krakow at fewer than 3
   available engineers — closes F4 and F5.
4. Gate go-live on verified readiness, not the calendar: each Krakow engineer acks a test
   page and executes one runbook against prod with real access — closes F3 and S2.

## Summary table

| Rank | ID | Title | Category | Severity | Status |
|------|----|-------|----------|----------|--------|
| 1 | F1 | 6-hour nightly coverage hole with undefined "closest" routing | Coverage gaps and mis-routed pages | Critical | Confirmed |
| 2 | F2 | All-US IC pool forces overnight US pages for every Krakow-window Sev1 | Plan defeats its own goal | Critical | Confirmed |
| 3 | F4 | Escalation chain is one hop into a sleeping engineer, then dead-ends | Incidents go unhandled | High | Confirmed |
| 4 | F5 | 3-person, 12-hour rotation collapses on the first absence | Krakow burnout or failure | High | Confirmed |
| 5 | F3 | Go-live is calendar-gated while Krakow prod access is incomplete | Incidents go unhandled | High | Plausible |
| 6 | F6 | Success metric can go green while every real failure mode worsens | Unverifiable success | Medium | Confirmed |
| 7 | S2 | Runbook and training handover has no acceptance criteria | Incidents go unhandled | Medium | Confirmed |
| 8 | S1 | No handover procedure for incidents in flight at a shift boundary | Coverage gaps and mis-routed pages | Medium | Confirmed |
| 9 | F7 | DST transitions silently grow the hole to 7 hours for ~4 weeks/year | Coverage gaps and mis-routed pages | Medium | Confirmed |
| 10 | S3 | No rollback or abort criteria if the rotation fails | Plan defeats its own goal | Low | Confirmed |

Ranking note: F1 outranks F2 because F1 fires on any incident in the hole, nightly and
unconditionally; F2 fires only on Sev1s. F5 sits above F3 because vacation and attrition are
certain events, while F3 hinges on an unverified fact (whether provisioning lands before
go-live).

## Findings

### Finding: 6-hour nightly coverage hole with undefined "closest" routing (F1)
- **Category:** Coverage gaps and mis-routed pages
- **Severity:** Critical — Confirmed
- **Corroboration:** Found independently by all three adversaries.
- **Failure scenario:** Winter time: Krakow's 08:00–20:00 CET is 07:00–19:00 UTC; US-East's
  08:00–20:00 ET is 13:00–01:00 UTC. From 01:00 to 07:00 UTC (20:00–02:00 ET, 02:00–08:00
  CET) neither shift is on duty — 6 hours every day, a quarter of the clock (the windows
  also overlap 13:00–19:00 UTC, so they sum to 24 local hours but only 18 distinct ones). A
  Sev1 fires at 04:00 UTC. The only routing rule is "page whichever shift is 'closest'": at
  04:00 UTC both shifts are exactly 3 hours away, so the rule has no answer, and PagerDuty
  cannot encode "closest" as a schedule. Whoever configures it picks: either an off-duty
  US engineer is paged overnight (defeating the goal — and for the first 3 hours of the hole,
  20:00–23:00 ET, US-East is unambiguously "closest", so the rule as written assigns US-East
  the overnight burden), or a Krakow engineer is woken pre-shift, or the schedule is left
  unassigned and the page fires into nobody, leaving the Sev1 unacked for up to 6 hours.
- **Root cause:** Plan step 1 leaves 6 of 24 hours uncovered and delegates routing to the
  undefined word "closest".
- **Suggested fix:** Replace step 1 with windows defined in UTC that tile the full 24 hours
  with an explicit owner for every hour, and delete the "closest" rule. If no region can
  honestly own the hole, say so in the plan and adjust the goal.

### Finding: All-US IC pool forces overnight US pages for every Krakow-window Sev1 (F2)
- **Category:** The plan defeats its own goal
- **Severity:** Critical — Confirmed
- **Corroboration:** Found independently by all three adversaries.
- **Failure scenario:** A Sev1 fires at 10:00 CET (04:00 ET), squarely inside Krakow's
  window. Step 5 requires an incident commander and the IC pool is entirely US-based,
  "as-is for now" — with no IC paging schedule defined at all. Either a US engineer is woken
  at 04:00 (the exact page the plan exists to eliminate), or the Krakow primary — 6 weeks in,
  never shipped to production — runs a Sev1 with no commander, no authority to coordinate
  other teams or approve risky mitigations, cold-calling US phone numbers. Second-order
  effect: because step 6 counts any US overnight page as failure, Krakow is structurally
  incentivized to under-classify Sev1s as Sev2 to protect the metric, so the highest-impact
  incidents get either an overnight US page or a downgraded severity — never a clean
  response. Krakow's window is 02:00–14:00 ET, so roughly half of it overlaps US night; the
  goal fails structurally, on the plan's own text, before any operational slippage.
- **Root cause:** Step 5 keeps the IC pool US-only with no paging path while step 6 declares
  success as zero US-East overnight pages; the plan never reconciles the contradiction.
- **Suggested fix:** Train and delegate IC authority to at least one Krakow engineer before
  go-live and put the IC pool on its own paging escalation — or amend the goal and metric to
  carve out IC pages as an accepted, separately counted number to drive down.

### Finding: Escalation chain is one hop into a sleeping engineer, then dead-ends (F4)
- **Category:** Incidents go unhandled or are mishandled
- **Severity:** High — Confirmed
- **Corroboration:** Found independently by two adversaries.
- **Failure scenario:** A page reaches the Krakow primary at 11:00 CET and gets no ack in 15
  minutes (sick, commuting, notification failure — with 3 engineers there is no secondary).
  Step 4 pages the other region's primary: a US engineer at 05:00 ET, asleep, who also
  misses it. The plan defines nothing after that — no second tier, no manager, no all-hands.
  Two missed pages, then silence; the incident is unowned indefinitely. The design guarantees
  the escalation target is off-shift, because follow-the-sun means the regions are awake at
  opposite times; during the F1 hole, both hops target sleeping engineers, so the chain is
  dead on arrival every night. With a 3-person bench, a missed first page is routine, not an
  edge case.
- **Root cause:** Step 4 defines exactly one escalation hop, its target is by construction
  outside their working window, and no tier exists past it.
- **Suggested fix:** Escalate within the on-duty region first (primary → secondary →
  engineering manager) with defined timeouts, and run ack-test drills so a full-chain
  failure still reaches a human who is awake.

### Finding: 3-person, 12-hour rotation collapses on the first absence (F5)
- **Category:** Krakow team burnout or failure
- **Severity:** High — Confirmed
- **Failure scenario:** Each Krakow engineer is primary one day in three, 12 hours per
  shift, year-round, with one week of shadowing as their total production exposure. One
  engineer takes two weeks of vacation (Polish statutory minimum exceeds 20 days) or
  resigns: the remaining two alternate 12-hour primary shifts every other day indefinitely.
  Within weeks they miss acks, and step 4's 15-minute escalation forwards their pages to the
  US primary — during US night for six of Krakow's twelve hours. The rotation degrades into
  a page-forwarding delay in front of the old US overnight rotation, adding 15 minutes to
  every incident, and the Notes rule out headcount relief this half.
- **Root cause:** Step 1 sizes Krakow's window by clock coverage, not sustainable rotation
  math for 3 people; no minimum-staffing threshold or degradation plan exists, and the Notes
  acknowledge zero headcount flexibility.
- **Suggested fix:** Define a minimum-staffing rule: below 3 available Krakow engineers, the
  rotation reverts to a declared interim schedule; gate go-live on 3 fully provisioned
  engineers plus a trained backup rather than a calendar date.

### Finding: Go-live is calendar-gated while Krakow prod access is incomplete (F3)
- **Category:** Incidents go unhandled or are mishandled
- **Severity:** High — Plausible (depends on whether provisioning completes and is verified
  before go-live; see Verification items)
- **Failure scenario:** Go-live day, 10:00 CET (04:00 ET). A Sev1 routes to the Krakow
  primary. Provisioning is still "in progress": no prod SSH, no dashboards, possibly not a
  valid PagerDuty target. The engineer either cannot ack, or acks and can only watch. The
  incident stalls until the 15-minute escalation wakes the sleeping US primary, who starts
  cold at 04:00. Minimum added Sev1 duration: 15+ minutes on every incident in the Krakow
  window until provisioning lands.
- **Root cause:** The Goal sets a hard calendar go-live ("starting next month") while the
  Notes line "Access provisioning ... is 'in progress'" is attached to no plan step; nothing
  gates the pager transfer on access being done.
- **Suggested fix:** Add a go-live gate: Krakow takes no live shift until each engineer has
  acked a test page and executed a runbook against prod with their own credentials.

### Finding: Success metric can go green while every real failure mode worsens (F6)
- **Category:** Unverifiable success
- **Severity:** Medium — Confirmed
- **Corroboration:** The under-classification incentive was independently raised by a second
  adversary under F2.
- **Failure scenario:** Month one ends with zero PagerDuty overnight pages to US-East.
  Meanwhile: Krakow acks within 15 minutes to stop escalation but cannot resolve, so
  incidents run long; US engineers are woken by Slack DMs, phone calls, and IC activations,
  none of which count as "pages"; noisy overnight alerts are silenced or downgraded to
  protect the metric. Leadership declares success and locks the decision in; the real cost
  surfaces a quarter later in Sev1 MTTR data. The metric measures page routing, not the goal
  (US engineers sleeping and incidents resolved), so it rewards displacement and suppression.
- **Root cause:** Step 6 defines success as a single absence-of-signal metric with no
  companion measure of incident outcomes, escalation count, or out-of-band contact.
- **Suggested fix:** Pair the page metric with two guardrails for the same month: overnight
  escalations/IC activations reaching US-East (counted, trending to zero) and Sev1 MTTR
  during Krakow hours (no regression vs baseline).

### Finding: Runbook and training handover has no acceptance criteria (S2 — seam sweep)
- **Category:** Incidents go unhandled or are mishandled
- **Severity:** Medium — Confirmed
- **Failure scenario:** Step 3 commits US-East to "tidy up" wiki runbooks with no owner,
  deadline, definition of done, or reader test; step 2 gives Krakow one week of shadowing —
  passive observation — as their entire training. Krakow's first solo week, a service they
  have never operated fails at 09:00 CET; the runbook assumes tribal knowledge (stale
  hostnames, links to US-only dashboards, "restart the usual way"). The engineer cannot
  execute it, escalates, and a sleeping US engineer resolves the incident from memory — the
  handover transferred the pager but not the capability, invisibly, until an incident tests
  it.
- **Root cause:** Steps 2–3: "tidy them up" and one shadow week are unverifiable handover
  criteria; no step requires a Krakow engineer to execute any runbook before go-live.
- **Suggested fix:** Make the gate executable: each critical runbook is run start-to-finish
  by a Krakow engineer (game-day or staging) before their first solo shift; a runbook that
  fails the dry run blocks that service's handover.

### Finding: No handover procedure for incidents in flight at a shift boundary (S1 — seam sweep)
- **Category:** Coverage gaps and mis-routed pages
- **Severity:** Medium — Confirmed
- **Failure scenario:** An incident starts at 19:40 ET, 20 minutes before the US shift ends.
  At 20:00 ET the US primary's shift is over; the plan defines no handoff call, no warm
  transfer, no rule for who owns an open incident crossing the boundary. Either the US
  engineer works into their night (an overtime pattern that erodes the goal) or drops it
  into the F1 hole where nobody is on duty. The same failure occurs daily at the 14:00 ET
  Krakow-to-US boundary for any incident open at that moment.
- **Root cause:** Steps 1–4 define shift windows and escalation but no shift handover:
  in-flight incident ownership at a boundary is unassigned.
- **Suggested fix:** Add one rule: an incident's current responder owns it until a named
  engineer on the incoming shift explicitly accepts it, plus a 15-minute overlap or written
  handoff at each boundary.

### Finding: DST transitions silently grow the hole to 7 hours for ~4 weeks a year (F7)
- **Category:** Coverage gaps and mis-routed pages
- **Severity:** Medium — Confirmed
- **Failure scenario:** The US springs forward the second Sunday of March; the EU not until
  the last Sunday. For those 2–3 weeks (and ~1 week from late October to early November) the
  CET–ET offset drops from 6 hours to 5. The nightly hole grows from 6 to 7 hours, and any
  rule encoded as fixed UTC times or the fixed mental mapping "20:00 ET = 02:00 CET" is
  wrong by an hour: pages route on stale arithmetic to a region that believes its shift has
  not started, and a handoff scheduled "at 20:00 ET / 02:00 CET" happens at two different
  moments. The plan never mentions DST, so nobody owns catching this before the first March.
- **Root cause:** Step 1 defines both windows in local time and does all gap reasoning
  implicitly, with no acknowledgment that the offset varies across the year.
- **Suggested fix:** Define shift boundaries in one reference zone (folded into the F1 fix)
  and add a calendar note naming the four DST transition dates with an owner who re-verifies
  coverage that week.

### Finding: No rollback or abort criteria if the rotation fails (S3 — seam sweep)
- **Category:** The plan defeats its own goal
- **Severity:** Low — Confirmed
- **Failure scenario:** Month one goes badly — long Sev1s, Krakow overwhelmed. Nothing in
  the plan defines what triggers reverting the pager to US-East, who decides, or what
  "badly" means, so the failing rotation persists by default while each incident relitigates
  the question. Reverting is mechanically cheap (US-East held the pager last month), which
  is why this is Low — but only if someone is empowered to pull the trigger.
- **Root cause:** The plan has a go-live and a success metric (step 6) but no abort
  criterion or named decision-maker for failure.
- **Suggested fix:** Add one line: "If [threshold, e.g. any Sev1 exceeds N hours unowned, or
  the week-2 review fails], [named role] reverts the pager to the prior US-East rotation."

## Killed findings

None. All twelve adversary findings survived verification; they merged into seven (see
corroboration notes). One numeric aside in an adversary scenario ("84 hours/week each
rotation") was ambiguous but not load-bearing and was dropped from the merged text.

## Verification items

- **F3:** The actual completion and verification date for Krakow's prod SSH, dashboard, and
  PagerDuty access, relative to the go-live date.
- **F1:** Whether a PagerDuty schedule has already been built for this plan, and how the
  configurer encoded the "closest" rule for 20:00–02:00 ET.
- **F5:** Krakow's known leave and travel plans for the first quarter of the rotation.

## Retest list

- **F1:** Revised schedule assigns a named, on-duty owner to every minute of a 24h UTC day,
  with no "closest" rule remaining — yes/no.
- **F2:** A Sev1 at 04:00 ET can obtain an incident commander without paging an off-duty
  US-East engineer, or the goal/metric explicitly carves out IC pages — yes/no.
- **F4:** An unacked page at 11:00 CET reaches an awake human through at least two further
  escalation tiers within the on-duty region — yes/no.
- **F5:** With one Krakow engineer absent for two weeks, the plan names the schedule that
  applies and it does not require the remaining two to alternate 12h shifts — yes/no.
- **F6:** Success is measured by at least one outcome metric (overnight escalations/IC
  activations to US-East, or Sev1 MTTR in Krakow hours) alongside the page count — yes/no.
- **S2:** Each critical runbook has been executed end-to-end by a Krakow engineer before
  that service's first solo shift — yes/no.
- **S1:** An incident open at 20:00 ET has a defined owner until explicit acceptance by the
  incoming shift — yes/no.
- **F7:** Shift boundaries are defined in one reference zone and the four DST transition
  dates have a named coverage-verification owner — yes/no.
- **S3:** The plan names an abort threshold and the role who reverts the pager — yes/no.

(F3 is Plausible pending its verification item; once access status is known, retest as: every
Krakow engineer acked a test page and ran a runbook with their own prod credentials before
their first solo shift — yes/no.)
