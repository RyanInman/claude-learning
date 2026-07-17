---
name: reverse-engineering-specs
description: >
  Reverse-engineers already-implemented code -- a file, directory, module,
  feature area, or a diff/branch -- into a spec.md of numbered Requirements
  and testable Acceptance Criteria, inferred from what the code actually
  validates, branches on, and handles as edge cases. Use this skill whenever
  the user wants to back out a spec, requirements, or acceptance criteria
  from existing code; asks things like "write AC for this module", "what
  does this code actually require", "spec out what this feature does",
  "reverse engineer requirements from this implementation", or wants a
  testable requirements doc for undocumented legacy code -- even if they
  don't say "spec" explicitly. Do NOT use to mine cross-branch coding
  conventions or generate a reusable implementation skill from git history
  (use mining-implementation-patterns), to document a codebase's overall
  architecture or conventions (use extract-patterns), or to author a
  forward-looking design doc or PRD from a conversation or new idea (use
  rfc-writer or to-prd).
---

# Reverse-Engineering Specs

Turns already-working code into a testable spec. Reads a target -- a path,
module, or feature area at its current state, or a diff/branch -- and writes
a single `spec.md` of numbered Requirements with per-requirement Acceptance
Criteria, plus flagged assumptions and open questions for human review.
Unlike a forward spec written before code exists, every requirement here
must trace to a file:line, branch, or test in the real implementation --
this is documentation of what *is*, not a proposal for what should be.

## Workspace layout (create on first use)

```
<repo>/.reverse-spec/<target-slug>/
├── scan.json          # deterministic code-scan output (script)
└── spec.md            # the finished spec -- the deliverable
```

`<target-slug>` = the target path or branch name with `/` and other
non-alphanumeric characters replaced by `-` (e.g. `src/api/billing` →
`src-api-billing`, `feature/sso-login` → `feature-sso-login`). Add
`.reverse-spec/` to `.gitignore` unless the team wants scan snapshots kept
around. `spec.md` is meant to leave this folder once finished -- offer to
copy it to wherever the team keeps specs (e.g. `docs/specs/`) as the last
step.

## Platform notes

- Paths in this doc use forward slashes throughout; Claude Code's file
  tools and Python accept them on Windows too.
- Scripts are invoked with `python3`. On Windows, use `python` instead if
  `python3` isn't on PATH.
- `scan_code.py --repo` defaults to `.`; pass it explicitly (either mode)
  when not running from the repo root.

## Mode selection

- "reverse engineer this file/module/directory into a spec", "what are the
  requirements for X", "write AC for the existing code in Y" → **Snapshot
  mode** (the target's current state).
- "reverse engineer this diff/branch/PR into a spec", "what requirements
  does this change add" → **Diff mode** (only what a change introduced).
- If the user gives both a path and a branch, run Diff mode scoped to that
  path (`--target` alongside `--head`/`--base`).

## Snapshot mode (spec for a target's current behavior)

1. **Scan the target** — run:
   `python3 scripts/scan_code.py --target <path> --out .reverse-spec/<slug>/scan.json`
   This inventories files under `<path>`, extracts language-agnostic
   signatures (functions/classes/routes), flags validation/error-handling
   signals, pairs source files with their tests, and includes a truncated
   excerpt around each signature so real behavior -- not just a name -- is
   visible.
2. **Read `scan.json`.** For any excerpt cut off mid-branch, or any file
   whose behavior is unclear from the excerpt alone, open it directly with
   Read — the scan is a map, not a substitute for reading the logic that
   matters.
3. **Apply the six lenses** in `references/inference-guide.md` to turn
   observed behavior into numbered requirements and Given/When/Then
   acceptance criteria.
4. **Write `spec.md`** following `references/spec-format.md` exactly.
   Every requirement cites a `path:line` or test name; anything inferred
   without a direct citation goes in Open Questions, not the Requirements
   table.
5. **Report** to the user: requirement count, how many are `high`
   confidence vs. `medium`/`low`, and the open-questions count.

## Diff mode (spec for what a change added)

1. **Scan the diff** — run:
   `python3 scripts/scan_code.py --head <branch> --out .reverse-spec/<slug>/scan.json`
   Add `--base <ref>` only when the script can't find a merge-base or the
   branch was squash-merged (pass `--head <merge-commit> --base <merge-commit>^`).
   Add `--target <path>` to scope a wide branch to one area.
2. **Read `scan.json`.** Its `diffs` map shows what changed; its
   `signatures`/`behavior_signals` are extracted from the post-change
   (`--head`) content, so they describe the resulting behavior, not just
   the diff text. Open a file directly if a diff excerpt is truncated where
   the interesting change is.
3. **Apply the lenses**, per `references/inference-guide.md` §4: describe
   only what the change added or altered, citing the commit alongside the
   file:line — a requirement the diff didn't touch doesn't belong in this
   spec.
4. **Write `spec.md`** — same template and rules as Snapshot mode.
5. **Report** the same way as Snapshot mode step 5.

## Example

**Input:** "Reverse engineer `src/api/auth/OktaValidator.py` into a spec."

**Snapshot scan (excerpt of `scan.json`):**

```json
{
  "path": "src/api/auth/OktaValidator.py",
  "paired_test": "src/api/auth/OktaValidator.spec.ts",
  "signatures": [{"kind": "function", "name": "validate_token", "line": 40, "excerpt": "..."}],
  "behavior_signals": [
    {"keyword": "raise", "line": 42, "text": "raise ExpiredTokenError(...)"},
    {"keyword": "raise", "line": 47, "text": "raise InvalidIssuerError(...)"}
  ]
}
```

**spec.md output (excerpt):** a Requirements table row —
`R1 | Rejects an expired token | high | OktaValidator.py:42, OktaValidator.spec.ts`
— plus a matching `### R1` Acceptance Criteria section with a Given/When/Then
bullet citing the same evidence. Full worked example in
`references/spec-format.md` §4.

## Gotchas

- A paired test proves the requirement, but the requirement is what the
  test *asserts*, not the fact that a test exists — cite the specific
  assertion, not "has a test."
- Absence of validation for a case is not evidence the case is out of
  scope. Flag silently-unhandled edge cases in Open Questions rather than
  omitting them entirely or inventing a requirement the code doesn't
  actually enforce.
- `scan_code.py`'s signature and diff extraction is regex-based, not a real
  parser — it will miss unusual syntax and occasionally mislabel a
  signature. Treat every hit as "worth reading," not as verified fact;
  confirm anything load-bearing by opening the file.
- Excerpts and diffs are truncated under a per-file/total budget so
  `scan.json` stays readable in one pass. If a truncation marker hides the
  actual branching logic, open the file (or `git show`) directly rather
  than guessing from the signature line alone.
- A file with `signatures_truncated: true` hit the per-file signature cap
  (very large or generated-looking files) — some of its interface was
  never scanned. Note this as an Open Question rather than treating that
  file's requirement list as complete.
- `scan_code.py` excludes lockfiles, vendored, and generated files by
  default because they inflate signature counts without carrying behavior
  signal; pass `--include-generated` only if that generated output is
  itself the target.
- `spec.md` is an inferred spec, not a verified one — it exists to be
  reviewed by a human before anyone treats it as ground truth. Keep Open
  Questions honest rather than resolving uncertainty by assumption.

## Reference files

- Read `references/inference-guide.md` when turning `scan.json` (plus any
  source you opened directly) into requirements — the six lenses, evidence
  discipline, and confidence levels.
- Read `references/spec-format.md` when writing `spec.md` — the exact
  template, field rules, and acceptance-criteria style.
