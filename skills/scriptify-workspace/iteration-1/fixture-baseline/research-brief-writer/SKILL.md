---
name: research-brief-writer
description: Builds a short research brief for each topic in topics.txt by fetching a source for it, keeping the useful ones, and writing a summary. Use when the user asks for a research brief or a topic roundup.
---

# Research Brief Writer

Turn the topic list into a set of short research briefs, then publish the index
to the team's Notion page.

## Workflow

1. Read the topic list from `topics.txt`, one topic per line. Drop blank lines,
   drop duplicates, and normalize each remaining topic to a lowercase slug.
2. For each topic, fetch the top source for it with WebFetch and save the raw
   page to `sources/<slug>.html`.
3. Ask the user with AskUserQuestion which of the fetched sources to keep for
   the brief. Offer one option per fetched source.
4. Count the words in each kept source. Record any source under 200 words as
   thin.
5. Query the `notion` MCP tool for the id of the page titled "Research Index",
   then append this run's summary block to that page.
6. Write a 200-word brief for each kept topic in the house voice: plain,
   concrete, no marketing language.
7. Render the index table of topic, source URL, and word count, sorted by word
   count descending.
