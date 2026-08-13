# Choice point

The prompt said "report only for now, don't change anything", so I stopped here and wrote nothing
into `workspace/research-brief-writer/`. Below is the question I would have asked the user next.

**Question:** I found three steps worth converting to scripts. Which do you want me to build?

**Options:**

1. **Both scripts (recommended)** — Add `scripts/parse_topics.py` for step 1 and
   `scripts/index_report.py` for steps 4, 5, and 7, then rewrite those steps in `SKILL.md` to call
   them. Covers every deterministic step in the workflow.

2. **Step 1 only** — Add `scripts/parse_topics.py` and rewrite step 1. Fixes the case-differing
   duplicate that costs a wasted WebFetch, and leaves the rest of the skill untouched.

3. **Steps 4 and 7 only** — Add `scripts/index_report.py` and rewrite steps 4, 5, and 7. Keeps every
   fetched HTML page out of the context window, which is the larger token saving.

4. **Nothing yet** — Keep the report and decide later.
