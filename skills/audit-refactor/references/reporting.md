# Phase 7 reporting — the three report files

Read this when writing the Phase 7 reports. The skill **always** writes all three files under
`reports/`, even on a clean run with nothing reverted — each serves a different reader, so the next
session (human or a follow-up `refactoring-from-audit` run) can pick up without re-deriving state.
If a section is empty, say so in the file rather than omit the file.

## Contents
- [File 1 — refactor-summary.md (issues addressed)](#file-1)
- [File 2 — refactor-followup.md (follow-up work remaining)](#file-2)
- [File 3 — <original-report-name>.updated.<yy-mm-dd>.md (audit updated in place)](#file-3)
- [Matching rule: by (file, title), never by row number](#matching-rule)

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

## File 3 — `reports/<original-report-name>.updated.<yy-mm-dd>.md` (the audit, updated in place) {#file-3}

Name the file with `updated` and the run date in `yy-mm-dd` form (`date "+%y-%m-%d"`, e.g.
`rule-adherence-high-medium.updated.26-07-01.md`), so successive continuation runs write distinct
files rather than overwriting the prior one. Copy the original report and **mark** every finding now
`applied` *and* confirmed — do **not** remove it. Two markers:

- **addressed** — a fix was applied and confirmed;
- **cleared** — the finding no longer applies (false positive, or made moot by another change).

Mark a finding by prefixing its summary-table **Issue** cell **and** its detail-block heading with a
bracketed tag: `[ADDRESSED]` or `[CLEARED]`. Keep the row and detail block otherwise intact, so the
file stays a valid, loadable report and the full history stays visible. `load_findings.py` detects
these tags and skips the finding, so a future run that loads this file sees only open work.

Stamp the current date/time at the top of the file on an `Updated: <YYYY-MM-DD HH:MM>` line (run
`date "+%Y-%m-%d %H:%M"` to get it), so each continuation run records when it last touched the audit.

Leave `reverted`/`skipped` findings **untagged** — they are still open work and must reload as open
findings next run.

## Matching rule: by `(file, title)`, never by row number {#matching-rule}

`load_findings.py` finding-ids (`f1..fN`) do **NOT** match the report's summary-table `#` column.
The id is assigned in load order; the `#` is the audit's ranking; they diverge (e.g. `f39` can be
table row 41). So:

- Find the row/block to tag by its `(file, issue)` cells — the **same key** in the summary table
  and the detail block. That tags both consistently.
- Acting by `int(#) == int(id[1:])` tags the wrong rows and leaves fixed findings untagged (they
  would reload as open work next run).
- After marking, verify **every** addressed/cleared finding carries its tag in **both** the table
  and its detail block, and no still-open finding was tagged by mistake.
