# Adversarial Review 2 — Report: Follow-the-sun on-call rotation plan

Artifact: `oncall-rotation-plan.md`. Charter: `charter.md`. Three fresh-eyes adversaries
attacked in parallel (lenses: unanswered/delayed pages; unready responder; Sev1 stalls,
metrics, and sustainability). Twelve raw findings merged to eight; none killed.

## Summary table

| ID | Title | Category | Severity | Status |
|----|-------|----------|----------|--------|
| F1 | Six hours per day (20:00–02:00 ET) have no on-shift responder and no defined routing target | Unanswered or delayed pages | High | Confirmed |
| F2 | Sev1 incidents during Krakow's shift stall waiting for a sleeping US incident commander | Sev1 response stalls | High | Confirmed |
| F3 | Go-live is gated by the calendar, not by access provisioning — Krakow may be unreachable or unable to act | Unanswered pages / unready responder | High | Confirmed |
| F4 | One shadow week for engineers with zero production experience produces responders who act wrongly, not just slowly | Incident mishandled by an unready responder | High | Plausible |
| F5 | A 3-person rotation covering 12h/7d collapses on the first vacation, sickness, or resignation | Rotation burns out or loses people | High | Confirmed |
| F6 | Escalation chain is two pages deep and dead-ends with the incident unacknowledged | Sev1 response stalls | Medium | Confirmed |
| F7 | The success metric reports success while incidents burn, and punishes correct escalation | Plan reports success while failing | Medium | Confirmed |
| F8 | "Tidy up" runbooks written for US veterans leaves Krakow executing docs full of unstated tribal knowledge | Incident mishandled by an unready responder | Medium | Plausible |

No finding graded Critical: every failure here is recoverable — the harms are extended
outages, mishandled incidents, and a rotation that collapses back to the pre-plan state, not
irreversible loss. F4's worst branch (wrong runbook choice destroys data) would be Critical
if verification item V1 confirms destructive runbook branches exist.

## Findings

### F1 — Finding: Six hours per day (20:00–02:00 ET) have no on-shift responder and no defined routing target
- **Category:** Unanswered or delayed pages
- **Severity:** High — Confirmed
- **Corroboration:** Two adversaries hit this independently; the second added that whichever
  team "closest" resolves to silently absorbs ~42 hours/week of overnight paging, invisible
  in the plan and (if routed to Krakow) invisible in the success metric.
- **Failure scenario:** A Sev1 fires at 22:30 ET on a Tuesday. Krakow's window (08:00–20:00
  CET) ended at 14:00 ET; US-East's window ended at 20:00 ET. The two windows (02:00–14:00 ET
  and 08:00–20:00 ET) leave 20:00–02:00 ET uncovered every day — this is not a
  "follow-the-sun" schedule, it is a schedule with a nightly 6-hour hole during US evening
  peak traffic. The plan's only rule for this hole is "page whichever shift is 'closest',"
  which no paging tool can execute: at 22:30 ET, is "closest" the US primary who went off
  shift 2.5 hours ago, or the Krakow primary asleep at 04:30 local? Whoever configures
  PagerDuty must invent an answer; either choice pages someone off-shift who has no
  obligation or expectation to respond. The page rings, nobody acks, the outage runs until
  02:00 ET at the earliest.
- **Root cause:** Plan step 1: the two 12-hour local windows are offset by only 6 hours,
  leaving an 18-hour combined span and a 6-hour daily gap, and "closest" is undefined — it is
  scare-quoted in the plan itself.
- **Suggested fix:** Redraw the schedule so the two windows sum to 24 hours (e.g., Krakow
  08:00–20:00 CET, US-East 14:00–02:00 ET), and replace "closest" with an explicit named
  owner for every hour of the week, verified by exporting the PagerDuty schedule and checking
  no hour resolves to zero targets.

### F2 — Finding: Sev1 incidents during Krakow's shift stall waiting for a sleeping US incident commander
- **Category:** Sev1 response stalls
- **Severity:** High — Confirmed
- **Corroboration:** Two adversaries hit this independently; the second stressed the pairing
  effect — the least-experienced engineer in the company is de facto commanding the
  highest-severity incidents during exactly the hours the IC pool is asleep.
