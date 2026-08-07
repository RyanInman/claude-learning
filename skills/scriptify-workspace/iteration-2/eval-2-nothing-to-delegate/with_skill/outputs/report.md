# Delegation review — `well-delegated` (release-note-advisor)

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-2-nothing-to-delegate/with_skill/workspace/well-delegated/`

**Answer to the request: none. No part of this skill should become a new
script.** It is already a thin orchestrator — one exact script invocation
followed by the two things a script cannot do.

## Rendered report (verbatim from `render_report.py`)

## Delegation review: release-note-advisor

**Verdict:** 0 of 3 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~0 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Run exactly: `python3 scripts/check.py notes/ --json` to lint structure" (L10-11) | numbered-list | 35 | ALREADY_DELEGATED | step is already one exact invocation of scripts/check.py; script is mentioned in body, has argparse, --help works, exit codes documented 0/1/2 | - |
| s2 | "Read the findings JSON and decide which flagged items actually matter for" (L12-13) | numbered-list | 39 | CLAUDE | audience-fit call: whether a missing heading matters depends on who this release ships to; reasonable runs should differ. The mechanical shell (enumerate the candidates) is already scripted in s1 by check.py, so no HYBRID residue is left to strip | - |
| s3 | "Write a short, plainly-worded explanation for each item worth fixing, in" (L14-15) | numbered-list | 26 | CLAUDE | prose writing in the project's voice; no format spec exists in the skill for a lint script to check against, so a validator would invent a contract the skill never states | - |

## Reasoning per step

### s1 (L10-11) — ALREADY_DELEGATED

The step is one pinned command: `python3 scripts/check.py notes/ --json`, with
exit codes 0/1/2 stated inline. The inventory's interface audit passed on all
three signals it checks: `mentioned_in_body: true`, `has_argparse: true`,
`help_ok: true`. `scripts/check.py` also carries a header docstring with USAGE
and EXIT CODES, writes JSON to stdout, and is argv-only — the full
`references/script-conventions.md` shape. Nothing to add.

### s2 (L12-13) — CLAUDE

The named judgment: *whether a flagged item matters for this release's
audience*. The step's own prose supplies the example — "a missing heading on an
internal note may be fine". That is a call two reasonable runs should make
differently, given different releases, so a script here would encode one
arbitrary answer and wear false authority.

Per the rubric's tie-break, HYBRID was tried first and rejected. The HYBRID
shape for this step is extract-then-judge: a script enumerates the candidates,
Claude filters them. That script already exists and already runs — it is
`check.py` in s1, and its findings JSON is exactly the enumerated candidate
list this step consumes. The mechanical shell has already been stripped. What
remains is the judgment core alone, with no second script to insert between the
findings and the decision.

Pre-computing an audience signal (internal vs. external) was considered and
rejected. The skill states no rule for deriving audience from a note, so such a
script would guess and present the guess as fact.

### s3 (L14-15) — CLAUDE

Prose writing, in the project's voice, sized to each item. Judgment all the way
through.

The rubric notes that prose steps usually keep a script that lints the result —
required sections present, length within bounds, links resolve. It does not
apply here. The skill defines no format for these explanations: no required
sections, no length bound, no link requirement. A lint script would have to
invent a contract the skill never states, and then enforce it. That is the
"scripting judgment hides variance behind false authority" gotcha. The source
material a lint script would otherwise gather is, again, already gathered by
`check.py`.

## What this means

No script work follows. Steps 5-9 of the scriptify workflow (contract,
implement, smoke test, SKILL.md rewrite, wrap-up) do not run, because there are
no picked rows to implement. The target SKILL.md is unchanged — byte-identical
to the restore point taken at Step 0.

## Notes worth passing on

- `SKILL.md` is untracked in git (the whole workspace directory is untracked).
  Warned rather than blocked; a restore copy was taken at
  `scratch/.delegation-review/SKILL.md.orig` before any work, and nothing was
  written to the target.
- No DEAD steps found, so there is no `skillit:review` follow-up owed from this
  review. A general quality review of the target is still worth running
  separately if the user wants one — this review only answers the
  script-delegation question.
