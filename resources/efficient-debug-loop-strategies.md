# The Debug Loop Playbook for Claude Code (and Any Agentic Coding Assistant)

## TL;DR
- **The single highest-leverage move is to give the agent a check it can run.** Every effective debug loop with Claude Code (or any LLM coding agent) is a closed feedback loop: reproduce the failure with a fixed input, write a failing test or repro script *first*, let the model form and rank hypotheses, make one small instrumented change, run the check, and read the real output — never trust "looks fixed."
- **Context is the scarce resource, not model intelligence.** Long debugging sessions rot: failed attempts, stack traces, and dead-end file reads pollute the window and bias the model toward repeating its own mistakes. Manage context aggressively — `/clear` after two failed corrections, offload noisy investigation to subagents, and externalize findings to a scratchpad/CLAUDE.md before resetting.
- **Small, single-variable diffs on a clean git history are what make LLM debugging tractable.** Checkpoint constantly, keep changes atomic, insist on root-cause fixes over symptom patches, and set deterministic gates (hooks running tests/linters after edits) so the loop closes itself instead of relying on you to catch every error.

## Key Findings

1. **Verification-driven debugging is the core pattern.** Anthropic's own guidance states that "Claude stops when the work looks done. Without a check it can run, 'looks done' is the only signal available, and you become the verification loop." The fix is to give Claude something that returns a pass/fail signal — a test suite, build exit code, linter, or screenshot diff — so it iterates until the check passes. For bugs specifically, Anthropic's recommended prompt pattern is: "write a failing test that reproduces the issue, then fix it."

2. **Tight feedback loops beat long reasoning chains.** Both practitioner and research sources converge: human-style "generation → verification → feedback" loops let the model use negative feedback to progressively approximate the correct patch, rather than one-shotting. Grounding on real runtime state (print statements, logs, traces) is what bridges the gap between a *symptom* and a *root cause* — research on LLM program repair found that when models only see outcome-level symptoms they produce "plausible but incorrect" patches that mask the symptom.

3. **Context rot is the dominant failure mode.** Chroma's technical report *"Context Rot: How Increasing Input Tokens Impacts LLM Performance"* (July 14, 2025; Kelly Hong, Anton Troynikov & Jeff Huber) evaluated 18 frontier models — including GPT-4.1, Claude 4, Gemini 2.5, and Qwen3 — and found that "models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows." Anthropic's docs echo this: "LLM performance degrades as context fills… Claude may start 'forgetting' earlier instructions or making more mistakes." Accumulated failed attempts are especially toxic because they bias the model toward repeating ruled-out approaches.

4. **Anthropic's explicit rule: after two failed corrections, reset.** From the Claude Code best-practices docs: "If you've corrected Claude more than twice on the same issue in one session, the context is cluttered with failed approaches. Run `/clear` and start fresh with a more specific prompt… A clean session with a better prompt almost always outperforms a long session with accumulated corrections."

5. **Subagents are the primary tool for keeping the debug loop clean.** Investigation ("read 20 files, grep error patterns, check config, scan commits") produces verbose output you don't need later. Running it in a subagent returns only a summary to the main thread; the noise never accumulates. Anthropic: "Since context is your fundamental constraint, subagents are one of the most powerful tools available."

6. **Anti-patterns are predictable and detectable.** The recurring ones: looping on the same wrong fix, sycophantic "you're right, that's fixed!" without verification, hallucinated APIs/packages, and making too many changes at once (scope creep). Each has a specific countermeasure covered below.

## Details

### 1. Debug loop fundamentals: hypothesize → test → observe → refine

The reliable structure for troubleshooting with an LLM agent is an explicit, verification-gated loop:

1. **Reproduce first, deterministically.** Pin the exact input that reliably triggers the failure. As one field guide puts it, "Variability at this stage means you're debugging a different problem each iteration." Ask Claude to write a minimal reproduction script or a failing test before touching any implementation code.
2. **State and rank hypotheses.** Have the model enumerate 2–4 candidate root causes and rank them by likelihood *before* editing. This forces externalized reasoning and prevents the "jump straight to a fix" reflex.
3. **Instrument, don't guess.** Instruct the model to add logging/print statements to observe runtime state, rather than speculating. Research on LLM repair shows runtime intermediate states "act as a critical bridge between the symptom and the root cause."
4. **Make one small change.** Change a single variable, run the check, read the actual output.
5. **Observe the real signal.** Feed exact test output / stack traces back into the loop. Anthropic recommends having Claude "show evidence rather than asserting success: the test output, the command it ran and what it returned."
6. **Refine or abandon.** If the top hypothesis is disproven, move to the next; if two or three attempts fail, reset context (see §2).

