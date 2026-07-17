# Path-Scoped Rule Targets

The compile step always emits generic rule files into
`output/rules/` first (frontmatter `paths:` glob + bullets). Installation
into a consumer format is a copy/transform of those. Ask the user which
consumer(s) they use; when unstated and the repo shows evidence of one
(`.cursor/` folder, existing `CLAUDE.md`), propose that one.

## Claude Code — nested CLAUDE.md

Claude Code automatically pulls in a `CLAUDE.md` that sits in a directory
when working with files under it. Install by merging rule bullets into
`<scope-dir>/CLAUDE.md` (create if absent), dropping the frontmatter, and
keeping the `derived_from` line as an HTML comment so future compiles can
find and refresh their own section:

```markdown
<!-- derived_from: mining-implementation-patterns 2026-07-16 -->
## Conventions (learned from past branches)
- Every new endpoint ships with a validator and matching *.spec.ts ...
```

Refresh rule: on later installs, replace only the block between the marker
comment and the next heading; hand-written content elsewhere in the file
stays untouched.

## Cursor — .cursor/rules/*.mdc

One `.mdc` per scope, glob in frontmatter:

```markdown
---
description: API layer conventions learned from past branches
globs: ["src/api/**"]
alwaysApply: false
---
- Every new endpoint ships with a validator and matching *.spec.ts ...
```

## Generic / other harnesses

Hand over `output/rules/*.md` as-is; the `paths:` frontmatter is a common
denominator most rule-loading systems can be adapted to. For harnesses
with a single global rules file, concatenate the rule files under
per-scope headings and note the glob in each heading.

## Choosing scope granularity

Prefer the narrowest glob the evidence supports (`src/api/**` over
`src/**`). Merge scopes only when their rule sets are identical. A rule
true repo-wide belongs in the generated skill's workflow or the repo-root
CLAUDE.md instead of a scoped file — repo-wide scoped files just duplicate
loading.
