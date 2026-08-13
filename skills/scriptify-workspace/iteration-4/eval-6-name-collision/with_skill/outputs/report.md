# Scriptify run: docs-linter

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-6-name-collision/with_skill/workspace/docs-linter`
Eligible to write: yes (user-owned, writable, outside every plugin cache). Restore point saved to `.delegation-review/SKILL.md.orig` before any rewrite.

## What the target's own data says

`sample_target_data.py` digested the three markdown files the workflow runs on, and two of them break the level-1 heading rule the workflow exists to catch:

- `docs/tutorial.md` opens with `Some intro prose that arrives before any heading at all.` — it *has* an H1, just not on line 1.
- `docs/reference/api.md` opens with `## API Reference` — it has no H1 anywhere.
- `docs/getting-started.md` is the only compliant file.
- Fenced blocks: getting-started 2, tutorial 1, api 1, total 4.

Those two files are different failures, so the generated script gives them different finding codes. Collapsing them into one `missing_h1` would report `tutorial.md`, which has an H1, as missing one.

One more real finding, outside the workflow: the pre-existing `scripts/check_headings.py` exits 1 on this docs tree, because `docs/reference/api.md` carries `![](diagram.png)` with empty alt text.

## The name collision

`scripts/check_headings.py` already exists. Despite the name it has nothing to do with headings — it checks image alt text, and its docstring says the release pipeline calls it by that exact path. The natural name for step 2's script is therefore taken by an unrelated script that must not move or change.

Resolution: the new script is `scripts/lint_docs.py`. `check_headings.py` is byte-identical to its starting state, and its docstring is quoted in the new script's header so the next reader does not repeat the confusion.

## Delegation review

## Delegation review: docs-linter

**Verdict:** 3 of 4 steps become pure script invocations. Replacing the 3 SCRIPT step(s) removes ~67 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file under `docs/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob docs/**/*.md, sort by path, count - a pure function of the tree, identical on every run | `python3 scripts/lint_docs.py docs/ --json` -> JSON with files[] (sorted rel paths), file_count, h1_findings[], fence_counts{}, fence_total, exit 0 no findings / 1 findings / 2 usage |
| s2 | "Check that each file starts with a level-1 heading followed by a blank line." (L15-16) | numbered-list | 28 | SCRIPT | fixed rule: first line is '# ...' and line 2 is blank. Same regex verdict every run. Name collision: scripts/check_headings.py already exists and checks image alt text, not headings, so the new code goes in lint_docs.py and that file is left untouched | `python3 scripts/lint_docs.py docs/ --json` -> JSON with files[] (sorted rel paths), file_count, h1_findings[], fence_counts{}, fence_total, exit 0 no findings / 1 findings / 2 usage |
| s3 | "Count the fenced code blocks in each file and total them across files." (L17-17) | numbered-list | 18 | SCRIPT | counting fenced blocks per file and summing is arithmetic over the same tree s1 already walks | `python3 scripts/lint_docs.py docs/ --json` -> JSON with files[] (sorted rel paths), file_count, h1_findings[], fence_counts{}, fence_total, exit 0 no findings / 1 findings / 2 usage |
| s4 | "Decide which of the flagged files matter most to fix this sprint, given that" (L18-19) | numbered-list | 30 | CLAUDE | ranks findings by traffic and by what fits this sprint - inputs no script sees, and two reasonable runs should rank differently. lint_docs.py already hands it the flagged list, so a second script would add an invocation and remove no reasoning | - |

s1, s2, and s3 all walk the same `docs/` tree, so they share one script and one invocation instead of three. s4 stays CLAUDE: it consumes `h1_findings`, which lint_docs.py already produces, and a second script would add an invocation without removing any reasoning.

## Script written

`scripts/lint_docs.py` — one pass over a docs tree.

    python3 scripts/lint_docs.py <docs-dir> [--json] [--out FILE]

stdout with `--json`: `{root, files[], file_count, h1_findings[], fence_counts{}, fence_total}`.
Exit 0 no heading findings, 1 findings, 2 usage error or unreadable directory.
`--out FILE` keeps stdout to a one-line summary, because a large docs tree would otherwise dump the whole report into context.

Finding codes, one per condition, each with its own fixture:

| Code | Condition |
|---|---|
| `first_line_not_h1` | line 1 is not a `# ` heading |
| `no_h1_anywhere` | no line in the file is a `# ` heading |
| `h1_missing_blank_line` | line 1 is a `# ` heading but line 2 is not blank |

`check_headings.py` was not touched, not renamed, and not absorbed.

## Smoke test

    python3 <scriptify>/scripts/smoke_test.py .delegation-review/manifest.json

    PASS  scripts/lint_docs.py  exists
    PASS  scripts/lint_docs.py  help
    PASS  scripts/lint_docs.py  fixture-run[0]
    PASS  scripts/lint_docs.py  fixture-run[1]
    PASS  scripts/lint_docs.py  fixture-run[2]
    PASS  scripts/lint_docs.py  fixture-run[3]
    PASS  scripts/lint_docs.py  fixture-run[4]
    PASS  scripts/lint_docs.py  bad-data
    PASS  scripts/lint_docs.py  bad-args
    PASS  scripts/lint_docs.py  codes-distinct

    10/10 checks passed

Each finding code has its own failing fixture and its own asserted string, so the suite proves the logic discriminates rather than merely runs.

## SKILL.md diff

    --- a/SKILL.md
    +++ b/SKILL.md
    @@ -10,10 +10,12 @@

     ## Workflow

    -1. List every `.md` file under `docs/`, sorted by path, and note the total
    -   count.
    -2. Check that each file starts with a level-1 heading followed by a blank line.
    -   Record every file that does not.
    -3. Count the fenced code blocks in each file and total them across files.
    -4. Decide which of the flagged files matter most to fix this sprint, given that
    +1. Run exactly: `python3 scripts/lint_docs.py docs/ --json`
    +   One pass covers the file inventory, the level-1 heading rule, and the
    +   fenced-block counts. Exit 0 no heading findings, 1 findings, 2 usage error.
    +   Read `files` and `file_count` for the sorted inventory, `h1_findings` for
    +   the flagged files, and `fence_counts` with `fence_total` for the block
    +   counts. Finding codes: `first_line_not_h1`, `no_h1_anywhere`,
    +   `h1_missing_blank_line`.
    +2. Decide which of the flagged files matter most to fix this sprint, given that
        the tutorial pages get the most traffic.

The judgment step keeps its wording verbatim. The workflow is now one invocation plus one judgment call.

## Wrap up

- Scripts written: `scripts/lint_docs.py` (1 new file). `scripts/check_headings.py` untouched.
- Smoke test: 10/10 PASS.
- DEAD steps flagged for a `skillit:review` follow-up: none.
- Residue not kept, so `.delegation-review/` was removed after the green run.
- Loose end worth a follow-up, not changed here: `check_headings.py` is invoked by no step in this skill and it currently fails on `docs/reference/api.md`. Adding an alt-text step, or moving the script out of this skill, is a decision the target's owner owns.
- Next: run `skillit:review` on the target as a final check.
