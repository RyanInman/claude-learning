---
name: mining-implementation-patterns
description: >
  Studies completed feature branches alongside their requirements (pasted
  text or an Azure DevOps / Jira ticket URL) and distills how a codebase
  implements features into three deliverables: an overview.md of findings
  and patterns, a plain-prose patterns-research findings doc per branch,
  and path-scoped rule files. Use this skill whenever the user wants to
  learn from past branches, PRs, commits, or diffs; mine or
  reverse-engineer conventions from git history; map requirements or
  tickets to code changes; "train" Claude on how features get built in a
  repo; or compile learnings from several branches into research notes or
  rules — trigger on phrases like "learn from this branch", "analyze these
  diffs against the ticket", "write up findings from our past work",
  "update the patterns-research notes with what we learned from this
  branch", or "build rules from our git history". Do NOT use to review an
  open PR (use code-review), implement a new feature (this skill only
  studies history, it doesn't write new code), or document a codebase's
  current architecture/conventions (use extract-patterns).
---

# Mining Implementation Patterns

Turn finished work into reusable guidance. Each **learn** run studies one
branch: requirements on one side, commits and diffs on the other, and writes
a structured per-branch analysis. A **compile** run merges every studied
branch into three deliverables: `overview.md`, a plain-prose
patterns-research findings doc per branch, and path-scoped rule files. All
state lives in `.pattern-mining/` at the repo root, so branches can be
studied one at a time over weeks and recompiled at any point.

## Workspace layout (create on first use)

```
<repo>/patterns-research/
└── <branch-slug>.md              # plain-prose findings doc for this branch

<repo>/.pattern-mining/
├── branches/<branch-slug>/       # one folder per studied branch
│   ├── requirements.md           # the ticket / requirement list
│   ├── extract.json              # deterministic git data (script output)
│   └── analysis.md               # the learnings for this branch
├── index.json                    # cross-branch stats (script output)
└── output/
    ├── overview.md
    └── rules/<scope-slug>.md
```

`<branch-slug>` = branch name with `/` replaced by `-` (e.g.
`feature/sso-login` → `feature-sso-login`). On first use, add
`.pattern-mining/` to `.gitignore` (or commit it deliberately if the team
wants shared learnings) — the extract script excludes it from analysis
either way. `patterns-research/` is the human-facing output and is meant
to be committed.

## Platform notes

- Paths in this doc use forward slashes throughout; Python and Claude
  Code's file tools accept them on Windows too, no conversion needed.
- Scripts are invoked with `python3`. On Windows, use `python` instead if
  `python3` isn't on PATH.
- Set `AZURE_DEVOPS_PAT` / `JIRA_EMAIL` / `JIRA_API_TOKEN` however your
  shell sets env vars: `export VAR=value` (macOS/Linux/Git Bash),
  `$env:VAR="value"` (PowerShell), or `set VAR=value` (cmd.exe).

## Mode selection

- "learn / analyze / study branch X against these requirements" → **Learn**
- "compile / aggregate / regenerate the outputs" → **Compile**
- If the user supplies a branch and asks for the outputs in the same
  request, run Learn then Compile.

## Learn mode (once per branch)

1. **Capture requirements** into `branches/<slug>/requirements.md`:
   - Pasted text → save verbatim, then add a `## Normalized requirements`
     section listing each requirement as `R1`, `R2`, ... (atomic, testable
     phrasing). These IDs anchor traceability later.
   - Ticket URL → if an ADO/Jira MCP connector is available, fetch through
     it; otherwise run
     `python3 scripts/fetch_ticket.py --url <url> --out branches/<slug>/requirements.md`
     (needs `AZURE_DEVOPS_PAT`, or `JIRA_EMAIL` + `JIRA_API_TOKEN`, as env
     vars — the script's errors say exactly what is missing). Then add the
     `## Normalized requirements` section the same way.
2. **Extract git data** — run:
   `python3 scripts/extract_branch.py --repo <repo> --head <branch> --out <repo>/.pattern-mining/branches/<slug>/extract.json`
   (`scripts/` resolves against this skill's folder, the workspace against
   the repo root — anchor both paths before running.)
   Add `--base <ref>` only when the script cannot find a merge-base or the
   branch was squash-merged (then pass `--head <merge-commit> --base <merge-commit>^`).
3. **Study the change.** Read `extract.json` for the shape of the work
   (commit sequence, directory histogram, per-file stats), then read the
   truncated diffs it contains. For the commits that carry the core of the
   feature, view full patches with `git show <sha>` — the JSON truncates
   long diffs by design. For each normalized requirement, decide whether
   the diffs actually fulfill it, partially fulfill it, or don't touch it
   at all — the traceability table in the next step follows this call, it
   doesn't make it.
4. **Write `analysis.md`** following `references/analysis-guide.md`
   exactly — the frontmatter there is machine-read by the compile step, so
   the format is load-bearing, and its Traceability table requires a
   fulfilled/partial/not-fulfilled status per requirement, not just a
   commit/file mapping. Before writing, list pattern IDs already
   used by earlier branches (use the Grep tool for `id:` across
   `.pattern-mining/branches/*/analysis.md` and dedupe the matches — this
   works the same on every platform, unlike a shell `grep | sort -u` pipe)
   and reuse an existing ID whenever the same pattern recurs; recurrence
   counting depends on shared IDs.
5. **Validate and report** — run
   `python3 scripts/compile_index.py --workspace <repo>/.pattern-mining`
   and check its warnings: a zero-pattern warning means the analysis.md
   frontmatter did not parse — fix it before moving on. Then report to
   the user from its output: branches studied so far, patterns confirmed
   (recurring in ≥2 branches), patterns still single-occurrence.

## Compile mode (rerun whenever the corpus grows)

All three deliverables are fully regenerated every compile — reports, not
hand-edited artifacts. Durable corrections belong in the per-branch
`analysis.md` files (see Gotchas), not in the compiled output.

1. Run:
   `python3 scripts/compile_index.py --workspace <repo>/.pattern-mining`
   This aggregates every `extract.json` and every `analysis.md` frontmatter
   into `index.json` (directory touch frequency, files seen in multiple
   branches, source↔test pairing rate, pattern-ID recurrence).
2. Read `index.json` and every `branches/*/analysis.md` in full.
3. Write the three deliverables using the templates and promotion rules in
   `references/output-templates.md`. The promotion rules decide what is
   confirmed enough to state as fact in `overview.md` versus flagged as an
   open observation.
   - `overview.md` and `output/rules/*.md`: overwrite in full.
   - `patterns-research/<branch-slug>.md`, one per branch in the corpus:
     overwrite in full — a plain-prose write-up of that branch's own
     findings (standard steps, conventions, examples, gotchas,
     traceability summary), noting where a pattern also recurs elsewhere
     in the corpus. Not a SKILL.md and not meant to be loaded as a skill —
     just readable research notes for an engineer about to work on
     similar code.
4. For rule files, pick the target format with the user per
   `references/rule-formats.md`, then offer to install them (e.g. copy a
   rule into `src/api/CLAUDE.md`).
5. Append one line to the `## Compile log` section of `overview.md`: date,
   corpus size, and what changed.

## Example

**Input:** "Learn from branch `feature/sso-login`, ticket says: 1) users
can sign in with Okta, 2) failed logins are audit-logged."

**Learn output (excerpt of `analysis.md` frontmatter):**

```yaml
branch: feature/sso-login
patterns:
  - id: endpoint-adds-validator-and-spec
    scope: src/api/**
    claim: Every new endpoint lands with a FluentValidation validator and a matching *.spec.ts in tests/api, in the same commit.
    evidence: [a1b2c3d, e4f5a6b]
```

**Compile output (excerpt of `overview.md`):** a pattern table row —
`endpoint-adds-validator-and-spec | confirmed (3/4 branches) | src/api/**`
— plus the same pattern appearing in `patterns-research/feature-sso-login.md`
and as a bullet in `output/rules/src-api.md`.

## Gotchas

- Deleted or squash-merged branches have no branch ref; extraction still
  works against the merge commit (`--head <merge-sha> --base <merge-sha>^`
  for squash merges, since the squash commit contains the whole change).
- `extract_branch.py` excludes lockfiles, vendored, and generated files by
  default because they dominate line counts and drown real signal; pass
  `--include-generated` only if generated output is itself the pattern.
- Commits usually contain work beyond the ticket (drive-by fixes,
  formatting). Record those under `unmapped` in the traceability table
  rather than forcing every change onto a requirement — forced mappings
  poison the compiled patterns.
- A requirement appearing in `requirements.md` doesn't mean the branch
  delivered it — tickets describe intended scope, not necessarily shipped
  scope. Judge fulfilled/partial/not-fulfilled from what the diffs do, not
  from the ticket text, before mapping any code to it; citing files
  against a requirement they don't actually satisfy is the same poison as
  forcing unrelated commits onto one.
- Keep `analysis.md` self-contained prose with commit/path citations;
  never paste raw diff hunks or `extract.json` bodies into it, because the
  compile step reads every analysis in full and bloated analyses blow the
  context budget as the corpus grows.
- Single-occurrence patterns stay marked *observed once* in `overview.md`,
  not promoted to Confirmed; a convention seen once may be one developer's
  habit. The thresholds in `references/output-templates.md` are the
  contract.
- `overview.md`, the rule files, and every `patterns-research/*.md` doc
  are fully regenerated every compile; hand-edits to any of them are lost
  on the next run. Durable corrections that should survive every compile
  belong in the per-branch `analysis.md` files, which do survive.

## Reference files

- Read `references/analysis-guide.md` when writing any `analysis.md`
  (lenses to apply, evidence discipline, exact frontmatter format).
- Read `references/output-templates.md` when compiling (templates for all
  three deliverables + promotion thresholds).
- Read `references/rule-formats.md` when emitting or installing
  path-scoped rules (Claude Code nested CLAUDE.md, Cursor .mdc, generic).
