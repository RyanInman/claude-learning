# Red-team review: follow-the-sun on-call rotation plan

Source: `oncall-rotation-plan.md`. Each finding states what breaks, how it breaks, and a severity grade.

Severity scale:
- **Critical** — plan fails at go-live or during the first real incident; risk of extended outage.
- **High** — likely failure within the first month; degrades incident response materially.
- **Medium** — friction or slow burn; hurts the team but incidents still get handled.
- **Low** — cosmetic or fixable in flight.

---

## Critical

### C1. Coverage gaps are real, daily, and undefined
The two windows do not tile the clock. 08:00–20:00 CET is roughly 02:00–14:00 ET; 08:00–20:00 ET is roughly 14:00–02:00 CET. Overlap runs 08:00–14:00 ET; the uncovered gap runs 20:00 CET to 08:00 ET — about **02:00–08:00 CET / 20:00–02:00 ET**, six hours every single night. "Page whichever shift is closest" is not a routing rule PagerDuty can execute: "closest" is undefined at 05:00 CET (3 hours after Krakow ended, 3 hours before Krakow starts — and 11 hours into US off-hours). In practice this becomes an unconfigured schedule hole.

**What breaks:** a Sev1 at 04:00 CET pages nobody, or pages a sleeping engineer chosen by an ambiguous rule. First unhandled overnight Sev1 turns into a multi-hour outage.
**Also:** DST shifts differ (US and EU change on different weeks), so the gap size silently changes twice a year.

### C2. Krakow cannot actually respond: no prod access at handover
Access provisioning (prod SSH, dashboards, PagerDuty) is "in progress" with go-live "next month." If any of the three is missing at go-live, a Krakow primary who acks a page can do nothing but escalate. PagerDuty access specifically is a hard dependency — without it they cannot even *receive* pages, and the rotation is fictional from day one.