**Verification-driven ("test-first") debugging** is Anthropic's most strongly endorsed pattern. The original best-practices post spelled out a TDD loop verbatim: "Ask Claude to write tests based on expected input/output pairs. Be explicit about the fact that you're doing test-driven development so that it avoids creating mock implementations… Tell Claude to run the tests and confirm they fail. Explicitly telling it not to write any implementation code at this stage is often helpful… Ask Claude to write code that passes the tests, instructing it not to modify the tests. Tell Claude to keep going until all tests pass." Committing the failing test as a checkpoint first is critical: Claude will sometimes alter tests to make them pass, and the committed diff exposes that. Anthropic also suggests having "independent sub-agents verify whether the implementation overfits the tests."

### 2. Context management principles

Anthropic's docs are blunt: "Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills." A single debugging session "might generate and consume tens of thousands of tokens."

Practical rules:

- **Compact proactively, not reactively.** `/compact` summarizes and replaces history while preserving essentials; `/clear` wipes conversation entirely (code changes and CLAUDE.md survive). Practitioners recommend compacting at roughly 60% context utilization — well before the ~80% auto-compact threshold — because "auto-compaction fires… at the model's lowest point of intelligence (context rot is worst near the limit)." Steer it: `/compact focus on the auth refactor, drop the test debugging`.
- **`/clear` between unrelated tasks and after failed loops.** This is the antidote to the "kitchen sink session" and "correcting over and over" anti-patterns Anthropic names explicitly.
- **Externalize state before resetting.** Write a short scratchpad — what you're debugging, what you've ruled out, the reproduction steps, the current hypothesis — into a notes file or CLAUDE.md, then `/clear` and paste that brief as your first message. Anthropic's long-running-agent research formalizes this: their harness uses a `claude-progress.txt` file plus git history so a fresh context window can "quickly understand the state of work." The key insight was learning "what effective software engineers do every day" — leave clean artifacts for the next shift.
- **Why accumulated failures bias the model.** Research on agent failure modes documents that "LLM agents frequently fall into unproductive loops, repeatedly executing ineffective actions," misinterpreting feedback and reasoning inconsistently over long trajectories. The failed attempts sitting in context act as (misleading) examples the model pattern-matches against. The "lost-in-the-middle" effect compounds this: accuracy can drop 30+ points when relevant facts sit in the middle of a long context rather than at the start or end.
- **Guard CLAUDE.md against bloat.** "Bloated CLAUDE.md files cause Claude to ignore your actual instructions." For each line ask: "Would removing this cause Claude to make mistakes?" If not, cut it.

### 3. Prompting strategies for debugging

- **Provide exact artifacts.** Paste the full error message and stack trace, not a paraphrase. Anthropic's before/after: instead of "the build is failing," use "the build fails with this error: [paste error]. fix it and verify the build succeeds. address the root cause, don't suppress the error." You can pipe logs directly: `cat error.log | claude`.
- **Give a minimal reproduction.** The discipline of shrinking to an MRE "helps build a deeper understanding of the problem and frequently leads to finding the root cause." Smaller repros also keep context lean.
- **Ask for hypotheses first, ranked.** "Before editing, list the top three likely causes ranked by probability and tell me how you'd test each." This surfaces reasoning you can correct cheaply.
- **Demand root cause, not symptomatic patches.** Explicitly say "address the root cause, don't suppress the error" — otherwise models tend to clamp values or swallow exceptions to make the symptom disappear.
- **Instrument over guess.** "Add logging to show the actual runtime values of X and Y, run it, and show me the output before proposing a fix."
- **Ask the model to explain before fixing.** For unfamiliar code, "explain what this function does and why it calls foo() instead of bar() on line 333" before any edit — this is also an effective onboarding pattern per Anthropic.
- **Scope the symptom precisely.** "users report that login fails after session timeout. check the auth flow in src/auth/, especially token refresh. write a failing test that reproduces the issue, then fix it."

### 4. Tool / harness setup

