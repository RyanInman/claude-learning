# Choice point

Reached after delivering the report. The prompt said "Report only for now, don't change anything",
so I stopped here and wrote nothing into the skill folder.

## Question I would have asked

> I found three steps worth scripting (topic normalization, word counting + thin flag, index table
> rendering) and one data-loss bug (step 2 discards the source URL that step 7 needs). Want me to
> build them?

## Options I would have offered

1. **Build both scripts** — write `scripts/normalize_topics.py` and `scripts/index_report.py`, then
   rewrite steps 1, 4, 5, and 7 of SKILL.md to call them.
2. **Build the topic normalizer only** — the highest-value, lowest-risk one, since duplicate topics
   currently cause wasted fetches with no visible error.
3. **Fix the URL gap first** — amend step 2 to save `sources/<slug>.json` with the URL, since the
   index table cannot be scripted correctly until the URL is recorded somewhere.
4. **Nothing yet** — keep the report, decide later.

## What I did instead

Obeyed the prompt: report only. No files were created or modified inside
`workspace/research-brief-writer/`.
