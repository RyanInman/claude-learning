# Style pass and checklist

Draft naturally first, then edit toward these rules, because writing to rules from a blank page produces stiffer prose than editing toward them. Apply them to the body and references. The description is exempt (triggering outranks style), and examples are exempt (an edited example teaches the wrong distribution).

## Sentence rules

1. Open every instruction with a command verb. "Read the config before editing", not "You should read the config first".
2. Keep the actor visible. Active voice; the actor is Claude, the user, or a script. "The script writes `out.json`", not "results are written".
3. One instruction per sentence. A condition can share its sentence. No "and then" chains.
4. Treat 20 words as a rewrite tripwire for procedural sentences (25 for descriptive). An alarm, not a cap - clarity is the target.
5. One term per concept. Synonym variety reads as distinction: "config" in step 2 and "settings file" in step 5 implies two files. Keep a terminology table in drafting notes; keep it out of the shipped skill.
6. Name the specific action and amount. "Truncate the log to the last 200 lines", never "shorten appropriately". The words "handle", "process", "appropriately", "as needed", "various", and "etc." delegate a decision without the information to make it.
7. Use the standard term of art ("idempotent", "rebase"). A plainer paraphrase is longer and vaguer.
8. Keep grammar flat: present tense for facts, imperative for steps, at most one subordinate clause. Break nested conditions into `If X → do Y` lines.
9. Attach a reason to every non-obvious rule, because a bare rule works only on inputs its author anticipated; a reason generalizes. Catching yourself typing "MUST", "NEVER", or "ALWAYS" in caps is the signal to reframe as rule-plus-reason. Skip the reason on genuinely obvious steps.

## Content rules

- Spend tokens only on what pushes Claude out of its defaults. Deleting a line that changes nothing is a strict improvement, because bloat buries the load-bearing rules.
- No option menus. One default tool per job, with an escape hatch.
- No time-sensitive lines ("before the August API"). A skill is not a log.
- No contradictions between the skill and other loaded layers - when rules conflict, Claude picks one arbitrarily.

## Pre-ship checklist

Fix violations; never annotate them.

- [ ] Every instruction opens with a command verb
- [ ] No passive voice in procedures
- [ ] No "and then" compound steps
- [ ] No sentence far past the 20/25-word tripwire without cause
- [ ] One term per concept throughout
- [ ] Zero "handle / process / appropriately / as needed / various / etc." in instructions
- [ ] Every non-obvious rule carries a "because"; zero ALL-CAPS directives
- [ ] Description: third person, verbatim trigger phrases, negative triggers
- [ ] All "when to use" content in the description, none in the body
- [ ] At least one verbatim input→output example, untouched by editing
- [ ] Gotchas section present, each entry with its reason
- [ ] Forward-slash paths; no `@` imports
- [ ] References one level deep; TOC on any reference over ~100 lines
- [ ] Only when the user asked for evals: 3 or more prompts in `evals/evals.json`, run against the no-skill baseline
