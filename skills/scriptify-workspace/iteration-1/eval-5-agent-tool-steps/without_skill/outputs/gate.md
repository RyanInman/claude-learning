# Gate — decisions needed before scripting research-brief-writer

Unattended run. Both questions answered with a default; ratify or override before
any script is written.

## 1. Does dedupe run before or after slug normalization?

SKILL.md step 1 reads "Drop blank lines, drop duplicates, and normalize each
remaining topic to a lowercase slug" — dedupe first. `topics.txt` holds both
`retrieval augmented generation` and `Retrieval Augmented Generation`, so the two
readings disagree on the real input: 5 topics vs 4. The literal reading also emits
`retrieval-augmented-generation` twice, and step 2 would overwrite
`sources/retrieval-augmented-generation.html`.

**Default chosen: normalize, then dedupe → 4 topics.** Collapses the case variant
and removes the collision. Requires rewording step 1.

**Override if** case variants are meant to be treated as separate topics, in which
case the slug scheme needs to disambiguate rather than the dedupe order changing.

## 2. How are words counted for the "under 200 words = thin" rule?

Sources are saved as raw HTML, so the count depends entirely on extraction. On a
195-word article body, four methods gave 226 / 232 / 210 / 197 words — the thin
verdict flips between them.

**Default chosen: parse the HTML, drop `<script>` and `<style>` bodies, count
whitespace-separated tokens over the remaining text.** Stdlib only, no new
dependency.

**Override if** the intent is article-body-only measurement, which is more faithful
to "is this source thin" but needs a readability/extraction dependency and its own
failure modes on unusual markup.
