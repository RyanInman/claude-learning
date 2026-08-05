---
name: report-render
description: Renders weekly metrics reports from JSON exports. Use when the user asks for a "weekly report", "render the metrics", or shares a metrics JSON export.
---

# Report Renderer

Render the weekly report from a metrics JSON export.

## Steps

1. Read the metrics JSON.
2. Render the report with the template in `references/formats.md`.
3. Write the report to `report.md`.

## Example

Input: "render the weekly report from metrics.json"
Output: `report.md` with a summary table and one chart per metric.