- **Failure scenario:** A Sev1 fires at 10:00 CET (04:00 ET). The Krakow primary acks within
  15 minutes, so the escalation rule never fires — but the incident requires an IC, and the
  entire IC pool is US-based and asleep with no on-call IC schedule. The Krakow engineer
  (6 weeks tenure, never shipped to production, access "in progress") must either run the
  Sev1 alone or cold-call US engineers off-rotation. Command structure forms 30–60+ minutes
  late, exactly when the responder is least equipped. The highest-severity incidents get the
  slowest, least-coordinated response for roughly half of every day.
- **Root cause:** Plan step 5 keeps the IC pool all US-based "for now" with no overnight IC
  paging path, while steps 1–2 hand half the clock to Krakow. Nothing connects "Sev1 requires
  an IC" to "an IC is reachable during Krakow hours."
- **Suggested fix:** Before go-live, add an on-call IC to the pager schedule for Krakow's
  shift — either a paid US overnight IC rotation or a fast-tracked Krakow IC with an explicit
  US backup page at Sev1 declaration — and make "IC engaged within 15 minutes of Sev1
  declaration, 24/7" a go-live gate.

### F3 — Finding: Go-live is gated by the calendar, not by access provisioning — Krakow may be unreachable or unable to act
- **Category:** Unanswered pages / incident mishandled by an unready responder
- **Severity:** High — Confirmed
- **Corroboration:** Two adversaries hit the same root cause from different ends: one showed
  pages routing into a PagerDuty layer whose members have no accounts or untested contact
  methods (built-in 15+ minute delay on every EU-morning incident); the other showed the
  acked-but-helpless case below.
- **Failure scenario:** Go-live day arrives next month. A prod incident pages the Krakow
  primary at 10:00 CET. She acks within a minute, opens the runbook, and hits the first
  command: SSH to the affected host. Her prod SSH request is still queued in the
  "in progress" provisioning backlog; the dashboard link 403s; she isn't even in PagerDuty's
  responder tier for the service, so she was paged via a manual override. She spends
  40 minutes finding a US engineer awake at 04:00 ET to run commands for her, dictated over
  Slack. The outage runs 40+ minutes longer than under the old rotation, and the
  dictated-command pattern invites a wrong-host mistake.
- **Root cause:** Notes: access provisioning is "in progress," yet the Goal puts Krakow on
  primary "starting next month" with no provisioning-complete gate and no verification step.
- **Suggested fix:** Gate go-live on a verified per-engineer checklist: active PagerDuty
  account with a tested (live test page, acked) contact method, prod SSH, and dashboard
  access exercised end-to-end; slip the date until all three engineers pass.

### F4 — Finding: One shadow week for engineers with zero production experience produces responders who act wrongly, not just slowly
- **Category:** Incident mishandled by an unready responder
- **Severity:** High — Plausible (see verification item V1)
- **Failure scenario:** Week 3 post-go-live, a Krakow engineer with 7 total weeks at the
  company and zero production deploys faces a partial database failover alert. The runbook
  offers two branches; picking the wrong one (promoting a stale replica) converts a
  degraded-read incident into data loss. He has seen at most a handful of real incidents
  during his single shadow week — possibly zero, since a quiet shadow week teaches nothing —
  and there is no reverse-shadow phase where he drives while a US engineer watches. He picks
  the wrong branch. A Sev2 becomes a Sev1 with data damage.
- **Root cause:** Plan step 2 fixes training at one shadow week, while the Notes concede the
  team has never shipped to production; nothing guarantees the shadow week contains any
  incidents, and there is no supervised-primary phase.
- **Suggested fix:** Replace the single shadow week with a phased ramp: 2+ shadow rotations,
  at least two game-day incident simulations per engineer, then 2 weeks of
  Krakow-primary-with-US-secondary (reverse shadow) before solo coverage.

### F5 — Finding: A 3-person rotation covering 12h/7d collapses on the first vacation, sickness, or resignation
- **Category:** Rotation burns out or loses the people it depends on
- **Severity:** High — Confirmed
- **Corroboration:** Two adversaries hit this independently; one focused on the short-term
  absence case (one vacation plus one sick day leaves zero or one engineer, with no defined
  fallback), the other on the attrition spiral below.
