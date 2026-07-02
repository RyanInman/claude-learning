# Session Review Checklist — what each signal means and how to fix it

This is the interpretation layer for `scripts/analyze_session.py`. The script
emits metrics and boolean `signals`; this file explains what each one indicates,
why it matters, and the concrete fix to recommend. Severity tags:

- **OBVIOUS** — well known, easy to spot, often still un-acted-on.
- **SUBTLE** — silent; the session still "works," just worse/slower/pricier.
- **RARELY-CONSIDERED** — high-impact and easy to miss.

Only raise a finding when the session actually shows the signal. Don't pad the
report with items that didn't fire. Lead with the highest-impact confirmed
issues. Facts were verified against primary sources 2026-07-01; community
guidance is labeled as such.

## Table of contents
1. Context management (peak context, history bloat)
2. Prompt cache health
3. Tool use and agent loops
4. Output and latency
5. Reasoning effort
6. Reliability and multi-turn structure
7. Compaction and long-running sessions
8. Cross-cutting: the one idea

---

## 1. Context management

**Signal: `high_peak_context` / `context_in_danger_zone`** (peak_context_size,
peak_context_pct_of_window — computed against each turn's model window: 1M is
the default on Fable 5, Mythos, Opus 4.6+, Sonnet 4.6+; 200k otherwise).
SUBTLE → RARELY-CONSIDERED. "Context rot" is official Anthropic vocabulary now:
as tokens grow, recall accuracy degrades, well before the window is full, and
the decline is silent. Chroma's 18-model report found focused ~300-token
prompts significantly outperforming the same questions over full ~113k-token
contexts. Still the most common root cause of "the model got dumber."
- **Fix:** `/clear` between unrelated tasks — one session per task, not one
  session per project; push exploration into subagents so the noise is
  discarded; per block ask "would removing this change the output?" The
  40–60% peak-utilization band is community guidance (HumanLayer), not an
  official target — treat it as a heuristic.

**Lost in the middle.** SUBTLE. Mid-context content is attended worst
(U-shaped curve; Liu et al. measured mid-position multi-document QA falling
below even the no-documents baseline). Earliest instructions are followed most
reliably.
- **Fix:** put the most important instructions at the start or end; in long
  sessions, re-state the live task near the end of the turn (recitation)
  rather than relying on something said 30 turns ago.

**History bloat from accumulating tool results.** SUBTLE. Old tool outputs
degrade every later turn; large `tool_results` + high `assistant_turns` is the
tell. On newer models prior-turn *thinking* is also kept by default and bills
as input (see §5).
- **Fix:** clear/compact at checkpoints; paginate or filter tool output.
  Claude Code auto-compact clears older tool outputs first, but by the time it
  fires, quality has already been degrading — don't rely on it.

**The two-correction rule.** OBVIOUS, official, rarely followed. After two
failed corrections on the same issue, `/clear` and rewrite the original prompt
with what you learned — a clean session with a better prompt almost always
beats a long session with accumulated corrections.

## 2. Prompt cache health

**Signal: `low_cache_hit`** (cache_hit_fraction; classified evidence in
warm_cache_miss_turns vs miss_turns_after_ttl_gap). RARELY-CONSIDERED,
high-impact. Cache reads cost 0.1x base input; 5-minute-TTL writes 1.25x
(1-hour writes 2x). The prefix is hashed byte-for-byte in fixed order
(tools → system → messages); any early change invalidates everything after it.
- **Read the miss classification first.** The default TTL is 5 minutes,
  refreshed free on each use. A miss after an idle gap over 5 minutes
  (`miss_turns_after_ttl_gap`) is *expected* — the cache expired; that's idle
  cost, not a harness bug. Only `warm_cache_miss_turns` (gap ≤ 5 min) indicate
  real prefix instability.
- **Warm-miss causes to check:** a timestamp/request ID early in the system
  prompt; non-deterministic tool ordering; mutating tool definitions;
  toggling thinking *mode* mid-session (invalidates message-level cache only —
  tools and system survive); adding/removing images mid-prefix.
- **Fix:** move dynamic content after the cached prefix; serialize tools in a
  fixed sorted order; for loops with predictable idle gaps, the 1-hour TTL
  (2x write) often pays for itself on a large stable prefix
  (`cache_creation_by_ttl` shows the current split).

**Signal: `model_switching`** (models.switches). SUBTLE. Caches are
model-scoped — switching mid-loop rebuilds the cache from scratch. A
deliberate one-time switch can be fine; flag it so the user confirms intent.

**Fast mode** (models.fast_mode_turns). SUBTLE cost cliff. Fast mode (Opus
4.8: up to ~2.5x faster at 2x token price) repays the *entire conversation
context* at fast-mode uncached input price the first time it's enabled in a
conversation. Enable it from the start or not at all; unavailable on
Fable/Sonnet/Haiku.

## 3. Tool use and agent loops

**Signal: `tool_sprawl`** (distinct_tools > ~15). RARELY-CONSIDERED. Past a
threshold, more visible tools degrade selection of all of them. The 2026 fix
is deferral, not just pruning: Claude Code defers MCP tool schemas by default
(tool search — Anthropic measured ~85% token reduction with accuracy *gains*).
- **Fix:** verify tool search wasn't disabled (`ENABLE_TOOL_SEARCH=false` or
  forced-upfront loading); disable unused MCP servers via `/mcp`; prefer CLI
  tools (`gh`, `aws`, `gcloud`) over MCP servers — no per-tool listing cost;
  route specialist work to subagents with small toolsets.

