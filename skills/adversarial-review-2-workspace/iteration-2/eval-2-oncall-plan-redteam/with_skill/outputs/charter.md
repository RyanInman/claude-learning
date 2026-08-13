# Red-Team Charter: Follow-the-sun on-call rotation plan

## Artifact and context

Under review: `oncall-rotation-plan.md` — a plan to split platform on-call between US-East
(6 engineers) and a new Krakow team (3 engineers), starting next month. The plan governs who
gets paged for production incidents, including Sev1s. Downstream consumers: every service the
platform team supports, the engineers being paged, and customers affected by incident
response speed. Failure downstream means incidents go unacknowledged, are handled by
engineers who lack access or context, or land back on US-East overnight — the exact harm the
plan exists to remove.

Known constraints: Krakow joined 6 weeks ago and has never shipped to production; access
provisioning is incomplete; no extra headcount this half; go-live is next month.

## Harm categories, ranked

1. **Incidents go unhandled or are mishandled** — a page fires and nobody with access,
   runbooks, or authority can resolve it; Sev1 duration and customer impact grow.
2. **Coverage gaps and mis-routed pages** — windows where no shift is on duty, ambiguous
   routing ("closest" shift), or escalation paths that wake the wrong region.
3. **The plan defeats its own goal** — US-East keeps getting paged overnight (as escalation
   target, IC pool, or de-facto fallback), so the stated goal fails while looking solved.
4. **Krakow team burnout or failure** — 3 engineers carrying a 12-hour daily window with no
   production experience; attrition or errors under load.
5. **Unverifiable success** — the metric declares victory while masking suppressed,
   swallowed, or displaced pages.

## Out of scope

- Whether hiring Krakow was the right decision, org structure, compensation.
- Tooling choices (PagerDuty vs alternatives), wiki platform, style of the document.
- Incidents unrelated to the platform team's services.

## Success criterion

A finding counts only if it would plausibly change a decision about correctness (does
coverage actually work), cost (rework, incident cost), risk (Sev1 outcomes, burnout), or
maintainability of the rotation. "I'd phrase it differently" does not count.
