# Red-Team Charter: Follow-the-sun on-call rotation plan

## Artifact and context

Under review: `oncall-rotation-plan.md` — a plan to split platform-team on-call between
US-East (6 engineers) and a new Krakow team (3 engineers), starting next month. The rotation
guards production for the platform team: when it fails, production incidents go unanswered or
badly handled, and customers and downstream teams eat the outage. The Krakow team is 6 weeks
old, has never shipped to production, and does not yet have full prod access.

## Harm categories, ranked

1. **Unanswered or delayed pages** — a production incident fires and no one capable
   acknowledges it in time; outage duration and customer impact grow.
2. **Incident mishandled by an unready responder** — the on-call acks but cannot act
   (missing access, missing knowledge, bad runbooks), turning a small incident into a large
   one or a wrong-fix into data damage.
3. **Sev1 response stalls** — incident-commander or escalation structure fails at the worst
   hour, so the highest-severity incidents get the slowest response.
4. **The plan reports success while failing** — the success metric or schedule design hides
   the failure, so leadership commits to a broken rotation.
5. **Rotation burns out or loses the people it depends on** — unsustainable load on the
   3-person Krakow team or hidden overnight load on US-East, causing attrition that collapses
   coverage.

## Out of scope

- Whether follow-the-sun is the right strategy versus alternatives (hiring, paying for
  overnight on-call) — the review attacks this plan, not the strategy choice.
- Compensation, legal, and employment policy for on-call in Poland.
- Wiki tooling and documentation style.

## Success criterion

A finding counts only if it would plausibly change a decision about the plan's correctness,
cost, risk, or maintainability — e.g., delay go-live, add a phase, change the schedule, or
change the success metric. Style preferences and hypotheticals with trivial downstream impact
do not count.