- **Failure scenario:** Krakow's 3 engineers cover 08:00–20:00 CET daily: each is primary one
  week in three, 84 hours of pager duty per on-call week, indefinitely, with no secondary
  layer mentioned. One engineer takes a two-week vacation or gets sick: the rotation drops to
  1-in-2. One engineer quits (a 6-week-old team under this load is a plausible quitter, and
  "no budget for extra headcount this half" blocks backfill): the remaining two carry
  alternating 84-hour weeks until burnout or a second resignation, at which point Krakow
  coverage collapses and all pages revert overnight to US-East — the pre-plan state, now with
  an exhausted team and a leadership that believes the problem is solved.
- **Root cause:** The plan (Goal, step 1, Notes) staffs a permanent 12h/7d shift with
  3 people and no minimum-staffing threshold, secondary rotation, or degradation plan;
  industry floor for a sustainable single-site rotation is 4–6.
- **Suggested fix:** Set a go-live gate of at least 4 pageable Krakow engineers (or shrink
  Krakow's window until then), define a secondary/backup layer, and write the fallback
  schedule that activates when Krakow staffing drops below the threshold — with reverted
  hours recorded so the shortfall is visible rather than silent.

### F6 — Finding: Escalation chain is two pages deep and dead-ends with the incident unacknowledged
- **Category:** Sev1 response stalls
- **Severity:** Medium — Confirmed. Graded Medium rather than High because the dead-end
  mostly bites when the page first routes to someone off-shift — F1's coverage hole — and
  fixing F1 plus adding a secondary largely closes it; the failure needs two consecutive
  misses during covered hours and the fix is cheap.
- **Failure scenario:** At 04:00 CET a page routes to the Krakow primary (per whatever
  "closest" got configured). They are asleep off-shift and do not ack in 15 minutes. Step 4
  pages "the other region's primary" — the US primary at 22:00 ET, also off-shift, also
  possibly asleep or unreachable. The plan defines nothing after that: no in-region
  secondary, no manager escalation, no re-page loop. Two missed pages and the incident sits
  unacknowledged indefinitely. With 3 Krakow engineers and no secondary layer, a single sick
  day or flight makes the first miss near-certain.
- **Root cause:** Plan step 4 specifies exactly one escalation hop and no terminal fallback;
  the plan defines no secondary on-call in either region.
- **Suggested fix:** Add a secondary within each region as the first escalation hop, and a
  terminal step (engineering manager or IC pool, re-paged every 10 minutes until ack) so the
  chain cannot end with an open unacknowledged Sev1.

### F7 — Finding: The success metric reports success while incidents burn, and punishes the engineers who escalate correctly
- **Category:** The plan reports success while failing
- **Severity:** Medium — Confirmed. The perverse interaction is verifiable in the text:
  step 4's escalation pages US overnight, and step 6 counts any overnight US page as failure.
- **Failure scenario:** Month one: Krakow primaries ack every overnight page but, lacking
  prod SSH and with untested runbooks, cannot resolve several incidents. Per step 4, a no-ack
  escalates to the US primary overnight — which counts against the "zero overnight pages for
  US-East" metric. So Krakow engineers ack everything (stopping escalation) and struggle
  alone; MTTR doubles; two incidents that a US engineer would have fixed in 20 minutes run
  for hours. The metric reads zero overnight US pages. Leadership declares the rotation a
  success and cancels any fallback. The plan measures page routing, not incident outcomes,
  and its escalation path is the metric's failure condition — so the design pressures
  everyone to suppress the one safety valve it has.
- **Root cause:** Step 6 defines success as absence of pages to one team, with no MTTA/MTTR,
  incident-outcome, or escalation-count measure; combined with step 4, every legitimate
  overnight escalation makes the plan "fail."
- **Suggested fix:** Replace the metric with outcome measures — MTTA and MTTR for overnight
  incidents versus the prior 3-month baseline, plus escalation count reported as a health
  signal (expected nonzero early) — and state explicitly that escalating to US overnight is
  correct behavior, not a metric miss.

### F8 — Finding: "Tidy up" runbooks written for US veterans leaves Krakow executing docs full of unstated tribal knowledge
- **Category:** Incident mishandled by an unready responder
- **Severity:** Medium — Plausible (see verification item V2)
- **Failure scenario:** A Krakow engineer follows a wiki runbook that says "restart the
  ingestion service the usual way" and links a dashboard the US team knows to cross-check
  first. The unstated precondition (drain the queue before restart, or you drop in-flight
  events) lives only in US engineers' heads; the runbook was written as a memory aid for
  people who already knew the system. The restart drops events; downstream teams discover
  silent data gaps hours later. No one caught this because "tidy up" had no acceptance test —
  no naive reader ever executed the runbooks before go-live.
- **Root cause:** Plan step 3 makes runbook readiness a vague, unowned, unverifiable task
  ("tidy them up") with no completion criterion and no validation by the actual future
  audience.
- **Suggested fix:** Define runbook readiness as: for each alert routed to Krakow, a Krakow
  engineer executes the runbook end-to-end (in staging or a game day) without asking a US
  engineer anything; the runbook fails the gate until that succeeds.

## Killed findings

None. All twelve raw findings verified against the artifact; four were duplicates merged
into F1, F2, F3, and F5 (recorded as corroboration, not kills).

## Verification items

- **V1 (for F4):** Do the production runbooks contain destructive or branching procedures
  (failover promotion, data-mutating recovery steps) where a wrong choice is irreversible?
  If yes, F4's worst outcome is data loss and the finding upgrades to Critical.
- **V2 (for F8):** Current runbook state: can someone without platform-team tribal knowledge
  execute the critical runbooks end-to-end today? Sample two or three and have a non-author
  attempt them.
- **V3 (for F3):** Actual provisioning ETA for Krakow prod SSH, dashboards, and PagerDuty —
  "in progress" has no date; if completion is guaranteed well before go-live with verified
  test pages, F3's severity drops.

## Retest list

Re-run each scenario verbatim against the revised plan; a finding is fixed only when its
scenario no longer fails.

- **F1:** A Sev1 fires at 22:30 ET on a Tuesday. Krakow's window (08:00–20:00 CET) ended at
  14:00 ET; US-East's window ended at 20:00 ET. The two windows (02:00–14:00 ET and
  08:00–20:00 ET) leave 20:00–02:00 ET uncovered every day. The plan's only rule for this
  hole is "page whichever shift is 'closest'," which no paging tool can execute: at 22:30 ET,
  is "closest" the US primary who went off shift 2.5 hours ago, or the Krakow primary asleep
  at 04:30 local? Either choice pages someone off-shift with no obligation to respond; the
  page rings, nobody acks, the outage runs until 02:00 ET at the earliest. Check: does every
  hour of the week resolve to exactly one on-shift named owner?
