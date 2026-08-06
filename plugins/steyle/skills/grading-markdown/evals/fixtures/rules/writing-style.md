# Writing style

Apply to all written output: prose, documentation, messages, commit text, code comments, guides.

## Core rules (all writing)

- Write in active voice and name the actor. "The parser drops empty rows," not "empty rows are dropped."
- Give each sentence one idea. Avoid "and then" chains.
- Cut filler, hedges, and restatement. "in order to" → "to"; "make use of" → "use"; "note that you may want to cache this" → "cache this."
- Use one term per concept. Do not swap in synonyms for variety, because variety reads as a distinction that isn't there — "config" in one line and "settings file" in the next implies two files.
- Name the specific action and amount. Avoid "handle," "process," "appropriately," "as needed," "various," and "etc.," because each delegates a decision without supplying the information to make it.
- Use the standard term of art. Do not paraphrase a word the reader already knows: write "idempotent," not "runs again with no extra effect."
- Keep grammar flat. Present tense for facts, imperative for steps, at most one subordinate clause per sentence.
- Treat ~20 words as a rewrite alarm for a procedural sentence, not a hard cap. A clear 22-word sentence may stay; a 35-word one rarely does.

## When writing instructions or procedures (docs, guides, runbooks, skills)

- Open each instruction with a command verb. "Read the config first," not "You should read the config first."
- Attach a reason to every non-obvious rule, and skip the reason on obvious steps. Do not write directives in ALL CAPS, because a rule plus its reason lets the reader generalize to cases you didn't anticipate; a bare caps directive doesn't.

## Clarity outranks these rules

Never compress past clarity. If applying a rule forces a reread, restore the words. Keep articles, named actors, reasons, and specific amounts even when they cost length — telegraphic prose trades tokens for ambiguity.

## Worked example

Before:

> You'll want to make sure the data gets cleaned up first — various issues should be dealt with appropriately, and then you can process everything and generate the output, handling errors as needed.

After:

> Clean the data before analysis. Drop empty rows. Then run the analysis. On a parse error, log the row number and continue, because one bad row must not abort a large job.
