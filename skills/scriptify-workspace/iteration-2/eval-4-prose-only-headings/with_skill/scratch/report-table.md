## Delegation review: link-checker

**Verdict:** 2 of 3 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | glob + regex extraction of relative link targets with file and line; pure function of the docs tree, two runs must not differ | `python3 scripts/collect_links.py docs/ --out .link-check/links.json` -> counts: files scanned, links found, anchor-only links skipped, exit 0 links found / 1 no markdown files found / 2 usage |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | path-existence check plus a tally; the correct output is fully determined by links.json and the filesystem | `python3 scripts/resolve_links.py .link-check/links.json --json` -> JSON {total, broken_count, broken:[{source,line,target}]}, exit 0 no broken links / 1 broken links found / 2 usage |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | weighing each broken link against the docs owner's release deadline; the deadline arrives in conversation and reasonable runs should rank differently. Mechanical shell already stripped: s2's script enumerates and structures the candidates | - |