**Signal: `duplicate_tool_calls`** (duplicate_call_total, duplicated_tools).
SUBTLE. The same tool called with identical input more than once is wasted
work — a re-read of a file already in context, a repeated identical search.
- **Fix:** if it's a re-read of unchanged data, the info was already in
  context — the harness should remind the model not to re-fetch. If it's
  repeated searches, prefer one targeted query; make tool errors specific and
  actionable so the model doesn't retry blindly.

**Signal: `large_tool_outputs`** (tool_outputs_over_cap,
largest_tool_output_chars). SUBTLE. Outputs near the ~25k-token truncation
cap bloat context and risk silently losing the tail.
- **Fix:** default limits, pagination, `--output` to a file; process bulk
  output in a script on disk and return a summary (Anthropic measured +11%
  accuracy with 24% fewer input tokens for code-orchestrated tool use); or a
  PostToolUse hook that condenses verbose output before it enters context.

**Poor tool descriptions / ambiguous names.** SUBTLE (inferred from
misselection, not directly measured). Overlapping descriptions cause silent
misselection.
- **Fix:** crisp, differentiated descriptions; unambiguous parameter names
  (`user_id` not `user`).

## 4. Output and latency

**Output length dominates latency.** RARELY-CONSIDERED. Decode is sequential;
latency is roughly linear in output tokens, while input prefill is
comparatively cheap. High mean/max_text_chars (narration, restated code, data
dumps) is the tell.
- **Fix:** cap volume ("report at most five items"); demand structured output
  and parse it; plan-validate-execute so reasoning lives on disk. Fable 5
  un-steered elaborates beyond the task, especially at higher effort — a short
  brevity instruction is as effective as listing every verbose pattern.

**Latency metrics** (latency block, from turn_duration entries). Long turns
are NOT inherently bad — autonomous runs legitimately take minutes. Interpret
with evidence: long turns + duplicate calls + low output = thrash; long turns
+ steady distinct tool progress = working as intended.

**The two speed levers to recommend:**
- **Effort** (`/effort`; low/medium/high/xhigh/max, default high). Lower
  effort makes the model combine tool calls, skip preamble, and answer
  tersely — it shapes *all* output, not just thinking. Skills and subagents
  can pin `effort:` in frontmatter. Effort is not recorded in the transcript —
  ask the user what it was set to.
- **Fast mode** (`/fast`) for interactive iteration on Opus — see the §2 cache
  caveat. Also: parallel tool calls, and Haiku-routed subagents for
  mechanical fan-out.

## 5. Reasoning effort

**Signal: `heavy_thinking`** (thinking_blocks, approx_thinking_chars).
RARELY-CONSIDERED. Reasoning tokens bill as output and add latency. The
control surface changed in 2026: effort levels replaced thinking budgets —
`budget_tokens` is deprecated on newer models, adaptive-thinking models ignore
`MAX_THINKING_TOKENS`, and thinking cannot be disabled on Fable 5.
`ultrathink` in a prompt is the only remaining deep-reasoning keyword ("think
hard" does nothing now).
- **Fix:** heavy thinking on mechanical turns → lower session effort, or pin
  `effort: low` on the mechanical skill/subagent. On newer models prior-turn
  thinking blocks are kept by default and bill as input on every later turn —
  in very long sessions that compounds; a fresh session (or API context
  editing) clears it.

## 6. Reliability and multi-turn structure

**Signal: `tool_errors_present`** (tools.error_count). SUBTLE → OBVIOUS.
Recovered errors are normal in small numbers; clusters mean a brittle tool
interface or the model fighting an opaque failure.
- **Fix:** errors should say what went wrong, what was expected, what to try;
  backoff with jitter for rate limits. Counterpoint: keep errors in context
  *while actively debugging* — erasing failures removes the evidence the model
  adapts from (Manus); clean them at task boundaries.

**Multi-turn drift.** RARELY-CONSIDERED, now measured: across 200k+ simulated
conversations, models averaged a 39% drop when requirements arrived over many
turns vs one consolidated prompt — driven by premature answers and
over-anchoring on their own early wrong output (arXiv 2505.06120, ICLR 2026).
- **Fix:** consolidate requirements before generation; re-state the full task
  when correcting; after two failed corrections apply the two-correction rule
  (§1).

## 7. Compaction and long-running sessions

**Signal: `compaction_occurred`** (compaction.summary_lines). Informational,
not a fault. What survives is precisely documented: project-root CLAUDE.md,
unscoped rules, and auto memory are re-injected from disk; path-scoped rules
and nested CLAUDE.md are lost until a matching file is read again; invoked
skill bodies are re-injected capped at 5,000 tokens per skill / 25,000 total,
oldest dropped first; the skill *listing* is not re-injected. Auto-compact
clears older tool outputs first, then summarizes, and gives up after a few
attempts if one giant file keeps refilling context.
- **Fix:** bridging artifacts (spec/progress file + git history) so a fresh
  session can resume — now official guidance; a "Compact Instructions" section
  in CLAUDE.md or `/compact <focus>` to steer what survives; re-invoke a large
  skill after compaction if its body was dropped.
- **When recommending rewrites of memory files or summaries,** prefer
  incremental delta edits over full rewrites: iterative summarization erodes
  detail ("brevity bias") and monolithic rewrites destroy accumulated
  knowledge ("context collapse") — ACE, arXiv 2510.04618.

## 8. Cross-cutting: the one idea

Every token carried on every turn competes for the same finite attention as
the live task. Minimizing what's resident isn't austerity — it's how you buy
back the model's intelligence. Prefer one session per task; recite the live
goal near the end of long sessions; push deterministic work into scripts and
hooks; and when the same problem recurs across sessions, fix the harness
(see `references/harness-fixes.md`), not the transcript.
