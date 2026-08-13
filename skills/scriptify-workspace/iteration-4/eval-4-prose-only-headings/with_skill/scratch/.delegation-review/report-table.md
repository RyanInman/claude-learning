## Delegation review: link-checker

**Verdict:** 2 of 4 steps become pure script invocations. Replacing the 2 SCRIPT step(s) removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | walking docs/ and recording each relative link with file and line is a function of the tree on disk; two runs must not differ | `python3 scripts/check_links.py docs/ --json --out .link-check/links.json` -> counts summary: total links, broken count, files scanned, exit 0 no broken links / 1 broken links found / 2 usage or missing docs dir |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | existence check per target path plus two tallies; the unit test writes itself, and it shares one pass over the tree with s1 | `python3 scripts/check_links.py docs/ --json --out .link-check/links.json` -> counts summary: total links, broken count, files scanned, exit 0 no broken links / 1 broken links found / 2 usage or missing docs dir |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | ranks broken links against a release deadline stated in conversation, which no script can see; reasonable runs should differ here. s1/s2's JSON is already the candidate list, so a second script would only re-hand Claude what it must read anyway | - |
| s4 | "Gotchas" (L25-27) | heading-fallback | 22 | CLAUDE | reference prose, not a workflow step | - |
