# The Token Heretic's Field Guide
### How to make Claude faster, cheaper, and *smarter* — by feeding it less

---

## The one idea that changes everything

You think you bought a 200K context window. You didn't. You bought an **attention budget**, and it's far smaller than the window.

Here's the heresy: **adding context can make Claude dumber.** This isn't a cost story — it's an intelligence story. When researchers loaded models with up to 500 instructions, even frontier models cratered to ~68% adherence at max density (Claude Sonnet 4 hit 42.9%, Opus 4 44.6%). Models read near-perfectly through ~100–250 instructions, then fall off. Separately, "context rot" research found a 200K-window model degrading at just **50K tokens** — long before the window is full. And the "lost in the middle" effect buries whatever sits in the center of your context under a >30% accuracy penalty.

Put those together and you get the only sentence that matters:

> **Every token you force Claude to carry on every turn competes for the same finite attention as the live task. Minimizing tokens isn't austerity — it's how you buy back intelligence.**

The rest of this guide is tactics. But they all serve that one idea.

---

## Law 1 — The most expensive token is the one you pay for *forever*

There are two kinds of tokens, and people confuse them constantly:

- **One-time tokens** — loaded once when a task triggers, then gone.
- **Recurring tokens** — loaded on *every turn of every session*, taxing you in perpetuity.

A 2,000-token always-loaded memory file across a 50-turn session isn't 2,000 tokens. It's **100,000 token-turns** of attention you spent re-reading the same rules instead of doing work. The always-loaded layer is rent. Everything else is a one-time purchase.

**The move:** ruthlessly shrink the always-loaded layer. Anthropic's own rule of thumb is a memory file under **200 lines**, and the practical instruction budget is ~150–200 before compliance erodes — of which the system prompt already eats ~50. You have maybe **150 instructions to spend.** Budget them like calories.

The litmus test for every line: *"If I deleted this, would Claude make a mistake?"* If no, it's not documentation — it's noise that's hiding your real rules. Anthropic says it bluntly: bloated memory files *cause* Claude to ignore actual instructions.

---

## Law 2 — Don't load knowledge. Load the *address* of knowledge.

This is progressive disclosure, and it's the single biggest architectural lever. Knowledge loads in three tiers:

1. **Startup:** only a skill's name + description (~100 tokens each) sit in context.
2. **On match:** the full instructions load *only when the task fits.*
3. **On demand:** reference files and scripts are read/run *only when actually needed.*

The consequence is almost too good: **bundled reference files cost zero tokens until read, and scripts cost zero until run.** Ten skills cost you ~1,000 tokens at startup instead of the 50,000+ you'd pay if every body loaded eagerly. You can attach effectively unbounded knowledge to Claude as long as it stays *addressable* rather than *resident.*

**The trap that eats beginners:** `@imports` are NOT free. An import is inlined at launch — it costs full tokens. A "read `references/schema.md` when relevant" pointer costs nothing until the moment of need. Same information, opposite economics. **Prefer pointers to imports.**

---

## Law 3 — The description is the whole game (you write ~100 tokens that decide whether 5,000 ever load)

A skill's `description` is not documentation. It's a **router.** It alone determines whether the skill fires. And Claude's failure mode is *under*-triggering — it won't reach for a skill unless the match is obvious.

So write descriptions that are deliberately, almost embarrassingly "pushy": third person, stating *what it does* AND *when to use it*, packed with concrete trigger phrases — "use this whenever the user mentions X, Y, or Z, even if they don't say 'dashboard.'" A vague description means the skill never fires and its entire token budget is wasted. A trigger-rich one fires reliably.

**Then prevent the opposite failure with negative triggers:** "Do NOT use for simple data exploration — use the data-viz skill instead." One skill, one job. Overlapping skills create a false-positive tax where the wrong tool keeps loading.

**Debugging trick:** ask Claude directly, *"When would you use the X skill?"* It'll quote the description back — instantly exposing the missing keywords.

---

## Law 4 — Compile cognition into silicon (10% steering, 90% execution)

LLMs are expensive, slow, and non-deterministic at mechanical work. So stop asking Claude to *think* through deterministic steps every time — **compile that thinking into code once.**

A 50-line validation script that returns `"Validation passed: 3 pages, 2 tables"` costs ~**15 tokens** — just its output. The 50 lines never enter context. You've outsourced the work to a substrate that doesn't think in tokens at all. The community framing for an ideal skill: **10% LLM steering, 90% deterministic code execution.**

This reframes the whole job. Three questions to triage any instruction:

- **Can a machine do this deterministically?** → Write a script. (Free cognition.)
- **Must this hold *every* time, no exceptions?** → Write a **hook**, not prose. A rule in a memory file is a polite request re-issued every turn; a PreToolUse hook is enforced once and free forever. "Never push to main" in prose is a wish. As a hook, it's physics.
- **Would one example teach it faster than a paragraph?** → Show, don't tell. One concrete input→output pair beats 50 lines of abstract rules; Claude generalizes from examples far better than from rule-lists.

---

## Law 5 — Treat context like a CPU cache, not a hard drive

Borrow the memory hierarchy. Map every piece of knowledge to a tier by *how hot it is*:

| Tier | Holds | Loads | Keep it... |
|---|---|---|---|
| **L1 — always-loaded** | Project memory (CLAUDE.md): build commands, architecture-at-a-glance, a few critical gotchas | Every turn | **Tiny** (<200 lines) |
| **L2 — locality-scoped** | Path-scoped rules (`.claude/rules/*.md` with `paths:` globs) | When Claude touches a matching file | <100 lines |
| **L3 — task-scoped** | Skill bodies | When the task matches the description | <500 lines |
| **Disk — on demand** | References, scripts, assets | Read/run only when needed | Unbounded |

The discipline is the same as cache design: **keep hot data minuscule, keep cold data addressable.** A finance query should never load the sales schema. A payments-deploy skill should never wake up while you're editing inventory. Organize references *by domain* so Claude reads only the one file the query needs.

**Boundary rule (the crux):** *Conventions go in memory; procedures go in skills.* A naming rule is always true → memory. A seven-step migration playbook → skill. If it's multi-step, needs scripts, or only matters in one corner of the codebase, it does **not** belong in the always-loaded layer.

---

## Law 6 — Put your best material first and last, never in the middle

"Lost in the middle" is real: attention forms a U-curve, and content stranded in the center of a long context can lose >30% of its accuracy. There's also a confirmed **primacy bias** — earlier instructions are obeyed more reliably.

This gives length a *second* hidden cost beyond tokens: a long file doesn't just cost more, it **relocates your important rules into the attention dead-zone.** Front-load the rules that matter. Reserve your one or two genuine "IMPORTANT / YOU MUST" markers for the rules that truly can't slip — if everything shouts, nothing is heard.

---

## The output side (because speed isn't only about input)

Everyone optimizes what goes *in*. Fewer people optimize what comes *out* — yet generation is where latency lives.

- **Don't make Claude reason verbosely in-context when it can write a compact plan to a file.** The plan-validate-execute pattern: Claude writes a structured plan (`changes.json`), a script validates it, then it executes. The reasoning lives on disk, not in the token stream — and you catch errors before they're applied.
- **Cap the volume.** "Report at most five nits." "Keep approval messages terse." A code-review skill that posts comments via a *script* instead of prose is faster, cheaper, and consistent.
- **Demand structured output** (JSON/CSV to stdout, diagnostics to stderr). Parse it; don't make the model narrate it.
- **Fork the heavy thinking.** Use `context: fork` / subagents for noisy exploration. The exploration is scratch memory — it does its work and gets discarded instead of polluting your main thread for the rest of the session.

---

## The anti-patterns (a rogues' gallery)

- **The Kitchen Sink** — the diligent dev who documents *everything*. The worst memory files are the thorough ones; an empty file costs nothing, a bloated one actively makes Claude worse.
- **The Shouting File** — `MUST`/`ALWAYS`/`NEVER` in all-caps with no reasoning. State the rule *and the why* ("use constructor injection — field injection breaks testability") so Claude can generalize to edge cases. A reason survives context shifts; a bare command gets dropped.
- **The Fossil** — stale, time-sensitive lines ("before August's API," "yesterday's deploy bug," current-sprint tasks). Memory files are not logs.
- **The Contradiction** — two well-meaning rules pulling opposite ways ("use interfaces" vs "prefer type aliases"). When rules conflict across layers, Claude may pick one *arbitrarily.* Eliminate contradictions; don't rely on precedence.
- **The Menu** — "use pypdf, or pdfplumber, or PyMuPDF, or…". Give one default with an escape hatch.
- **The Obvious** — restating defaults Claude already follows ("write clean code"). Spend tokens only on what pushes Claude *out* of its defaults — which is why a **Gotchas section** is the highest-signal content in any file. ("The `subscriptions` table is append-only — take the highest version, not the newest `created_at`.")

---

## Your Monday-morning playbook

1. **Audit your baseline.** Run `/context`, `/memory`, `/doctor`, and `wc -l CLAUDE.md`. If the always-loaded layer exceeds ~10% of the window *before any work begins*, you're starting every task half-blind. Target 40–60% peak utilization; quality drops hard above ~80%.
2. **Cut, compile, or cache — every line must earn it.** Delete obvious-defaults and fossils. Compile guarantees → hooks, mechanical steps → scripts. Cache everything situational → skills and path-scoped rules. Leave the root memory file as a lean *index*: identity, build/test commands, architecture-at-a-glance, a handful of gotchas.
3. **Make every recurring procedure a skill** the third time you paste it into chat. Write the description first — pushy, trigger-rich, with negative triggers — and test it on 8–10 natural phrasings before writing the body.
4. **Build the eval before the docs.** Run the task *without* the skill, document the failures, write the minimum to fix them, and only keep the skill if it measurably beats the no-skill baseline (fewer tool calls, fewer tokens, higher pass rate). A skill that ties baseline should be retired — the model outgrew it.
5. **Prune on a cadence, and after every model release.** Comment out compensating rules one at a time and see what's still load-bearing. Yesterday's necessary workaround is tomorrow's pure overhead.

---

## The closing line

The industry is obsessed with bigger windows. That's the wrong race. A bigger window is a bigger room to lose your keys in.

The real skill isn't *fitting more in* — it's the discipline of keeping the working set small enough that every token left in the room is fighting for the task in front of it. **Don't fill the context. Curate it.**

You're not saving money. You're buying back attention — and attention is the only thing you were ever really paying for.
