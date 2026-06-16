# Session Review Checklist — what each signal means and how to fix it

This is the interpretation layer for `scripts/analyze_session.py`. The script
emits metrics and boolean `signals`; this file explains what each one indicates,
why it matters, and the concrete fix to recommend. Severity tags:

- **OBVIOUS** — well known, easy to spot, often still un-acted-on.
- **SUBTLE** — silent; the session still "works," just worse/slower/pricier.
- **RARELY-CONSIDERED** — high-impact and easy to miss.

Only raise a finding when the session actually shows the signal. Don't pad the
report with items that didn't fire. Lead with the highest-impact confirmed issues.

## Table of contents
1. Context management (peak context, history bloat)
2. Prompt cache health
3. Tool use and agent loops
4. Output and latency
5. Reasoning / extended thinking
6. Reliability
7. Compaction and long-running sessions
8. Cross-cutting: the one idea

---

## 1. Context management

**Signal: `high_peak_context` / `context_in_danger_zone`** (peak_context_size).
SUBTLE → RARELY-CONSIDERED. Model accuracy degrades as input grows, *well before*
the window is full — a 200k-window model can degrade around 50k tokens, and quality
drops hard above ~80% utilization. The decline is continuous, not a cliff, and it's
silent: the model keeps answering, just worse. This is the most common root cause of
"the model got dumber" — it's usually a context-management failure, not a model one.
- **Fix:** `/clear` between unrelated tasks; compact or summarize at checkpoints;
  push exploration into a forked subagent so its noise is discarded; for each block
  in context ask "would removing this change the output?" and cut if not. Target
  ~40–60% peak utilization.

**Lost in the middle.** SUBTLE. Even within a tolerable context size, content in the
*middle* is attended to worst (a U-shaped curve, with documented >30% accuracy drops
for mid-context info). Earliest instructions are followed most reliably (primacy).
- **Fix:** put the most important instructions/documents at the start or end, never
  buried mid-context. In a long session, re-state the live task near the end of the
  turn rather than relying on something said 30 turns ago.

**History bloat from accumulating tool results.** SUBTLE. In long agent loops, old
tool outputs, reasoning, and messages pile up and degrade every subsequent turn.
A large `tool_results` count combined with a high `assistant_turns` count is the tell.
- **Fix:** clear/compact tool results at checkpoints; paginate or filter tool output.

## 2. Prompt cache health

**Signal: `low_cache_hit`** (cache_hit_fraction, cache_miss_turns). RARELY-CONSIDERED,
high-impact. The cache prefix is built in a fixed order (tools → system → messages),
hashed byte-for-byte; any change early in the prompt invalidates everything downstream.
Cache reads cost ~10% of base input price and writes cost ~25% more — so a broken
cache silently multiplies cost and latency. A near-zero `cache_read` across turns that
share a prefix is the diagnostic.
- **Common causes to check for:** a live timestamp / request ID / session ID placed
  early in the system prompt; non-deterministic tool ordering (tools assembled from a
  dict/set that shuffles); mutating tool definitions or toggling thinking mid-session;
  adding/removing images mid-prefix.
- **Fix:** move all dynamic content *after* the cached prefix; serialize tools in a
  fixed sorted order and lock it with a unit test; hold the scaffold stable.

**Signal: `model_switching`** (models.switches). SUBTLE. Caches are model-scoped —
switching models mid-loop throws away the entire cache.
- **Fix:** keep the main loop on one model; spawn separate calls for cheaper sub-tasks
  rather than swapping the main loop's model. (A deliberate one-time switch can be
  fine; flag it so the user can confirm it was intentional.)

## 3. Tool use and agent loops

**Signal: `tool_sprawl`** (distinct_tools > ~15). RARELY-CONSIDERED. Past a threshold,
more tools degrade the model's ability to select *any* of them correctly — it picks
plausible-but-wrong tools silently.
- **Fix:** route to specialist sub-agents with small, coherent toolsets; use dynamic
  tool activation / tool-search so schemas are appended on demand instead of all loaded.

