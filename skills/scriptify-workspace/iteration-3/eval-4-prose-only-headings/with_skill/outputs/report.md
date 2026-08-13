Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-3/eval-4-prose-only-headings/with_skill/workspace/prose-only-reviewer/`
(skill name: `link-checker`). Writable, user-owned, outside every plugin cache -- eligible.
`git status` shows the SKILL.md is untracked rather than modified, so there is no uncommitted edit to
lose; I still copied it to `.delegation-review/SKILL.md.orig` as the restore point.

Transient files live in `<RUN_DIR>/scratch/.delegation-review/`, outside the target, so a report-only
run leaves nothing behind in the skill it reviewed.

The skill has no numbered steps, so the inventory anchored on section headings instead: 4 anchors,
0 existing scripts, 0 references, ~153 tokens of body. Heading-fallback is not "nothing to delegate" --
every body-bearing heading is a candidate and every one gets a row below.

`sample_target_data.py` exited 1: the target ships no data of its own -- no `docs/` tree, no fixtures,
no `assets/`. So the two proposed interfaces are written against the user's own docs root passed as
argv, not against a bundled fixture, and there is no planted malformed file to point at. The one
finding the target's own text does produce is in the Gotchas section: anchor-only links (`#section`)
must be skipped, which is a rule `collect_links.py` has to implement rather than a step of its own.

## Delegation review: link-checker

**Verdict:** 2 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | walking docs/ for .md files and pulling each relative link with its file and line is a fixed parse; two runs must produce the identical inventory | `python3 scripts/collect_links.py docs/ --out .link-check/links.json` -> counts only: files scanned, links found, anchor-only links skipped, exit 0 links found / 1 no markdown files under the root / 2 usage or unreadable root |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | a link is broken exactly when its resolved path is absent from disk; the counts are arithmetic, so no run should differ | `python3 scripts/resolve_links.py .link-check/links.json --out .link-check/broken.json` -> broken count / total count, then one line per broken link: source:line -> target, exit 0 all links resolve / 1 broken links found / 2 usage or unreadable input |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | the release deadline arrives from the conversation, not from disk, so reasonable runs should rank the same broken links differently; resolve_links.py already supplies the candidate list and exit 1 gates whether this step runs at all | - |
| s4 | "Gotchas" (L25-27) | heading-fallback | 22 | CLAUDE | reference prose, not a workflow step; its anchor-only rule belongs inside collect_links.py, and the section itself stays prose the reader reads | - |

## What the two scripts buy

`collect_links.py` and `resolve_links.py` split at the point where the data changes shape: one walks
the tree and emits an inventory, the other tests each entry against the filesystem. Keeping them
apart makes `resolve_links.py`'s exit code the gate for step s3 -- exit 0 means nothing is broken and
the run stops without Claude weighing anything, exit 1 means there is a candidate list to judge.
Both send their bulk to `--out` and keep only counts on stdout, so a large docs tree does not trade
prose tokens for output tokens.

`s3` stays CLAUDE with no mechanical shell left to strip: the shell -- enumerate the broken links,
count them, order them -- is exactly what `resolve_links.py` already returns. What remains is the
deadline trade-off, which only the conversation supplies.

## Nothing has been written

You asked for the review only, so the target is untouched: no `scripts/` folder, no SKILL.md rewrite,
no fixtures. Say the word and I will apply the two SCRIPT rows -- write both scripts, smoke-test them
against a temporary docs tree, and rewrite the two step sections into exact command invocations.

After that, run `skillit:review` on the target as a final check.