- **Automated feedback via hooks.** Claude Code hooks run deterministically at lifecycle points. A `PostToolUse` hook running your test runner (or `--findRelatedTests` for the edited file) after every Edit/Write gives "immediate feedback… Claude can fix its own mistakes while context is fresh." A `Stop` hook can gate the turn from ending until tests pass (Claude Code overrides it after 8 consecutive blocks). Unlike CLAUDE.md instructions, which are advisory, "hooks are deterministic and guarantee the action happens." Pair with linters/type checkers/formatters so quality checks "just happen. Every single time."
- **Plan mode for complex bugs.** Enter plan mode (`Shift+Tab`) to make Claude read and reason without editing — "separate research and planning from implementation to avoid solving the wrong problem." For a one-line fix, skip it; for a multi-file or unfamiliar bug, use it.
- **Extended thinking.** Trigger words escalate the reasoning budget: "these specific phrases are mapped directly to increasing levels of thinking budget in the system: 'think' < 'think hard' < 'think harder' < 'ultrathink.'" (The specific token figures — roughly 4,000 for "think," ~10,000 for "megathink"/"think hard," and 31,999 for "ultrathink" — come from Simon Willison's reverse-engineering of the CLI, not from Anthropic's blog text; note his decompilation found "think harder" and "ultrathink" both map to 31,999, contradicting the blog's implied strict ordering.) Reserve the heavy levels for genuinely hard bugs — extended thinking can make simple tasks more verbose and less accurate, and thinking tokens are billed as output.
- **Subagents for investigation.** "Use subagents to investigate why the test suite is failing" — the subagent reads dozens of files in its own context and returns a compact conclusion. Rule of thumb: "If the work is likely to be discarded, it should run in a subagent." Be aware of the cost: Anthropic's own multi-agent research system consumed roughly 15× more tokens than a plain chat (single agents ~4×), and in that work "token usage alone explains 80% of performance variance" — so spin up subagents for genuinely noisy investigation, not trivial lookups.
- **Git workflows.** Commit after each passing step so every change is independently revertible. LLMs "are really good at parsing diffs and using tools like `git bisect` to find where a bug was introduced" — but only "if you have a tidy commit history to begin with." Use `git bisect` (binary search — ~10 steps for 1,000 commits) to localize a regression, `git diff HEAD --stat` to audit what the agent actually touched, and `git revert`/`/rewind` checkpoints to roll back cleanly. Use worktrees/branches to isolate risky experiments. (Note: Claude Code's `/rewind` checkpoints only track changes made through Claude's file-editing tools — not Bash-driven changes — so they're not a git replacement.)
- **Adversarial review in fresh context.** Have a separate subagent or session review the fix diff "in a fresh context" so it "won't be biased toward code it just wrote." Tell it to flag only correctness/requirement gaps, since a reviewer asked to find problems will invent them, leading to over-engineering.

### 5. Common failure modes and anti-patterns

| Failure mode | How it shows up | Countermeasure |
|---|---|---|
| **Looping on the same wrong fix** | Same edit re-applied; unbounded "let me try another approach" with no diagnosis | After two failed corrections, `/clear` and restart with a sharper prompt incorporating what you learned |
| **Sycophantic "it's fixed"** | Model agrees a fix worked without running anything; revises toward what you seem to want | Require evidence (test output, command + result); never accept "looks fixed" — gate on a real check |
| **Hallucinated APIs / packages** | Calls to non-existent methods or imports of fake packages | Ground with type checkers/linters and code-intelligence plugins; verify package names against the registry before install |
| **Too many changes at once** | A one-class task returns a 14–40 file diff with unrequested refactors | Impose a "change budget"; scope prompts tightly; small atomic commits; review rendered diffs |
| **Context pollution / rot** | Model forgets constraints, contradicts earlier decisions, degrades mid-session | Compact/clear proactively; push investigation to subagents; externalize to scratchpad |
| **Overfitting the test** | Patch passes tests but is semantically wrong | Commit tests first; use an independent subagent to check whether the implementation overfits |

**On hallucinated packages specifically:** this is a well-quantified, common failure, not a fringe risk. Spracklen et al.'s USENIX Security 2025 study *"We Have a Package for You!"* found that **19.7% of recommended packages across 576,000 code samples from 16 LLMs were hallucinated** — 205,474 unique fake package names — with open-source models (21.7%) far worse than commercial ones (5.2%). Attackers exploit this via "slopsquatting" (registering the fake names). Encouragingly, the same research found strong models like GPT-4 Turbo and DeepSeek correctly flagged their own hallucinated names ~75% of the time, and a 2026 re-evaluation found frontier per-model rates compressed to roughly 4.6–6.1% — but five models still invented 127 identical fake names, so registry verification before install remains essential.

**When to abandon and restart:** the trigger is empirical — if you've corrected the same issue more than twice, or the model is proposing variants of a ruled-out fix, or output quality has visibly dropped mid-session. A clean session with a better prompt almost always beats a long polluted one.

### 6. General LLM principles underlying all of this

- **LLMs benefit from externalized state.** The tokens the model emits *are* its working memory between steps — unlike a human scratchpad that merely supplements internal memory. That's why writing hypotheses, progress notes, and reproduction steps to files (and to the visible reasoning trace) materially improves multi-step debugging: complex problems "require LLMs to externalize their reasoning."
- **Verification must be external and grounded.** The CRITIC-style principle: don't trust the model's introspection; use compilers, validators, and test suites to check output properties. Self-correction without an external signal risks *sycophantic correction*, where "the initial answer might have been more correct than the 'corrected' version."
- **Error-message grounding turns a nebulous problem into a concrete one.** Feeding the exact trace/runtime values is what lets the model localize the true fault instead of masking a symptom.
- **Small diffs and single-variable changes** make each step "independently reviewable and revertible" — "when something breaks, you git bisect to the exact line instead of debugging a half-finished mess."
- **Explicit reasoning (chain-of-thought / extended thinking)** improves accuracy on multi-step problems by giving the model space to explore and backtrack before committing.
- **Context is finite with diminishing returns.** Anthropic's context-engineering guidance frames the whole discipline as "finding the smallest set of high-signal tokens that maximize the likelihood of your desired outcome." Every principle above is, at bottom, a way to keep the signal-to-noise ratio high.

## Recommendations

**Stage 0 — Set up the harness once (do this before your next bug):**
1. Add a `PostToolUse` hook that runs the relevant tests (and linter/type checker) after every edit; add a `Stop` hook that blocks turn-end until tests pass.
2. Put your test/build/lint commands and any environment quirks in a concise CLAUDE.md. Install a code-intelligence plugin if you use a typed language (catches hallucinated symbols automatically).
3. Ensure a clean, small-commit git workflow is your default.

**Stage 1 — Every bug starts the same way:**
1. Reproduce deterministically; ask Claude to write a *failing test or repro script first* and commit it.
2. Ask for 2–4 ranked hypotheses before any edit; use plan mode (and "think hard"/"ultrathink") if the bug is complex or unfamiliar.
3. Delegate wide investigation to a subagent so the main thread stays clean.

**Stage 2 — Iterate in tight, grounded loops:**
1. Instrument with logging; make one small change; run the check; read the real output.
2. Insist on root-cause fixes ("don't suppress the error"). Require evidence of success — never accept "it's fixed."
3. Commit after each green step.

**Stage 3 — Know when to reset (the benchmark that changes your action):**
- **Corrected the same issue >2 times, or seeing repeated ruled-out fixes, or quality dropping** → externalize findings to a scratchpad/CLAUDE.md, `/clear`, and restart with a sharper prompt.
- **Context utilization approaching ~60%** → `/compact` with a focus hint before quality degrades.
- **A regression with unknown origin** → switch to `git bisect`.
- **Fix looks done** → run an adversarial review in a fresh subagent/session before shipping.

## Caveats
- **Some numbers are secondary or reverse-engineered.** The extended-thinking token budgets (4k / 10k / 31,999) come from Simon Willison's decompilation of the Claude Code CLI, not Anthropic's official text; treat them as approximate and version-dependent. Anthropic's blog states only the ordered phrase list.
- **The 15× subagent token figure is context-specific.** It comes from Anthropic's multi-agent *research* system on a browsing benchmark, not from Claude Code debugging specifically; individual practitioner estimates for Claude Code subagent overhead vary (commonly cited around 4–7×). Use it as an order-of-magnitude caution, not a precise rate.
- **Claude Code evolves quickly.** Exact command behavior (`/rewind`, `/compact`, `/goal`, hooks, auto mode, context-window size) changes between releases; the original April 2025 "Claude Code: Best practices for agentic coding" post has since been substantially rewritten into the current docs. Verify against the current docs. This report reflects guidance as of mid-2026.
- **LLM debugging is non-deterministic.** Even at temperature 0, infrastructure factors (batching, caching, floating-point ordering) can cause a "deterministic" test to pass three times and fail the fourth — freeze inputs when reproducing and don't over-interpret a single run.
- **Practitioner blogs vary in reliability.** Anthropic's official docs/engineering posts and peer-reviewed research are the strongest sources here; individual Medium/Substack write-ups were used for corroboration of widely-repeated patterns, not as sole authorities.
- **Hooks/CI complement but don't replace review.** A local test hook speeds feedback; CI should still run the full suite before merge, and a human should still review security/infrastructure-touching diffs.