**Signal: `duplicate_tool_calls`** (duplicate_call_total, duplicated_tools).
SUBTLE. The same tool called with identical input more than once is wasted work — a
re-read of a file already in context, a repeated identical search. Each repeat burns a
turn and adds context.
- **Fix:** if it's a re-read of unchanged data, the info was already in context — the
  skill/harness should remind the model not to re-fetch. If it's repeated searches,
  prefer one targeted query; make tool error messages specific and actionable so the
  model doesn't retry blindly.

**Signal: `large_tool_outputs`** (tool_outputs_over_cap, largest_tool_output_chars).
SUBTLE. Outputs near or past the harness truncation limit (~25k tokens in Claude Code)
both bloat context and risk silently losing the tail.
- **Fix:** give tools sensible default limits, pagination, and an `--output` to a file
  for large results; return a summary by default rather than a full dump.

**Poor tool descriptions / ambiguous names.** SUBTLE (inferred from misselection or
errors, not directly measured). Overlapping descriptions cause silent misselection.
- **Fix:** crisp, differentiated descriptions; unambiguous parameter names (`user_id`
  not `user`).

## 4. Output and latency

**Output length dominates latency and cost.** RARELY-CONSIDERED. Output generation is
far slower per token than input prefill, so trimming output is the biggest speed lever.
A high `max_text_chars` / `mean_text_chars` (verbose narration, full data dumps) is the
tell.
- **Fix:** cap volume ("report at most five items," "keep approval messages terse");
  use the plan-validate-execute pattern — write a structured plan to a file, validate
  with a script, then execute, so reasoning lives on disk not in the token stream;
  demand structured output (JSON/CSV to stdout) and parse it instead of narrating.

## 5. Reasoning / extended thinking

**Signal: `heavy_thinking`** (thinking_blocks, approx_thinking_chars).
RARELY-CONSIDERED. Reasoning tokens bill as output and add seconds of latency; they
help genuine math/logic/code-design/debugging but not factual lookup or formatting.
Prior-turn thinking also accumulates as input in multi-turn flows.
- **Fix:** enable extended thinking only on hard reasoning routes; start at the minimum
  budget and raise incrementally (diminishing returns at high budgets). If heavy
  thinking appears on simple/mechanical turns, that budget is being wasted.

## 6. Reliability

**Signal: `tool_errors_present`** (tools.error_count). SUBTLE → OBVIOUS. Tool errors
that the loop recovers from are normal in small numbers; clusters indicate a brittle
tool interface or the model fighting an opaque failure.
- **Fix:** make tool errors say what went wrong, what was expected, and what to try;
  add exponential backoff with jitter for rate-limit errors; treat refusals/failed
  validations as first-class errors, not silent passes.

**Multi-turn drift.** RARELY-CONSIDERED (inferred from many turns + repeated rework).
Models lose substantial performance when a task is revealed across many turns versus
one consolidated prompt, and once they take a wrong turn early they tend not to recover.
- **Fix:** consolidate requirements before generation; add validation checkpoints; when
  feasible, re-state the full task in one turn rather than dribbling it out.

## 7. Compaction and long-running sessions

**Signal: `compaction_occurred`** (compaction.summary_lines). Informational, not a
fault by itself — but it means context was long enough to need summarizing, and that
nested CLAUDE.md / path-scoped rules are NOT auto-re-injected after compaction (only
the project-root CLAUDE.md survives). Conversation-only instructions are lost entirely.
- **Fix:** for very long tasks, use bridging artifacts (a progress file + git history)
  so a fresh context window can resume; add "when compacting, preserve…" notes to the
  root CLAUDE.md for anything critical; re-invoke a large skill after compaction if it
  was dropped.

## 8. Cross-cutting: the one idea

Every token carried on every turn competes for the same finite attention as the live
task. Minimizing what's resident isn't austerity — it's how you buy back the model's
intelligence. When in doubt, the fix is almost always *less context*, more
addressable-on-demand knowledge (see `references/harness-fixes.md`), and more
deterministic work pushed into scripts and hooks.
