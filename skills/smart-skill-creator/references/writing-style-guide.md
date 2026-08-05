# Claude Skill Writing Style Guide

A prescriptive house style for authoring SKILL.md files and their `references/`. Follow every rule as written. The goal: skills that trigger reliably, read unambiguously, and stay token-lean.

**Scope:** Rules 1–9 govern the SKILL.md body and all reference files. Rules 10–11 govern the two zones with their own style. Rule 12 resolves conflicts.

---

## Part A — Sentence-level rules (body and references)

### Rule 1 — Start every instruction with a command verb

**Do:**
- "Read the config file before editing."
- "Run `scripts/validate.py` on the deliverable."

**Don't:**
- "You should read the config file first."
- "It is recommended that validation be performed."
- Any instruction phrased as a suggestion, a possibility, or advice to "you."

### Rule 2 — Keep the actor visible

Write in active voice. The actor is Claude, the user, or a script — name it, or imply Claude with the imperative.

**Do:**
- "The script writes results to `out.json`."
- "The user provides the ticket URL in their first message."

**Don't:**
- "Results are written to `out.json`." (Written by what?)
- "The ticket URL will be provided." (By whom? When?)

### Rule 3 — One instruction per sentence

Give each step its own sentence. A condition may share a sentence with its instruction.

**Do:**
- "Parse the CSV. Drop rows with empty IDs. Sort by date."
- "If the file exceeds 10 MB, stream it in chunks."

**Don't:**
- "Parse the CSV and then filter it, dropping empty-ID rows, and afterwards sort everything by date."
- Any step containing "and then."

**Exception:** where splitting would triple the line count with no clarity gain, keep the denser sentence. The 500-line ceiling on SKILL.md outranks this rule.

### Rule 4 — Treat 20 words as a rewrite tripwire

When a procedural sentence passes ~20 words (~25 for descriptive text), rewrite it — usually by applying Rule 3. A 22-word sentence that reads clearly may stay; a 35-word sentence never does.

**Don't:** enforce this as a hard cap. Clarity is the target; the number is only the alarm.

### Rule 5 — One term per concept, everywhere

Choose one verb per operation and one noun per object. Use them in every sentence of the skill. Build a terminology table in your drafting notes at the moment you catch yourself reaching for a synonym. Keep the table out of the shipped skill.

**Do:**

| Concept | Chosen term | Now banned in this skill |
|---|---|---|
| Getting data out | extract | pull, retrieve, get, grab |
| The settings file | config | settings, preferences, options |
| The final file | deliverable | output, result, artifact |

**Don't:**
- Alternate synonyms for variety. Variety reads as distinction: a skill that says "config" in step 2 and "settings file" in step 5 implies two different files.

### Rule 6 — Name the specific action and amount

**Do:**
- "Truncate the log to the last 200 lines."
- "Retry the request twice, then report the failure."

**Don't:**
- "Shorten the log appropriately."
- "Handle errors as needed."
- Use "process," "handle," "deal with," "appropriately," "as needed," "some," "various," or "etc." in an instruction. Each one delegates a decision without giving the information to make it.

### Rule 7 — Use the standard term of art

Write "idempotent," "rebase," "tokenize," "memoize" — whatever the domain's ordinary technical word is.

**Don't:** invent a plainer paraphrase for a term the model already knows. "Run the operation again without side effects on repeat" is longer and vaguer than "idempotent."

### Rule 8 — Keep grammar flat

Present tense for facts. Imperative for steps. "Will" only for genuine future consequences. At most one subordinate clause per sentence.

**Don't:**
- "Having ensured that the file, which may have been modified by an earlier run whose state is unknown, has been backed up, proceed."
- Stack conditions inside conditions. Break them into an ordered list of `If X → do Y` lines.

### Rule 9 — Attach the reason to every non-obvious rule

**Do:**
- "Use pdfplumber for table extraction, because pypdf drops cell boundaries in merged cells."
- "Log the row number on a parse error and continue, because one bad row must not abort a 10,000-row job."

