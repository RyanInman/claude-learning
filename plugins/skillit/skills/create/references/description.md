# Writing the description (the router)

The description is the only skill text loaded at startup, and it alone decides whether the body ever loads. Roughly 100 tokens decide whether 5,000 fire. Claude's observed failure mode is under-triggering: it will not reach for a skill unless the match is obvious.

## Rules

1. Write in third person: "Transforms...", "Reviews...", "Builds...".
2. State what the skill does AND when to use it. Both live here - Claude never sees the body until after the trigger decision, so "when to use" content in the body is dead weight.
3. Pack in verbatim trigger phrases, casual included: "turn this into a skill", "why won't my skill fire". Their value is that they match what users actually type - do not sanitize them into formal prose.
4. Cover implicit asks: "even if they don't say 'dashboard'".
5. Add negative triggers for near-miss cases: "Do NOT use for X (use [other-skill] instead)." One skill, one job - overlapping skills make the wrong body load.
6. Err pushy. A description that over-explains its triggers costs a few tokens; one that under-explains wastes the whole skill.
7. Stay within limits: 1024 characters max, non-empty.

Every sentence-level style rule is suspended inside the description. Triggering reliability outranks style.

## Testing the router

Test before and after writing the body:

1. Ask a fresh subagent, with only the description visible: "When would you use this skill?" It quotes the description back, exposing missing keywords.
2. Draft 8-10 realistic user phrasings (formal, casual, typo-ridden, implicit). Check each against the description by asking a subagent whether it would trigger. Target: the skill fires on 8 of 10 relevant phrasings.
3. Draft near-miss phrasings that share keywords but need a different tool. If they would trigger, add negative triggers.

Make the phrasings concrete, because abstract prompts test nothing: file names, column names, a sentence of backstory, lowercase, abbreviations. "ok so my boss sent me this xlsx (Q4 sales final FINAL v2.xlsx) and wants a margin column" beats "Format this data".

## Naming

- Lowercase letters, numbers, hyphens; 64 characters max; must not contain "anthropic" or "claude".
- Prefer gerund or action names (`processing-pdfs`, `create-release-notes`) over vague ones (`helper`, `utils`, `docs`).
- In Claude Code the directory name becomes the `/command`, so name the directory what the user should type.
