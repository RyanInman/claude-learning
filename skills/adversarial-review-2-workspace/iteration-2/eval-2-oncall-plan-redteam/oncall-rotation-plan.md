# Plan: Move to a follow-the-sun on-call rotation

## Goal
Eliminate overnight pages for the platform team (currently 6 engineers in US-East) by
splitting on-call between US-East and the new Krakow team (3 engineers) starting next month.

## Plan

1. Krakow covers 08:00-20:00 CET; US-East covers 08:00-20:00 ET. Gaps outside those windows
   page whichever shift is "closest".
2. Krakow engineers shadow US on-call for one week before go-live.
3. Runbooks live in the internal wiki; US team will "tidy them up" before handover.
4. Escalation: if the primary does not ack in 15 minutes, page the other region's primary.
5. Sev1 incidents require an incident commander; the current IC pool is all US-based, which
   stays as-is for now.
6. Success metric: zero overnight pages for US-East within the first month.

## Notes
- Krakow team joined 6 weeks ago and has not yet shipped to production.
- Access provisioning (prod SSH, dashboards, PagerDuty) is "in progress" for Krakow.
- No budget for extra headcount this half.