**Don't:**
- Write "MUST," "NEVER," or "ALWAYS" in caps. Catching yourself typing one is the signal to reframe as rule + reason. A bare rule works only on inputs you anticipated; a reason lets Claude generalize to inputs you didn't.
- Add a reason to genuinely obvious steps. "Read the file before summarizing it, because you cannot summarize unread text" wastes tokens.

---

## Part B — Zone rules

### Rule 10 — Write the frontmatter description in the user's own language

The description is the only text loaded at startup, and it alone decides whether the skill fires. Every rule in Part A is suspended here.

**Do:**
- Write third person: "Transforms a funny idea into 3 satirical headlines…"
- Pack in verbatim trigger phrasings, casual included: "turn this into a skill", "is this still good to eat", "what's wrong with my deck".
- Cover implicit asks: "even if they don't explicitly say 'dashboard'."
- Add negative triggers for near-miss cases: "Do NOT use for X (use [other-skill] instead)."
- Err pushy. Under-triggering is the default failure mode.

**Don't:**
- Apply the terminology table, sentence caps, or imperative mood to the description.
- Sanitize colloquial trigger phrases into formal prose. Their value is that they match what users actually type.
- Put "when to use" information anywhere in the body. Claude never sees the body until after the trigger decision is made.

### Rule 11 — Keep examples verbatim

Every skill includes at least one concrete input→output example. Claude generalizes from one real example better than from fifty lines of abstract rules.

**Do:**
- Reproduce real user phrasing and real output exactly, typos and informality included.

**Don't:**
- Rewrite example text to conform to Part A. An edited example teaches the wrong distribution.
- Substitute a description of the output for the output itself.

---

## Rule 12 — Conflict resolution order

When two rules collide, the earlier item wins:

1. Triggering reliability (Rule 10)
2. Example fidelity (Rule 11)
3. Token budget — body under 500 lines, splitting to `references/` from ~300
4. Reasoning attached to rules (Rule 9)
5. Sentence-level rules (Rules 1–8)

---

## Worked before/after

**Before:**

> You'll want to make sure that the data gets cleaned up first — various issues like empty rows or weird headers should be dealt with appropriately, and then you can go ahead and process everything and generate the output, handling any errors as needed.

**After:**

> Clean the data before analysis. Drop empty rows. If the header row contains merged cells, flatten it with `scripts/flatten_header.py`. Then run the analysis. On a parse error, log the row number and continue, because one bad row must not abort a 10,000-row job.

Violations fixed: buried actor (Rule 2), compound "and then" step (Rule 3), "various / appropriately / as needed" (Rule 6), missing reason on the error-handling rule (Rule 9).

---

## Pre-ship checklist

Run against the finished skill. Fix violations; never annotate them.

**Part A conformance (body + references):**
- [ ] Every instruction opens with a command verb (Rule 1)
- [ ] No passive voice in procedures (Rule 2)
- [ ] No "and then" compound steps (Rule 3)
- [ ] No sentence far past the 20/25-word tripwire without cause (Rule 4)
- [ ] Terminology table applied throughout (Rule 5)
- [ ] Zero instances of "handle / process / appropriately / as needed / various / etc." in instructions (Rule 6)
- [ ] Standard terms of art used, none paraphrased (Rule 7)
- [ ] No sentence with more than one subordinate clause (Rule 8)
- [ ] Every non-obvious rule carries a "because"; zero ALL-CAPS directives (Rule 9)

**Part B conformance:**
- [ ] Description: third person, verbatim user phrasings, implicit cases, negative triggers (Rule 10)
- [ ] All "when to use" content lives in the description, none in the body (Rule 10)
- [ ] ≥1 verbatim input→output example, untouched by Part A editing (Rule 11)

**General skill hygiene (unchanged by this guide):**
- [ ] Gotchas section present, each entry with its reason
- [ ] One default tool per job; no option menus
- [ ] Forward-slash paths; no `@` imports in SKILL.md
- [ ] References one level deep; TOC on any reference over ~100 lines
- [ ] ≥3 realistic eval prompts in `evals/evals.json`, tested against the no-skill baseline

---

## Workflow tip

Draft naturally first. Apply this guide as a dedicated editing pass, checklist in hand. Writing to the rules from a blank page is slower and produces stiffer prose than editing toward them.
