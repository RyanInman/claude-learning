# Session-Review Strengthening — Design

**Date:** 2026-07-01
**Target:** `skills/session-review/` (SKILL.md, references/review-checklist.md, references/harness-fixes.md, scripts/analyze_session.py)
**Approach:** Additive. Modernize analyze_session.py for the current transcript format and new usage fields; fold verified mid-2026 facts into the two references; minimal SKILL.md edits. No restructuring.

**Request:** "update skills/session-review/SKILL.md with latest best practices from Anthropic and the community - focus on speed increase, good structure and token optimization."

**Assumptions (user was away when asked; flag if wrong):**
- Focus means both (a) the advice the skill gives about sessions and (b) the skill's own structure and token footprint.
- Scope is the whole skill folder, not just SKILL.md, following the skill-reviewer strengthening precedent.
- Fresh research wanted; three research passes ran 2026-07-01 against primary sources (platform.claude.com docs, code.claude.com docs + changelog, engineering blogs, arXiv, local transcript inspection). Every claim below is verified; items research flagged UNVERIFIED are excluded or labeled.

## Goal

Bring the session-review skill's measurement and advice up to mid-2026 reality. Two forces drive this:

1. **The transcript format drifted under the script.** Subagent turns no longer interleave in the main JSONL (they live in a sibling `<session-id>/subagents/agent-*.jsonl` directory), so `sidechain_entries` reads 0 on modern transcripts and all subagent token spend is invisible. New fields the script ignores directly measure the user's three focus areas: `turn_duration` system entries (speed), `usage.speed` fast-mode marker (speed/cost), `cache_creation` 5m/1h TTL split (token cost), `attributionSkill` (token attribution).
2. **The advice layer predates the current levers.** Effort levels replaced thinking budgets as the primary reasoning/speed control; tool search made "too many MCP tools" a configuration check rather than a pruning lecture; 1M-token windows are now default on most models (the script's hardcoded 200k window overstates utilization); compaction survival rules are now documented precisely; multi-turn degradation went from folklore to an ICLR 2026 oral.

## Considered approaches

- **A. Additive strengthening (chosen).** Keep the three-layer structure (script measures, references interpret, SKILL.md routes). Update each layer in place. Lowest risk, consistent with the sibling skill-reviewer update, every change traceable to a verified fact.
- **B. Rebuild around speed/cost/structure pillar reports.** Cleaner thematic mapping to the request, but discards a working structure, large diff, high regression risk.
- **C. Script-only modernization.** Fixes the broken measurement but leaves stale advice (thinking budgets, 200k window, missing effort/fast-mode/tool-search guidance); does not deliver "latest best practices."

## Design principles

- Script does deterministic measurement; references interpret; SKILL.md routes. Unchanged.
- All new parsing tolerates old transcripts: both sidechain formats, absent fields, absent subagent dirs.
- Only verified numbers enter references, each with its source. Community folklore is labeled as such (e.g. the 40–60% utilization band) or cut (e.g. "compact at 60%" cadence numbers).
- Signals stay conservative: new metrics default to informational; only discriminating evidence (warm cache misses) changes an existing signal's meaning.
- Line budgets: SKILL.md < 200 lines (now 168); review-checklist.md ≤ ~220 (now 153); harness-fixes.md ≤ ~160 (now 109). Growth is paid for by cutting stale content.

## 1. scripts/analyze_session.py — measurement modernization

Six changes, each absence-tolerant:

1. **Subagent transcript discovery (format-drift fix).** Given a session file, also scan the sibling `<session-id>/subagents/agent-*.jsonl` directory (format since ~v2.1.15x). New `subagents` block: transcript file count, aggregated token totals (billed input, cache read/create, output), per-agent count. Keep legacy interleaved `isSidechain` counting for old transcripts. No new signal; subagent use is usually good hygiene, but its spend must be visible.
2. **Turn latency.** Parse `type: "system", subtype: "turn_duration"` entries (`durationMs`, `messageCount`). New `latency` block: turns measured, mean/median/max duration, top-3 slowest turns. Informational only; long turns are normal for autonomous work. The checklist interprets (long turn + low output + duplicate calls = thrash).
3. **Cache TTL-gap discrimination.** The 5-minute default cache TTL means idle gaps between turns guarantee a miss that is *expected*, not a harness bug. Compute gaps between consecutive assistant timestamps; classify each existing miss-turn as `after_ttl_gap` (gap > 300s) or `warm` (gap ≤ 300s). Warm misses indicate prefix instability (the real defect); TTL-gap misses are idle cost. `low_cache_hit` signal keeps its threshold but the report gains `warm_cache_miss_turns` as the discriminating evidence. Also surface the `cache_creation.ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens` split when present.
4. **Per-model context windows.** Replace the single `DEFAULT_WINDOW = 200_000` with a documented model→window map (1M default: Fable 5, Mythos 5, Opus 4.8/4.7/4.6, Sonnet 5, Sonnet 4.6; 200k: Haiku 4.5 and unknown/older). `peak_context_pct_of_window` and `context_in_danger_zone` use the window of the model active on that turn. `CONTEXT_DEGRADE_TOKENS = 50_000` stays absolute (context-rot degradation is measured against token count, not window fraction).
5. **New usage fields.** `usage.speed` → `fast_mode_turns` count (fast mode marker, metric only). `attributionSkill` → per-skill output-token attribution when present, top-5. No effort detection: verified absent from transcripts across 10k+ entries; the checklist tells the reviewer to ask the user instead.
6. **Plumbing.** New blocks appear in `--format text`; `_thresholds` documents the 300s TTL-gap cutoff and the window map date; exit codes unchanged.

**Rejected for the script:** effort detection (not in transcript), dollar-cost estimation (pricing churns; `/usage` reports it locally), parsing agent-team files (experimental, off by default).

## 2. references/review-checklist.md — knowledge refresh

Section-by-section (structure and severity tags unchanged):

- **§1 Context.** Add current citations: "context rot" is now official Anthropic vocabulary; Chroma's 18-model report (focused ~300-token prompts significantly outperform full ~113k-token contexts on LongMemEval; shuffled haystacks beat structured ones). Label the 40–60% utilization target as community guidance (HumanLayer ACE-FCA), not official — no official numeric target exists. Add the official **two-correction rule**: after 2 failed corrections on the same issue, `/clear` and rewrite the prompt with what you learned. Multi-turn drift gets its hard citation here or in §6: arXiv 2505.06120, 39% average multi-turn drop, models over-anchor on their own early wrong answers.
- **§2 Cache.** Add TTL mechanics: 5-min default refreshed free on each use, 1h option at 2x write; reads cost 0.1x input, 5-min writes 1.25x. Add the new discriminator: idle-gap misses are expected; only warm misses indicate prefix instability. Add: fast-mode toggling mid-conversation repays the full context at fast-mode uncached price (once per conversation) — enable from the start or not at all. Thinking-mode toggling invalidates message-level cache only (tools/system survive). Model switch still = full miss.
- **§3 Tools.** Rewrite the tool-sprawl fix for 2026: MCP tool search is on by default (schemas deferred, ~85% token reduction per Anthropic; check `ENABLE_TOOL_SEARCH` isn't forced off), prefer CLI tools (`gh`, `aws`, `gcloud`) over MCP servers, disable unused servers via `/mcp`. Large-tool-output fix gains the programmatic pattern: process bulk output in a script on disk and return a summary (Anthropic: +11% accuracy, −24% input tokens for code-orchestrated tool use), or a PostToolUse hook that trims verbose output.
- **§4 Output/latency.** Keep output-length-dominates-latency (decode is sequential; ~linear in output tokens). Add the two explicit speed levers: **effort** (`/effort`, five levels low→max, per-model calibration, default high; lower it for mechanical work; skills and subagents can pin `effort` in frontmatter) and **fast mode** (Opus 4.8: ~2.5x faster at 2x price, cache caveat above, not available on Fable/Sonnet/Haiku). Add Fable 5 verbosity note: un-steered it elaborates beyond the task; a short brevity instruction suffices. Parallel tool calls and Haiku-routed subagents for mechanical steps.
- **§5 Reasoning.** Rewrite around effort replacing thinking budgets: `budget_tokens` deprecated on newer models; adaptive-thinking models ignore `MAX_THINKING_TOKENS`; thinking cannot be disabled on Fable 5; `ultrathink` is the only remaining magic keyword ("think hard" no longer triggers anything). Prior-turn thinking blocks are now *kept* by default on newer models and bill as input — a context-growth source the old text assumed away. Effort level is not recoverable from the transcript: ask the user what it was set to.
- **§6 Reliability.** Keep, plus the citation from §1 and one counterpoint: keep errors in context during active debugging (erasing failures removes the evidence the model adapts from — Manus); clean them at task boundaries.
- **§7 Compaction.** Replace approximations with the verified survival table: project-root CLAUDE.md + unscoped rules + auto memory re-injected from disk; path-scoped rules and nested CLAUDE.md lost until a matching file is re-read; invoked skill bodies re-injected capped at 5,000 tokens/skill and 25,000 total, oldest dropped first; the skill *listing* is not re-injected. Auto-compact clears older tool outputs first, then summarizes; thrashing guard stops after a few attempts. Steer with a "Compact Instructions" CLAUDE.md section or `/compact <focus>`. Add ACE failure modes for any compaction/rewrite advice: brevity bias and context collapse — prefer incremental delta edits over full rewrites. Bridging artifacts (spec file → fresh session) are now official guidance.
- **§8 Cross-cutting.** Stands; add recitation (re-state the live task near the end of long sessions) and "one session per task, not one session per project."

## 3. references/harness-fixes.md — refresh

- **§2 CLAUDE.md.** The ~200-line guideline and per-line litmus test are now official wording; cite. Add: move conditional knowledge into skills (official costs guidance); auto memory loads first 200 lines / 25KB of MEMORY.md.
- **§3 Skills.** Add the listing-budget mechanics: descriptions share a budget of 1% of the context window with a 1,536-char per-entry cap; overflow drops least-invoked skills' descriptions; `/doctor` reports shortened/dropped entries; knobs are `skillListingMaxDescChars`, `skillListingBudgetFraction`, `skillOverrides` name-only, and `disable-model-invocation: true` for user-only skills. Add: skills and subagents can pin `model:` and `effort:` in frontmatter — the routing lever for cheap mechanical steps.
- **§4 Hooks.** Add: hooks run as code, not context — only `additionalContext` output enters the window; a PostToolUse hook that condenses verbose tool output is a token fix, not just a guarantee.
- **§5 Tool definitions.** Add MCP-vs-CLI guidance and tool-search defaults (mirror checklist §3).
- **§6 Token-tier table.** Add a "deferred" row for MCP tool schemas (names only until used).

## 4. SKILL.md — minimal edits

1. **Inputs section:** note subagent transcripts live in the sibling `<session-id>/subagents/` directory and the script aggregates them automatically.
2. **Step 2 telemetry:** add `/usage` (session cost + per-skill/subagent/plugin/MCP breakdown; `/cost` is now an alias); note `/context` reports the post-budget skill-listing size.
3. **Gotchas, three additions:** idle-gap cache misses are expected (5-min TTL) — only warm-gap misses indicate prefix instability; effort level is not in the transcript — ask the user; long turns are not inherently bad (autonomous runs), interpret with output and duplicate-call evidence.
4. **Description:** measured at 985 chars, under the 1,536 cap — no change (surgical-changes rule).

## Out of scope

- Restructuring the skill or splitting references by pillar.
- Live-session instrumentation or dollar-cost estimation.
- Non-Claude-Code transcript formats; agent-teams review (experimental, off by default).
- Reviewing SKILL.md files (stays with skill-reviewer).

## Verification

- **Fixture pair for the script** (precedent: audit.py fixture harness): one legacy-format fixture (interleaved `isSidechain` entries) and one modern fixture (main file + `subagents/` dir + `turn_duration` entries + `usage.speed` + TTL split + `attributionSkill`), with a small runner asserting expected metrics and signals from each. The TTL fixture includes one warm miss and one post-gap miss and asserts they classify differently.
- Run the script against 2–3 real local sessions under `~/.claude/projects`: no crashes, subagents detected on modern transcripts, sane text summary.
- `python3 -m py_compile scripts/analyze_session.py` passes; exit codes unchanged.
- Line budgets hold: SKILL.md < 200; review-checklist.md ≤ ~220; harness-fixes.md ≤ ~160; description ≤ 1,536 chars.
- Citation gate: every number in the references traces to a source below; items research flagged UNVERIFIED stay out (official utilization % target, "microcompaction" as a term, minimum-cacheable-token table, compact-at-60% cadence as fact).

## Sources (verified 2026-07-01)

- Prompt caching (TTL, pricing, prefix order, invalidation): platform.claude.com/docs/en/build-with-claude/prompt-caching.md
- Context windows, 1M defaults, thinking-block retention: platform.claude.com/docs/en/build-with-claude/context-windows.md
- Effort levels: platform.claude.com/docs/en/build-with-claude/effort.md; code.claude.com/docs/en/model-config
- Adaptive thinking + cache interaction: platform.claude.com/docs/en/build-with-claude/adaptive-thinking.md
- Fable 5 conduct (verbosity, over-prescription, context anxiety): platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md
- Compaction survival table, preload costs, /context: code.claude.com/docs/en/context-window.md
- Fast mode: code.claude.com/docs/en/fast-mode
- Costs levers (CLAUDE.md→skills, MCP overhead, /usage): code.claude.com/docs/en/costs
- Skill listing budget: code.claude.com/docs/en/skills.md
- Tool search / MCP deferral: code.claude.com/docs/en/mcp; anthropic.com/engineering/advanced-tool-use
- Best practices (two-correction rule, /clear, bridging artifacts): code.claude.com/docs/en/best-practices
- Context engineering: anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Context editing + memory numbers: claude.com/blog/context-management
- Chroma context rot: research.trychroma.com/context-rot
- Lost in the middle: arXiv 2307.03172
- Multi-turn degradation: arXiv 2505.06120
- ACE (brevity bias, context collapse): arXiv 2510.04618
- Manus KV-cache practices: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- HumanLayer ACE-FCA (40–60% band, labeled community): github.com/humanlayer/advanced-context-engineering-for-coding-agents
- JSONL format (empirical + community): local `~/.claude/projects` inspection; github.com/daaain/claude-code-log; claude-dev.tools/docs/jsonl-format
