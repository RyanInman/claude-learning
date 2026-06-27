# Phase 7 reporting — the three report files

Read this when writing the Phase 7 reports. The skill **always** writes all three files under
`reports/`, even on a clean run with nothing reverted — each serves a different reader, so the next
session (human or a follow-up `refactoring-from-audit` run) can pick up without re-deriving state.
If a section is empty, say so in the file rather than omit the file.

## Contents
- [File 1 — refactor-summary.md (issues addressed)](#file-1)
- [File 2 — refactor-followup.md (follow-up work remaining)](#file-2)
- [File 3 — <original-report-name>.remaining.md (audit minus fixes)](#file-3)
- [Pruning rule: by (file, title), never by row number](#pruning-rule)

## File 1 — `reports/refactor-summary.md` (issues addressed) {#file-1}

The `render_refactor_report.py` output. Every finding marked `applied` (and confirmed in the
confirmation pass), with its file, shape, model, verify method, and PASS/FAIL verdict. This is the
record of what *this* session changed — the zero-regression verdict at the top is computed by the
script by diffing `final` against `baseline`.

## File 2 — `reports/refactor-followup.md` (follow-up work remaining) {#file-2}

Everything still owed, so the next run has an actionable backlog:

- findings `reverted` — with the failing test and why;
- findings `skipped`/`deferred` — with the reason (e.g. a high-tier opus queue the user declined,
  or untested behavior that needs a characterization test built first);
- any finding the confirmation pass flagged as **applied-but-not-holding**;
- report slices never attempted this run.

Give each a one-line next step — the model to use, the safeguard to build, or the decision needed —
so it's directly actionable rather than just a list of what's left.

## File 3 — `reports/<original-report-name>.remaining.md` (the audit minus what's fixed) {#file-3}

Copy the original report and remove every finding now `applied` *and* confirmed, preserving its
structure: prune both the summary-table rows **and** the detail blocks. Update counts/headers to
match. This is the input a future `refactoring-from-audit` run loads to continue where this one
stopped, so it must stay a valid report.

Leave `reverted`/`skipped` findings **in** — they are still open work.

## Pruning rule: by `(file, title)`, never by row number {#pruning-rule}

`load_findings.py` finding-ids (`f1..fN`) do **NOT** match the report's summary-table `#` column.
The id is assigned in load order; the `#` is the audit's ranking; they diverge (e.g. `f39` can be
table row 41). So:

- Match rows to remove by their `(file, issue)` cells — the **same key** used to prune the detail
  blocks. That keeps the table and the detail blocks consistent.
- Dropping rows by `int(#) == int(id[1:])` deletes the wrong rows and leaves fixed findings in the
  remaining report.
- After pruning, verify **zero fixed titles remain** in either the table or the detail blocks.
