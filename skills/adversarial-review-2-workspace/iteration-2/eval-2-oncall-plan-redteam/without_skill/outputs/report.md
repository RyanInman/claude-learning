# Red-team review: follow-the-sun on-call rotation plan

Target: `oncall-rotation-plan.md`. Each finding states what breaks, how it breaks, and a severity grade.

Severity scale:
- **Critical** — plan fails its stated goal or leaves production unattended; will break in week 1.
- **High** — causes missed or botched incidents under realistic conditions; breaks within the first month.
- **Medium** — degrades response quality or sustainability; breaks over a quarter.
- **Low** — friction or ambiguity; annoying, survivable.

---

## Critical

### C1. The two shifts do not cover 24 hours — there is a 6-hour nightly hole

CET is 6 hours ahead of ET. Krakow's 08:00–20:00 CET is 02:00–14:00 ET. US covers 08:00–20:00 ET. Combined coverage is 02:00–20:00 ET.

**Nothing covers 20:00–02:00 ET.** That is US evening through 2am — historically a high-change, high-incident window (evening deploys, batch jobs, traffic peaks in western time zones). The plan's answer is to page "whichever shift is 'closest'", but:

- "Closest" is undefined and unimplementable. PagerDuty schedules need an explicit owner for every minute; there is no "closest" routing primitive. Whoever configures the schedule will make a silent decision the plan never made.
- Both candidate owners are off-shift and asleep or winding down. 20:00–02:00 ET is 02:00–08:00 CET — the middle of the Krakow night. Assigning it to Krakow gives them 3am pages; assigning it to US gives US overnight pages and **fails the plan's only success metric on day one**.

This is not an edge case. Follow-the-sun with two regions only 6 hours apart is arithmetically impossible with 12-hour shifts: 6 hours of double coverage (08:00–14:00 ET) and 6 hours of zero coverage. A true follow-the-sun needs a third region (~APAC) or 15–18-hour shifts. The plan cannot deliver its title with the teams it has.

**What actually breaks:** a Sev1 at 22:00 ET pages an alias with no defined human behind it, or a human 4 hours into sleep. Expect a missed or 30+ minute-late ack on the first bad night.

### C2. Krakow cannot operate production at go-live

Stack the plan's own notes:

- Joined 6 weeks ago, **never shipped to production**.
- Prod SSH, dashboards, and PagerDuty access are "in progress" with no completion date or gate.
- One week of shadowing, then live in under a month.

An engineer without prod SSH and dashboards cannot investigate anything; without PagerDuty access they cannot even receive the page. "In progress" access one month before go-live means the realistic outcome is engineers acking pages they cannot act on — which is worse than no coverage, because it silences escalation while nobody works the incident.

**What actually breaks:** Krakow primary acks a 10:00 CET Sev1, hits a login wall on the prod bastion, and burns the 15-minute escalation window plus more, because an acked page never re-escalates automatically. Time-to-mitigation doubles or worse on every non-trivial incident in the Krakow window.

**Missing gate:** go-live must be blocked on verified access (each Krakow engineer completes a live-fire drill: receive page, open dashboard, SSH to prod, run a runbook end-to-end). The plan has no gate at all.

### C3. Sev1s still wake up US engineers — the IC pool guarantees it

Every Sev1 requires an incident commander; the IC pool is entirely US-based and "stays as-is for now." A Sev1 at 10:00 CET is 04:00 ET. So every serious incident in the Krakow shift pages a sleeping US engineer anyway.

This contradicts the goal ("eliminate overnight pages for US-East") for exactly the incidents that matter most, and it makes the success metric ("zero overnight pages") either false or — worse — a perverse incentive: the way to hit the metric is to not declare Sev1s or not pull in an IC. A metric that rewards under-escalation during the highest-risk months of a new rotation is actively dangerous.

**What actually breaks:** either the metric fails in week 1, or Krakow runs its first real Sev1 without an IC, without prod tenure, and without US backup — and the incident review afterward asks why nobody escalated.

---

## High

### H1. A 3-person rotation is structurally unsustainable

Krakow's 3 engineers each carry 12-hour on-call every third day (or week-long primaries every third week), indefinitely, with:

- No secondary in-region (see H2).
- No slack for vacation, sickness, or attrition. One resignation or one two-week holiday makes it a 2-person rotation — 50% on-call load on a team six weeks into the job.
- No budget for headcount this half, so there is no relief valve.

Industry floor for a sustainable rotation is 4–6 people. Three is a burnout schedule, and burnout on a brand-new team shows up as attrition, which collapses the rotation entirely.

**What actually breaks:** within a quarter, expect degraded ack times, a resignation, or Krakow quietly handing pages back to US — any of which unwinds the whole plan.

### H2. The escalation path is a sleeping engineer in another country

If the primary misses a page for 15 minutes, the escalation target is the *other region's* primary — who is, by design, off-shift and mid-sleep (a 03:00 CET escalation for the US evening gap; a 04:00 ET escalation for a Krakow-morning miss). Problems:

- Escalation reintroduces the overnight pages the plan exists to eliminate, so responders are incentivized to sit on incidents rather than escalate (same perverse-metric dynamic as C3).
- There is no in-region secondary at all. A missed page goes straight from "one person" to "a person in the wrong time zone", skipping the cheapest fix (a second local responder).
- A sleeping cross-region primary has no context on the incident, the shift, or the ongoing changes.

**What actually breaks:** a missed 20:30 ET page escalates at 20:45 ET to a Krakow engineer at 02:45 local, who takes 10+ minutes to wake, log in (see C2), and orient. Realistic time-to-first-responder: 45–60 minutes on a Sev1.

### H3. "US will tidy up the runbooks" is an unowned, unverifiable dependency

