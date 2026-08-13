## Delegation review: link-checker

**Verdict:** 2 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | walking docs/ for .md files and pulling each relative link with its file and line is a fixed parse; two runs must produce the identical inventory | `python3 scripts/collect_links.py docs/ --out .link-check/links.json` -> counts only: files scanned, links found, anchor-only links skipped, exit 0 links found / 1 no markdown files under the root / 2 usage or unreadable root |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | a link is broken exactly when its resolved path is absent from disk; the counts are arithmetic, so no run should differ | `python3 scripts/resolve_links.py .link-check/links.json --out .link-check/broken.json` -> broken count / total count, then one line per broken link: source:line -> target, exit 0 all links resolve / 1 broken links found / 2 usage or unreadable input |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | the release deadline arrives from the conversation, not from disk, so reasonable runs should rank the same broken links differently; resolve_links.py already supplies the candidate list and exit 1 gates whether this step runs at all | - |
| s4 | "Gotchas" (L25-27) | heading-fallback | 22 | CLAUDE | reference prose, not a workflow step; its anchor-only rule belongs inside collect_links.py, and the section itself stays prose the reader reads | - |