- **F2:** A Sev1 fires at 10:00 CET (04:00 ET). The Krakow primary acks within 15 minutes,
  so the escalation rule never fires — but the incident requires an IC, and the entire IC
  pool is US-based and asleep with no on-call IC schedule. Check: is an IC engaged within
  15 minutes of Sev1 declaration at 04:00 ET without cold-calling an off-schedule US
  engineer?
- **F3:** Go-live day, 10:00 CET: a prod incident pages the Krakow primary. She acks and hits
  the runbook's first command: SSH to the affected host. Check: has every Krakow engineer,
  before taking a solo shift, demonstrated prod SSH, dashboard access, and an acked live
  PagerDuty test page?
- **F5:** Week 5: one Krakow engineer is on planned leave, another calls in sick Wednesday.
  Check: does a written rule name who covers 08:00–14:00 CET that Wednesday, and is the
  reverted coverage recorded rather than silent?
- **F6:** At 04:00 CET a page routes to the Krakow primary, who does not ack in 15 minutes;
  the other region's primary (22:00 ET, off-shift) also does not ack. Check: does a defined
  third step page someone until ack, so the chain cannot dead-end?
- **F7:** Month one: Krakow acks every overnight page but escalates three incidents to
  US-East overnight, correctly. Check: does the success metric count these escalations as
  healthy signal rather than failure, and does it track MTTA/MTTR against the prior
  3-month baseline?

Next step: decide which findings to fix; when fixes land, run Stage 5 (retest) against this
list — same inputs, same sequence.
