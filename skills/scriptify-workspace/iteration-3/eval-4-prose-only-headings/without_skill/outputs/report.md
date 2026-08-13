# Which parts of `prose-only-reviewer/` should be scripts

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-3/eval-4-prose-only-headings/without_skill/workspace/prose-only-reviewer/SKILL.md` (skill `name: link-checker`, 28 lines, no bundled files).

Nothing changed. This is the analysis only.

## Verdict per section

| Section | Verdict | Reason |
| --- | --- | --- |
| Frontmatter (`name`, `description`) | Stays prose | Trigger text. Never executable. |
| `# Link Checker` intro | Stays prose | One-line statement of purpose. |
| `## Collect the link inventory` | **Script** | File walk plus regex extraction plus line numbering. Pure mechanics with one right answer. |
| `## Resolve each target` | **Script** | Path join, normalize, `exists()` check, two counters. Pure mechanics with one right answer. |
| `## Decide what to fix now` | Stays prose | Weighs broken links against a release deadline. Judgment against context the script cannot see. |
| `## Gotchas` | Stays prose, rule moves into the script | The skip-anchors rule is an input filter, so the script must enforce it. The section stays as the human-readable reason. |

Two of the four body sections should become one script. The split is clean: the first two sections are the same pass over the same files, and the last two are the parts that need a reader.

## The one script to add

One script, not two. "Collect" and "resolve" walk the same files in the same pass, so splitting them buys nothing and forces an intermediate file format that both halves then have to agree on.

`scripts/check_links.py`

- Input: `python3 scripts/check_links.py <docs_root>` (default `docs/`).
- Output: JSON on stdout.

```json
{
  "docs_root": "docs",
  "total_links": 214,
  "broken_count": 7,
  "broken": [
    {"source": "docs/guides/setup.md", "line": 42,
     "target": "../api/tokens.md", "resolved": "docs/api/tokens.md"}
  ]
}
```

- Exit code: `0` when it ran, regardless of how many links are broken. Reserve a non-zero exit for a missing or unreadable `docs_root`, so a broken link never looks like a crash.

The script owns these rules, each of which the current prose either states loosely or omits:

1. Skip anchor-only targets (`#section`). The skill already says this.
2. Skip absolute URLs and non-file schemes (`http:`, `https:`, `mailto:`, `//`). The skill says "relative links" but never says how to exclude the rest.
3. Strip a trailing anchor before resolving (`../guide.md#setup` resolves as `../guide.md`). The skill does not mention this, and it is the most likely source of false positives.
4. Resolve relative to the source file's own directory, not to `docs/`.
5. Match every markdown link form: inline `[a](b)`, image `![a](b)`, and reference definitions `[a]: b`. The prose says "each relative link" and leaves the forms to be guessed.

Points 2 through 5 are the real argument for the script. Each is a decision the prose currently leaves to the reader, so two runs of the same skill can return different broken counts on the same folder. A script fixes the answer.

## What SKILL.md becomes

- `## Collect the link inventory` and `## Resolve each target` collapse into one step that runs the script and reads its JSON.
- `## Decide what to fix now` keeps its full prose and gains one line: it reads the `broken` array as its input.
- `## Gotchas` keeps the anchor entry as the explanation of a rule the script now enforces, and gains the trailing-anchor case.

Estimated body size after the change: roughly 20 lines, down from 28, with the variance removed rather than moved.

## What I would not script

`## Decide what to fix now` is the whole reason this skill is a skill. It reads a deadline, ranks broken links by how much they hurt, and picks a subset. A script would have to invent a priority formula that nobody asked for, and it would be wrong the first time the deadline moved. Leave it in prose.
