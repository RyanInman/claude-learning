# scriptify run — docs-linter (eval-6-name-collision)

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-6-name-collision/with_skill/workspace/docs-linter`

## Step 0 — eligibility

Writable, user-owned, outside every plugin cache path. Eligible for the full
run. `git status` on the target SKILL.md reports it untracked (`??`) rather than
dirty — no uncommitted edits at risk. Restore point copied to
`.delegation-review/SKILL.md.orig` before anything was touched.

## Step 1 — inventory (deterministic)

```
$ python3 <skill>/scripts/inventory.py <target> --out .delegation-review/inventory.json
inventory: .../workspace/docs-linter
steps: 4  existing scripts: 1  references: 0  body: ~128 tokens
  s1 numbered-list L13-14 ~21tok verbs=count,sort,list tools=-
  s2 numbered-list L15-16 ~28tok verbs=check tools=-
  s3 numbered-list L17-17 ~18tok verbs=count tools=-
  s4 numbered-list L18-19 ~30tok verbs=- tools=-
  script scripts/check_headings.py lines=43 mentioned=False argparse=False help_ok=False
exit 0
```

The existing-script audit is the important line: `scripts/check_headings.py`
exists, is **not** mentioned anywhere in the body, and — reading it — checks
markdown **image alt text**, not headings. Its docstring says "the release
pipeline still calls it by this exact path". No workflow step is delegated to
it, so nothing classifies as ALREADY_DELEGATED.

## Step 2 + 3 — classification report

Rendered by `render_report.py` (exit 0, classification valid):

## Delegation review: docs-linter

**Verdict:** 4 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~97 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file under `docs/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | file discovery plus a count: pure function of the docs tree, identical on every run | `python3 scripts/docs_stats.py docs/` -> JSON: files (sorted rel paths), file_count, code_blocks per file, total_code_blocks, exit 0 stats emitted / 2 usage or unreadable dir |
| s2 | "Check that each file starts with a level-1 heading followed by a blank line." (L15-16) | numbered-list | 28 | SCRIPT | fixed-rule validation: level-1 heading on line 1 followed by a blank line is a regex check with one right answer (named check_h1.py: scripts/check_headings.py already exists in the target and checks image alt text) | `python3 scripts/check_h1.py docs/` -> JSON: checked count and missing_h1 findings with path plus reason, exit 0 clean / 1 findings / 2 usage or unreadable dir |
| s3 | "Count the fenced code blocks in each file and total them across files." (L17-17) | numbered-list | 18 | SCRIPT | counting fenced blocks per file and totalling them is aggregation over the same traversal as s1 | `python3 scripts/docs_stats.py docs/` -> JSON: files (sorted rel paths), file_count, code_blocks per file, total_code_blocks, exit 0 stats emitted / 2 usage or unreadable dir |
| s4 | "Decide which of the flagged files matter most to fix this sprint, given that" (L18-19) | numbered-list | 30 | HYBRID | the sprint priority call is judgment that varies with the team's traffic knowledge; the candidate list it judges is mechanical, so the checker enumerates the flagged files and Claude ranks them (named check_h1.py: scripts/check_headings.py already exists in the target and checks image alt text) | `python3 scripts/check_h1.py docs/` -> JSON: missing_h1 findings Claude then ranks by traffic and cost, exit 0 nothing flagged, skip the judgment / 1 findings to rank / 2 usage |

Nothing classified DEAD, CLAUDE, or ALREADY_DELEGATED. s4 is HYBRID, not
CLAUDE: only the sprint-priority call varies between reasonable runs, and the
candidate list it ranks is mechanical, so the checker enumerates and Claude
ranks.

The first render of this table proposed the natural name `check_headings.py`
for s2/s4. It became `check_h1.py` after the collision gate below; the table
above is the re-render from the updated classification.

## Step 4 — gate (answered unattended, full text in `gate.md`)

- **Q1 which delegations** → all four. The request said "apply all of them".
- **Q2 keep verification residue** → No (Recommended). `.delegation-review/`
  removed after the green run; nothing extra written into the target.
- **Q3 name collision on `scripts/check_headings.py`** → rename the *new*
  heading checker to `check_h1.py` and leave the existing file untouched
  (Recommended). Overwriting it would silently kill a path the release pipeline
  calls; renaming the existing file would move that same path. Asked at the gate
  rather than at Step 6 because Step 5 keys its fixture folders by script name
  and this run is unattended.

## Step 5 — contract first (fixtures + manifest written before the scripts)

Expectations derived from the step wording, never from script output.

- `fixtures/check_h1/docs-good/` — `alpha.md` (h1 + blank), `nested/beta.md`
  (recursion), `only-heading.md` (h1 at EOF; decided to pass, since there is no
  following content to separate — documented in the script docstring).
