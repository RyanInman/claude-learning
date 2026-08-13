# Notes and assumptions

- No live user, so I assumed the arch-review audience: findings are written to be defensible in review, each with a fix direction, not just a complaint.
- "A way to re-check them" is implemented as stable finding IDs (F-01..F-13) plus a pass-criterion table with an Open/Closed status column at the end of the report. Re-checking = asking a reviewer (or a future session) to verify each ID's criterion against the revised doc.
- I assumed the charge/confirm path is not described elsewhere; F-03 flags its absence rather than assuming it exists.
- Numbers in fix directions (timeouts, headroom fractions) are conventional starting points, not measured values; the pass criteria require the doc's own measured numbers.
- The `debate-review` skill matches "red-team this design", but the output directory is a `without_skill` baseline, so I performed the review directly without invoking it.
