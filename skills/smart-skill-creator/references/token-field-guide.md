# Token Field Guide — Skill Grading Rules

Seven rules to grade a `skill.md` for token efficiency and instruction quality.

---

## R1 — Description triggers reliably

Description is third-person, states WHAT + WHEN, packed with concrete trigger phrases. Includes negative triggers ("do NOT use for X — use Y skill instead"). No vague noun-only title.

**Fail:** `"Handles dashboard queries."`
**Pass:** `"Use when user asks about dashboard metrics, charts, or KPIs, even if they don't say 'dashboard.' Do NOT use for raw data exports — use the data-export skill."`

---

## R2 — Body earns its tokens

Every line survives: *"if deleted, would Claude make a mistake?"* Remove:
- Obvious defaults Claude already follows
- Fossils (stale refs, sprint tasks, temporal language like "before August's API")
- Contradictions between rules
- Menus ("use X, or Y, or Z") — replace with one default + escape hatch

---

## R3 — Knowledge addressed, not imported

No `@import` of reference files. Heavy docs live in `references/` with a pointer: "read `references/schema.md` when relevant." Zero tokens until needed. An `@import` is inlined at launch — it costs full tokens regardless of relevance.

---

## R4 — Mechanical work is compiled

Deterministic steps → scripts, not prose. Hard invariants → hooks, not instructions. One concrete input→output example replaces 50 lines of abstract rules. Target: 10% LLM steering, 90% deterministic code execution.

---

## R5 — Critical rules front-loaded

Most important content appears in first 20% of body. At most 1–2 `IMPORTANT`/`MUST` markers total. If everything shouts, nothing is heard. Content in the middle of a long skill body loses >30% accuracy due to the "lost in the middle" effect.

---

## R6 — Output is constrained

Skill instructs Claude to produce structured output (JSON/CSV), cap volume ("report max 5 items"), or write reasoning to file rather than narrate it. Generation is where latency lives — skills must manage it explicitly.

---

## R7 — Skill has one job

Scope is narrow enough that overlap with other skills is zero or explicitly excluded via negative triggers. A skill doing two jobs is two skills — or noise that causes false-positive loading of the wrong tool.