- `fixtures/check_h1/docs-bad/` — `prose-first.md` (prose before the heading),
  `h2-first.md` (level 2, not level 1), `no-blank.md` (h1 with no blank line
  after: the subtler half of the rule).
- `fixtures/docs_stats/docs-sample/` — 3 md files across a subdir plus a
  `README.txt` that must be ignored; 2 + 1 + 0 = 3 code blocks.
- `fixtures/docs_stats/docs-empty/` — a tree with no markdown: `file_count` 0 and
  exit 0, because an empty result is valid data, not a failure.

Manifest asserts real values, not just exit codes: `"checked": 3`,
`"missing_h1": []`, `"file_count": 3`, `"total_code_blocks": 3`, and the exact
sorted sequence `alpha.md, bravo.md, sub/charlie.md`.

## Step 6 — scripts written into the target

- `scripts/check_h1.py` — s2, and the enumerator half of s4. Exit 0 clean / 1
  findings / 2 usage. JSON stdout, `--out` for big trees, argparse `--help`.
- `scripts/docs_stats.py` — s1 and s3 off one traversal. Exit 0 / 2. Same
  conventions.
- `scripts/check_headings.py` — **untouched, byte-for-byte identical to the
  baseline** (md5 `f39b9fc885e0c93eb84e34a3d3ae9aac`).

## Step 7 — smoke test

```
$ python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json
PASS  scripts/check_h1.py  exists
PASS  scripts/check_h1.py  help
PASS  scripts/check_h1.py  fixture-run[0]
PASS  scripts/check_h1.py  fixture-run[1]
PASS  scripts/check_h1.py  fixture-run[2]
PASS  scripts/check_h1.py  fixture-run[3]
PASS  scripts/check_h1.py  bad-data
PASS  scripts/check_h1.py  bad-args
PASS  scripts/docs_stats.py  exists
PASS  scripts/docs_stats.py  help
PASS  scripts/docs_stats.py  fixture-run[0]
PASS  scripts/docs_stats.py  fixture-run[1]
PASS  scripts/docs_stats.py  fixture-run[2]
PASS  scripts/docs_stats.py  fixture-run[3]
PASS  scripts/docs_stats.py  bad-data
PASS  scripts/docs_stats.py  bad-args

16/16 checks passed
exit 0
```

Green on the first run; no expectation was changed.

Both scripts against the target's own `docs/` tree, matching the hand analysis:
`docs_stats.py` → 3 files, code blocks 2/1/1, total 4, exit 0. `check_h1.py` →
`tutorial.md` ("first line is not a level-1 heading") and `reference/api.md`
("first line is a level-2 heading, not level 1"), exit 1.

## Step 8 — SKILL.md diff

```diff
--- a/SKILL.md
+++ b/SKILL.md
@@ -10,10 +10,16 @@

 ## Workflow

-1. List every `.md` file under `docs/`, sorted by path, and note the total
-   count.
-2. Check that each file starts with a level-1 heading followed by a blank line.
-   Record every file that does not.
-3. Count the fenced code blocks in each file and total them across files.
-4. Decide which of the flagged files matter most to fix this sprint, given that
-   the tutorial pages get the most traffic.
+1. Run exactly: `python3 scripts/docs_stats.py docs/`
+   Stdout JSON carries `files`, sorted by path, and `file_count`. Exit 0 stats
+   emitted, 2 unreadable directory. Big tree → add `--out stats.json` and read
+   the file.
+2. Run exactly: `python3 scripts/check_h1.py docs/`
+   Exit 0 clean, 1 findings (JSON on stdout), 2 usage error. Every entry under
+   `missing_h1` names the file and the reason it failed.
+3. Step 1's JSON already holds the code-block counts: `code_blocks` per file
+   and `total_code_blocks` across files. Re-run
+   `python3 scripts/docs_stats.py docs/` if that output is gone.
+4. Step 2 exit 0 → nothing flagged, stop here. Otherwise decide which of the
+   files under `missing_h1` matter most to fix this sprint, given that the
+   tutorial pages get the most traffic.
```

Lossless: "sorted by path" and the total both survive as `files` and
`file_count`; step 4 keeps its rationale clause verbatim ("given that the
tutorial pages get the most traffic") and gains an exit-code branch. Frontmatter
and the intro paragraph are unchanged.

## Summary

- **Scripts written:** `scripts/check_h1.py`, `scripts/docs_stats.py`. Four of
  four steps delegated — three SCRIPT, one HYBRID.
- **Diff:** shown above; the workflow is now four exact invocations plus one
  judgment call.
- **Smoke:** 16/16 checks passed, exit 0.
- **DEAD steps:** none.
- **Collision:** `scripts/check_headings.py` was left untouched. It is misnamed
  for what it does (image alt text) and is referenced nowhere in the SKILL.md —
  worth a `skillit:review` follow-up, along with a general quality pass on the
  rewritten skill.
- **Residue:** none. `.delegation-review/` removed after the green run.
