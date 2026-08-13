## Delegation review: link-checker

**Verdict:** 2 of 4 steps become pure script invocations. Replacing the 2 SCRIPT step(s) removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | walking docs/ and recording each relative link with file and line is a function of the tree on disk; two runs must not differ | `python3 scripts/check_links.py docs/ --json --out .link-check/links.json` -> counts summary: total links, broken count, files scanned, exit 0 no broken links / 1 broken links found / 2 usage or missing docs dir |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | existence check per target path plus two tallies; the unit test writes itself, and it shares one pass over the tree with s1 | `python3 scripts/check_links.py docs/ --json --out .link-check/links.json` -> counts summary: total links, broken count, files scanned, exit 0 no broken links / 1 broken links found / 2 usage or missing docs dir |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | ranks broken links against a release deadline stated in conversation, which no script can see; reasonable runs should differ here. s1/s2's JSON is already the candidate list, so a second script would only re-hand Claude what it must read anyway | - |
| s4 | "Gotchas" (L25-27) | heading-fallback | 22 | CLAUDE | reference prose, not a workflow step | - |

### One script covers both SCRIPT rows

`check_links.py` walks `docs/`, records every relative link with its source file
and line, resolves each target against the filesystem, and emits both the
inventory and the broken/total tallies from a single pass. s1 and s2 describe
the two halves of that pass, so splitting them into two scripts would walk the
tree twice and hand Claude an intermediate file nothing reads.

The step-25 gotcha (skip anchor-only `#section` links) is a rule the script
encodes, not a step Claude re-applies. Fold it into `check_links.py` and delete
the prose reminder from the rewritten SKILL.md, because a rule stated in two
places drifts.

### Why s3 stays prose

s3 is the one step where two runs should disagree. The release deadline it
weighs against arrives in conversation, and no script can read it. A helper
that sorted or grouped the broken links would only re-hand Claude the list it
must read in full anyway, so it would add an invocation and remove no
reasoning. `check_links.py --json` already delivers the candidate list; s3
consumes it.

### Findings from the target itself

- The target ships **no data of its own** — `sample_target_data.py` exited 1,
  no `docs/` fixture tree, no sample links. Every expectation for
  `check_links.py` would therefore be written against a fixture tree that does
  not exist yet, so applying these rows means authoring fixtures first: at
  minimum one resolving link, one broken link, and one anchor-only link that
  must not be counted broken.
- The frontmatter `name` is `link-checker`, but the folder is
  `prose-only-reviewer`. The name and the directory must match for the skill to
  load. Fix that independently of this review.
- The target has no numbered steps, so the inventory anchored on section
  headings. s4 ("Gotchas") is one of those anchors and is reference prose, not
  a workflow step; it is listed for completeness, not as a delegation
  candidate.

### Not changed

Nothing was written into the target. You asked for the assessment only.