**What breaks:** pages route to Krakow, Krakow acks (or can't), then escalates back to US — the US engineer gets woken anyway, now 15+ minutes later than under the old rotation. The plan makes overnight response *slower*, not better.
**Gate:** access must be a verified go-live blocker, not a parallel workstream.

### C3. Sev1s have no incident commander for half the day
The IC pool is all US-based and "stays as-is." A Sev1 during Krakow's solo window (08:00–14:00 CET, before US comes online) requires waking a US IC at ~02:00–08:00 ET. That is exactly the overnight paging the plan claims to eliminate — it just relabels who gets paged. Worse: an IC woken cold, commanding responders they have never worked an incident with, over a team that has never shipped to production.

**What breaks:** Sev1 response during EU morning either runs IC-less (uncoordinated, comms chaos, no decision authority) or reintroduces overnight US pages, which by the plan's own success metric counts as failure.

---

## High

### H1. One week of shadowing for a team that has never deployed to production
The Krakow team joined six weeks ago and has zero production experience with this system. One week of shadowing — which at best covers whatever incidents happen to occur that week, possibly none — is the entire training plan. There is no reverse-shadow phase (Krakow primary, US backup watching), no incident simulation, no sign-off criteria.

**What breaks:** first real Krakow-handled incident, the primary doesn't know the system's failure modes, mis-triages, and either escalates everything (US overnight pages return) or worse, doesn't escalate when they should (extended outage).

### H2. 3-engineer rotation is below sustainable minimum
Krakow's 3 engineers each hold primary one week in three, indefinitely, covering 12-hour shifts. Industry floor for a sustainable rotation is 4–6. One person on vacation → 1-in-2. One resignation or sick leave → a single engineer on permanent call. A brand-new team hit immediately with a heavy pager is a retention risk; losing one of three collapses the whole model.

**What breaks:** within a quarter, burnout or a single departure forces US-East to re-absorb coverage — with no budget for headcount, per the notes.

### H3. Cross-region escalation pages someone asleep by design
"If primary doesn't ack in 15 minutes, page the other region's primary." Outside the overlap, the other region's primary is off-shift and likely asleep — that is the whole premise of follow-the-sun. There is no in-region secondary before the cross-region jump. A missed ack (bad cell coverage, commute) at 10:00 CET wakes a US engineer at 04:00 ET as the *first* escalation step.

**What breaks:** the escalation path guarantees the overnight pages the plan exists to eliminate, triggered by something as small as one missed ack. It also adds ~15 minutes of dead time before anyone capable responds.

### H4. Runbooks: "tidy them up" is not a deliverable
The runbooks are the only knowledge transfer artifact besides one shadow week, and the plan's treatment is a scare-quoted "tidy them up" with no owner, no completion criteria, no review by the people who will use them. Runbooks written by veterans for veterans typically assume tribal knowledge ("restart the usual way", "check the dashboard") that a 6-week-old team does not have. Nobody validates that a Krakow engineer can execute them cold.

**What breaks:** 03:00 ET incident, Krakow primary opens a runbook that says "fail over the DB per standard procedure," and the incident stalls. Untested runbooks fail exactly when they're needed.

---

## Medium

### M1. The success metric is trivially gameable and measures the wrong thing
"Zero overnight pages for US-East within the first month" can be achieved by misrouting pages, suppressing alerts, or Krakow silently absorbing incidents it can't handle. It measures *who got paged*, not *whether incidents were resolved well*. Nothing tracks MTTA/MTTR, escalation rate, or incident outcomes — so the plan can "succeed" while reliability degrades.

**What breaks:** the org declares victory at week 4 while time-to-resolution has doubled; the regression surfaces only at the next big outage.

### M2. No rollback or abort criteria
There is no condition under which the rotation reverts to US-only, no checkpoint review, and no definition of "this isn't working." Combined with M1, failure will be invisible until it is expensive.

### M3. Handover between regions is unspecified
Follow-the-sun lives or dies on shift handover: open incidents, degraded systems, in-flight changes. The plan says nothing about a handover ritual, a shared log, or what happens to an incident still open at 20:00 CET. An incident that straddles the boundary loses all context mid-stream.

### M4. Weekends and holidays are unaddressed
The plan describes weekday-shaped 12-hour windows and never mentions weekends, or the fact that US and Polish public holidays don't align (Polish holidays where the whole office is legally off, e.g. May 1–3, Aug 15). A US holiday Monday plus the standing nightly gap could leave 18+ unclear hours.

## Low

### L1. "Next month" go-live with three unfinished prerequisites
Access, runbooks, and shadowing are all incomplete, and the date appears fixed. Date-driven rather than readiness-driven launches ship the gaps. Cheap fix: gate go-live on a checklist (access verified by test page, runbooks executed cold by a Krakow engineer, shadow + reverse-shadow complete).

### L2. Timezone naming imprecision
"CET" and "ET" are ambiguous across DST (CET vs CEST, EST vs EDT). Schedules should be defined in the paging tool with proper tz identifiers (Europe/Warsaw, America/New_York), or the windows drift an hour twice a year.

---

## Bottom line

The plan as written does not achieve its own goal. The three Critical findings mean that at go-live: six hours a night have no defined owner (C1), the EU responders may be unable to act on what they receive (C2), and every EU-morning Sev1 still wakes a US engineer as IC (C3). The escalation design (H3) then reintroduces overnight US pages as the standard fallback path.

Minimum changes before go-live:
1. Redraw shifts so the two windows tile 24h (e.g. 12h/12h aligned back-to-back), defined in tz-aware tooling, with weekend/holiday coverage explicit.
2. Gate go-live on verified Krakow access: a successful test page acked and a prod runbook executed end-to-end by each Krakow engineer.
3. Add an in-region secondary before any cross-region escalation.
4. Train at least one Krakow engineer as IC, or accept and state that US ICs remain on overnight call (and stop claiming zero overnight pages).
5. Replace the success metric with resolution-quality measures (MTTA, MTTR, escalation rate) alongside the paging count, plus an explicit rollback trigger at a 2-week checkpoint.
