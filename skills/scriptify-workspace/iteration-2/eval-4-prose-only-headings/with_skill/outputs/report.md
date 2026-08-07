# Delegation review — `prose-only-reviewer` (skill name: `link-checker`)

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-4-prose-only-headings/with_skill/workspace/prose-only-reviewer/`

Nothing was written into the target. The user asked for the classification only.

## Eligibility (Step 0)

Target holds a SKILL.md, is user-owned and writable, and sits outside every
plugin cache path. `git status` reports the file untracked (`??`), not modified,
so no uncommitted-change warning applies. Restore copy saved to
`scratch/.delegation-review/SKILL.md.orig`.

## Inventory (Step 1)

    python3 <scriptify>/scripts/inventory.py workspace/prose-only-reviewer \
      --out scratch/.delegation-review/inventory.json

    steps: 3  existing scripts: 0  references: 0  body: ~153 tokens
    no numbered steps found -- anchored on section headings instead

The target has no numbered steps, so the inventory anchored on section headings
(`origin: heading-fallback`). That is not "nothing to delegate": all three
workflow headings were extracted and every one is classified below. The
`## Gotchas` section is not an anchor and needs no entry.

## Rendered report (Step 3, verbatim from render_report.py, exit 0)

## Delegation review: link-checker

**Verdict:** 2 of 3 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~74 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Collect the link inventory" (L10-14) | heading-fallback | 35 | SCRIPT | glob + regex extraction of relative link targets with file and line; pure function of the docs tree, two runs must not differ | `python3 scripts/collect_links.py docs/ --out .link-check/links.json` -> counts: files scanned, links found, anchor-only links skipped, exit 0 links found / 1 no markdown files found / 2 usage |
| s2 | "Resolve each target" (L15-19) | heading-fallback | 39 | SCRIPT | path-existence check plus a tally; the correct output is fully determined by links.json and the filesystem | `python3 scripts/resolve_links.py .link-check/links.json --json` -> JSON {total, broken_count, broken:[{source,line,target}]}, exit 0 no broken links / 1 broken links found / 2 usage |
| s3 | "Decide what to fix now" (L20-24) | heading-fallback | 34 | CLAUDE | weighing each broken link against the docs owner's release deadline; the deadline arrives in conversation and reasonable runs should rank differently. Mechanical shell already stripped: s2's script enumerates and structures the candidates | - |

## Reasoning per step

**s1 — "Collect the link inventory" -> SCRIPT.**
Walking `docs/**/*.md` and recording each relative link target with its source
file and line number is file discovery plus parsing: two of the rubric's
commonly-delegable categories. The core test asks what stops this from being a
script; nothing does. Two runs over the same tree must produce the identical
inventory, and the unit test writes itself (fixture tree in, exact JSON out).
The Gotchas rule — skip anchor-only `#section` links — is a fixed filter, so it
belongs inside the script, and the script should report how many it skipped so
the rule stays visible. Output can be large on a real docs tree, so it goes to
`--out` with counts only on stdout, per the big-output gotcha.

**s2 — "Resolve each target" -> SCRIPT.**
"Mark a link broken when its target path does not exist on disk" is fixed-rule
validation, and "report the count of broken links alongside the total" is
aggregation. Both are pure functions of `links.json` plus the filesystem.
Splitting it from s1 keeps each heading mapped to one exact invocation and
avoids re-walking the tree. Exit 1 on broken links makes the script gate the
next step (rubric hybrid shape 3: no broken links -> exit 0 -> Claude never
engages).

**s3 — "Decide what to fix now" -> CLAUDE.**
This is the only step where reasonable runs should differ. It weighs each
broken link against the docs owner's release deadline — a fact that arrives in
conversation, not from disk — and picks a subset. Per the rubric, CLAUDE is the
last resort, so the HYBRID decomposition was tried first: can a script
enumerate the candidates, pre-compute the facts, validate the answer, or render
the result? Enumeration and fact-gathering are already fully covered by s2's
`resolve_links.py`, which hands Claude a structured `broken` list. Nothing
mechanical is left inside s3 itself, so adding a script here would encode one
arbitrary priority ordering and dress judgment up as determinism. It stays
prose.

## What the rewrite would look like (not applied)

- s1 -> "Run exactly: `python3 scripts/collect_links.py docs/ --out .link-check/links.json`.
  Exit 1 -> no markdown under `docs/`, stop."
- s2 -> "Run exactly: `python3 scripts/resolve_links.py .link-check/links.json --json`.
  Exit 0 -> no broken links, report clean and stop. Exit 1 -> broken links on stdout."
- s3 -> unchanged prose, now fed by the `broken` array instead of a hand-built list.
- Gotchas -> the anchor-only rule moves into `collect_links.py`; keep one
  sentence noting the script enforces it.

## Follow-ups

No DEAD steps. No existing scripts, so nothing was ALREADY_DELEGATED. After any
future rewrite, run `skillit:review` on the target as a final check.
