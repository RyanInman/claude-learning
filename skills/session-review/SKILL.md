---
name: session-review
description: Reviews a Claude Code session and produces a prioritized, graded list of instructional improvements covering context hygiene, prompt-cache health, tool use, output and reasoning budget, and harness setup (CLAUDE.md, skills, tool definitions, hooks). Works on a saved JSONL transcript (the files under ~/.claude/projects) or the currently active conversation. Use this whenever the user wants to review, audit, critique, or debug a Claude Code or LLM session, asks why a session got slow, expensive, or "dumber", wants to improve their CLAUDE.md or skills based on how a session went, shares or points to a .jsonl session file or transcript, or says things like "review this session", "analyze my session", "what went wrong in this run", or "how do I make my setup better". Also use proactively when a user shares a Claude Code transcript and asks what could be improved. Do NOT use to review a standalone SKILL.md in isolation (use the skill reviewer) or to write new application code.
---

# Session Review

Review a Claude Code session and hand the user a short, prioritized set of
instructional improvements — both how the *session itself* was conducted (context,
cache, tools, output, reasoning) and how their *harness* (CLAUDE.md, skills, tool
definitions, hooks) should change so the same problems don't recur.

The work splits cleanly: a script does the deterministic measuring, and you do the
judgment. Run the script, then interpret its `signals` against the checklist. Never
hand-count tokens or eyeball cache rates — that's what the script is for.

## Inputs and where the session lives

There are two inputs and two surfaces. Figure out which case you're in first.

**A saved JSONL transcript.** Claude Code writes each session to
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. If the user names a file, use it.
If they say "my latest session" or "the run I just did," run the script with `--latest`
to grab the newest one (or `--project-dir` to point at a specific project folder).

**The currently active session.**
- *In Claude Code:* the live session is itself a JSONL file. `--latest` usually finds it,
  but note it is mid-write, so the final turn may be incomplete — that's fine for a review.
- *In Claude.ai / Cowork:* there is no transcript file and no token/cache telemetry
  exposed. Review the conversation you can already see directly, and be honest that the
  metric-based findings (peak context, cache hit rate, exact token counts) can't be
  computed here. Focus on the conduct and harness items you *can* observe (tool sprawl,
  duplicated work, drifting requirements, output verbosity), and tell the user that for
  the full picture they can run the script on the JSONL in Claude Code.

## Workflow

### 1. Extract the metrics (when a JSONL file exists)

Run the analyzer. It is non-interactive, stdlib-only, and prints structured JSON:

```bash
python scripts/analyze_session.py PATH/TO/session.jsonl
# or, for the active/most-recent Claude Code session:
python scripts/analyze_session.py --latest
# add --format text for a quick human-readable summary, --full for the per-turn trajectory
```

Read the `signals` block first — each `true` flag is a confirmed thing to investigate.
Then use the supporting numbers (`tokens`, `cache`, `tools`, `compaction`, `output`,
`models`) as the evidence you'll cite in the report.

### 2. Gather live harness telemetry (Claude Code only, optional but valuable)

The JSONL captures the conversation, not the harness configuration. If the user is in
Claude Code and wants harness recommendations, ask them to share (or run) these — they
take seconds and reveal things the transcript can't:
- `/context` — what's eating the always-loaded budget before any work begins.
- `/doctor` — whether the skill-listing description budget is overflowing (a cause of
  skills silently not triggering).
- `/memory` — which CLAUDE.md and rules files are actually loaded.
- `wc -l CLAUDE.md` — memory-file size against the ~200-line guideline.

### 3. Interpret the signals

Read `references/review-checklist.md` and map every raised signal to its meaning, why it
matters, and the fix. Only write up signals that actually fired — don't pad with items
that didn't. Lead with the highest-impact confirmed issue (context rot and broken caching
usually outrank a couple of tool errors).

### 4. Turn findings into instructional changes

Read `references/harness-fixes.md` to decide *where* each durable fix belongs — a hook for
guarantees, a skill for procedures, CLAUDE.md for conventions, a path-scoped rule for
locality. The point of the review is not "try harder next time" but "change the harness so
this can't recur."

### 5. Write the graded report

Use the structure below. Keep it tight and prose-forward — a handful of findings that
matter, each with evidence and a concrete fix, beats an exhaustive checklist. This is
advice, so present it as the case for each change and let the user decide; don't manufacture
findings to fill the template.

## Report structure

Use this template:

```markdown
## Session review: <one-line characterization>

<2–4 sentences: the shape of the session from the metrics — length, peak context,
cache health, tool activity, anything that defines it.>

### Top findings (most impactful first)

**1. <Finding> — <OBVIOUS | SUBTLE | RARELY-CONSIDERED>**
- What I saw: <the specific metric/signal, with the number>
- Why it matters: <one or two sentences>
- Fix: <concrete change, ideally pointing at where it lives — hook / skill / CLAUDE.md / tool>

**2. ...**

### Harness recommendations

<Where the durable fixes belong: specific CLAUDE.md edits, a skill to create, a hook to
add, a tool description to tighten. Tie each back to a finding above.>

### Quick wins vs. deeper changes

<Optional: separate the one-minute fixes from the ones worth a dedicated session.>
```

Severity tags come from the checklist: OBVIOUS (well known, easy to spot), SUBTLE (silent
degradation), RARELY-CONSIDERED (high-impact and easy to miss).

## Gotchas

- **A clean report is a valid result.** If the script raises no flags and the conversation
  looks healthy, say so plainly and stop. Don't invent problems.
- **Compaction is not automatically a fault.** `compaction_occurred` just means the session
  got long enough to summarize; flag it only to note that nested CLAUDE.md / path-scoped
  rules aren't re-injected afterward.
- **A single model switch may be intentional.** Flag it as a cache cost, but let the user
  confirm whether it was deliberate before treating it as a defect.
- **Sidechain entries are subagent turns.** The script counts them separately
  (`sidechain_entries`); high subagent activity is usually good context hygiene, not a problem.
- **Thresholds are documented, not sacred.** The script's cutoffs (50k context, ~25k tool
  output, 15 tools, 50% cache hit) are reasoned defaults printed under `signals._thresholds`;
  treat a near-miss as "worth a look," not a hard verdict.
- **On Claude.ai there's no telemetry.** Don't fabricate token or cache numbers for a live
  chat — review what's observable and point to the JSONL path for the rest.

## Files

- `scripts/analyze_session.py` — parses a Claude Code JSONL transcript and emits metrics +
  signals. Run it; don't reimplement it.
- `references/review-checklist.md` — what each signal means, why it matters, and the fix
  (in-session conduct).
- `references/harness-fixes.md` — turning findings into CLAUDE.md / skill / hook / tool
  changes (the decision rule for where a fix belongs).