No owner, no deadline, no definition of done, and no test that the runbooks work for their actual audience. Runbooks written by a team with years of tribal knowledge systematically omit the steps that team no longer notices (VPN quirks, which dashboard is stale, the unwritten "actually you restart it this other way"). Krakow — zero prod experience — is the worst-case audience for implicit knowledge.

**What actually breaks:** at 09:00 CET, a Krakow engineer follows a runbook that says "restart the ingest service" without saying how, where, or what healthy looks like afterward. The fix: gate go-live on Krakow running 3–5 game-day scenarios using only the runbooks, and fixing every gap found. The plan has no verification step.

### H4. One week of shadowing US daytime cannot prepare Krakow for its own shift

Two failures in one line item:

- **Duration.** One week of shadowing exposes a team to whatever incidents happen to occur that week — possibly none. For a team that has never touched prod, four weeks-plus of shadow, then reverse-shadow (Krakow drives, US supervises), is the defensible ramp.
- **Coverage mismatch.** Shadowing the US shift (08:00–20:00 ET) teaches US-business-hours incident classes. Krakow's shift (02:00–14:00 ET) is dominated by overnight batch failures, cron jobs, and early-morning traffic ramp — a different failure population they will never have seen.

**What actually breaks:** Krakow's first solo week hits an incident class no one shadowed, with runbooks that assume context they don't have (H3), and access that may not work (C2). These findings compound.

---

## Medium

### M1. The success metric measures routing, not outcomes

"Zero overnight pages for US-East within the first month" can be achieved by misconfiguring routing, suppressing alerts, or under-escalating — all of which make reliability worse while the metric turns green. It says nothing about whether incidents are handled. Missing counter-metrics: ack time by region, escalation rate, MTTR before/after cutover, missed-page count, Sev1 outcomes. Without them, the plan cannot detect its own failure.

### M2. No rollback criteria or fallback plan

Go-live is a one-way door as written. There is no threshold ("if Krakow misses N pages or MTTR degrades X% in the first two weeks, US resumes 24/7 while we fix the gaps") and no decision owner. New rotations usually wobble; a plan with no reversion path converts a wobble into a prolonged outage-response crisis.

### M3. Shift handover is undefined

Two handovers a day (08:00 ET / 14:00 ET boundaries) with no handoff ritual: no rule for who owns an incident that is open at the boundary, no written handoff of ongoing degradations, no overlap call. Cross-region handoffs without a protocol are where context dies; an incident straddling 20:00 CET gets a fresh responder with zero state.

### M4. DST transitions silently move the gap

The US and EU change clocks on different dates (US mid-March/early November; EU late March/late October). For roughly three weeks a year the offset drops to 5 hours, growing the nightly hole to 7 hours and shifting both shift boundaries relative to each other. Fixed local-time schedules with an undefined gap owner (C1) will misroute during exactly these weeks. Schedules should be defined in UTC or explicitly re-derived at each transition.

---

## Low

### L1. "CET" is ambiguous

The plan says CET; Krakow is on CEST from late March to late October. If someone configures tooling literally to CET (UTC+1) year-round, every boundary is off by an hour all summer. Write zone names as `Europe/Warsaw` and `America/New_York`.

### L2. "Starting next month" has no date or checklist

No cutover date, no owner, no ordered checklist (access verified → runbooks verified → shadow complete → schedule built → comms sent). Everything in C2/H3/H4 needs a gate; "next month" gives them nothing to gate on.

---

## Summary table

| # | Finding | Severity | What breaks |
|---|---------|----------|-------------|
| C1 | 6-hour nightly coverage hole; "closest" routing undefined | Critical | Unowned pages 20:00–02:00 ET; missed Sev1s at night |
| C2 | Krakow lacks prod access, prod experience, and a readiness gate | Critical | Acked-but-unworkable incidents; doubled MTTR in Krakow window |
| C3 | US-only IC pool means every Sev1 wakes US anyway | Critical | Goal/metric contradiction; incentive to under-escalate |
| H1 | 3-person rotation with no headcount relief | High | Burnout, attrition, rotation collapse within a quarter |
| H2 | Escalation target is a sleeping cross-region engineer; no local secondary | High | 45–60 min time-to-responder on missed pages |
| H3 | Runbook "tidy up" unowned and unverified | High | Runbooks fail their first real use by the new team |
| H4 | One week of shadowing, wrong shift's incident classes | High | Krakow solo against failures it has never seen |
| M1 | Metric rewards routing changes, not incident outcomes | Medium | Green dashboard over degrading reliability |
| M2 | No rollback criteria | Medium | Wobble becomes prolonged crisis |
| M3 | No handover protocol | Medium | Context loss on incidents straddling boundaries |
| M4 | DST transitions widen and shift the gap | Medium | Misrouted pages ~3 weeks/year |
| L1 | "CET" vs CEST/`Europe/Warsaw` | Low | Hour-off schedules if configured literally |
| L2 | No cutover date or checklist | Low | Nothing to gate go-live on |

## The shape of the fix

The plan's core arithmetic is broken: two regions 6 hours apart cannot follow the sun with 12-hour shifts. The honest options are (a) keep US on a thin overnight secondary for 20:00–02:00 ET and rename the goal "reduce" rather than "eliminate", (b) run asymmetric shifts (e.g., Krakow 06:00–20:00 CET, US 08:00–24:00 ET) and accept longer shifts, or (c) defer full cutover until a third region or more Krakow headcount exists. Whichever is chosen, gate go-live on: verified prod access per engineer, game-day-tested runbooks, 4+ weeks shadow plus reverse-shadow, an in-region secondary, at least one EU-timezone IC, outcome metrics alongside the page-count metric, and written rollback criteria.
