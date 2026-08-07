# Scriptify classification — `prose-only-reviewer` (SKILL.md name: `link-checker`)

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-4-prose-only-headings/without_skill/workspace/prose-only-reviewer/SKILL.md`

Nothing was changed. Analysis only.

## How the steps were identified

The skill has no numbered steps and no `## Step N` headings. Its workflow is carried entirely by prose `##` headings. Each `##` section below `# Link Checker` is therefore treated as one workflow step (heading fallback). Four sections exist; three are workflow steps and one (`Gotchas`) is a constraint that attaches to a step rather than standing alone. This is not a "0 steps extracted" case — the absence of numbering is a formatting choice, not an absence of work.

## Classification table

| # | Step (heading) | Class | Why | Proposed interface |
|---|---|---|---|---|
| 1 | Collect the link inventory | SCRIPT | Walking `docs/**/*.md`, regexing out link targets, and recording source file + line number is fully deterministic. No judgment. Re-deriving the parse in prose each run is the main source of run-to-run variance. | `scripts/collect_links.py <docs_dir> [--json]` → stdout JSON array of `{source_file, line, raw_target, kind}` where `kind` is `relative` \| `anchor` \| `external`. Exit `0` = inventory produced (even if empty), `1` = bad usage, `2` = `docs_dir` missing or unreadable. |
| 2 | Resolve each target | SCRIPT | Path-existence checks and count arithmetic are mechanical and error-prone done by hand across many links. Deterministic given the same tree. Also renders the "broken vs total" summary line. | `scripts/resolve_links.py <docs_dir> [--inventory <path>] [--format json\|table]` → per-link `{source_file, line, target, resolved_path, status: ok\|broken\|skipped}` plus summary `{total, broken, skipped}`. Exit `0` = no broken links, `1` = broken links found, `2` = usage/IO error. Nonzero-on-findings lets SKILL.md branch without re-parsing output. |
| 3 | Decide what to fix now | CLAUDE | Requires weighing each broken link against the docs owner's release deadline — an input that changes every run and is not encoded in the repo. Ranking by impact and deadline pressure is judgment, not computation. Stays prose, fed by step 2's JSON. | — |
| 4 | Gotchas (anchor-only links) | SCRIPT (folded into step 1) | "Skip `#section` links" is a fixed, testable rule. As prose it is a reminder the model may forget; as code it is enforced once. Not a standalone step, so it belongs inside `collect_links.py` as `kind: anchor` and should shrink in the prose to one line describing script behavior. | — |

## Summary

- SCRIPT: `Collect the link inventory`, `Resolve each target` (plus the `Gotchas` rule folded into the first script).
- CLAUDE: `Decide what to fix now`.
- HYBRID: none. Steps 1 and 2 carry no judgment; step 3 carries no deterministic residue beyond data step 2 already produces.

Suggested split: two scripts rather than one. Collection is the parser, resolution is the filesystem check; keeping them apart makes each independently testable and lets resolution rerun after fixes without re-parsing. A single `check_links.py` doing both is also defensible if the raw inventory is never needed on its own.

## Post-delegation shape of SKILL.md

Steps 1 and 2 collapse to script invocations plus a sentence on reading the exit code. Step 3 stays prose and gains an explicit instruction to read the JSON summary instead of re-scanning `docs/`. Expected effect: lower token cost per run and identical broken-link counts across runs, with variance confined to the fix-order recommendation, where it belongs.
