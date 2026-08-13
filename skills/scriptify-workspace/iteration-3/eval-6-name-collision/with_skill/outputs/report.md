## Delegation review: docs-linter

**Verdict:** 3 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~67 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file under `docs/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob docs/**/*.md, sort by path, count - same output every run | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: files[] sorted, file_count, h1_violations[], fence counts, exit 0 clean / 1 h1 violations found / 2 usage |
| s2 | "Check that each file starts with a level-1 heading followed by a blank line." (L15-16) | numbered-list | 28 | SCRIPT | fixed regex rule (first line is '# ' and line 2 blank); a unit test is writable now. NOT already delegated: scripts/check_headings.py checks image alt text despite its name | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: h1_violations[] with path and reason, exit 0 clean / 1 h1 violations found / 2 usage |
| s3 | "Count the fenced code blocks in each file and total them across files." (L17-17) | numbered-list | 18 | SCRIPT | counting fenced blocks per file and totalling is pure aggregation | `python3 scripts/lint_docs.py docs/ --json` -> findings JSON: per-file fenced_blocks and fenced_blocks_total, exit 0 clean / 1 h1 violations found / 2 usage |
| s4 | "Decide which of the flagged files matter most to fix this sprint, given that" (L18-19) | numbered-list | 30 | CLAUDE | prioritising which flagged files to fix this sprint weighs traffic against effort; reasonable runs should differ, and the script shell around it (the flagged list) is already produced by lint_docs.py | - |

### Name collision — the existing `scripts/check_headings.py` is not what its name says

`docs-linter/scripts/` already ships `check_headings.py`, the obvious name for
step s2. It does **not** check headings. Its docstring and its code check
**image alt text**, and it states that the release pipeline calls it by that
exact path. Probing it confirms both halves:

    $ python3 scripts/check_headings.py --help
    not a directory: --help          (exit 2 - no argparse, so the audit's help_ok=False)

    $ python3 scripts/check_headings.py docs
    missing alt text: docs/reference/api.md
    (exit 1)

Two consequences:

1. **s2 is not ALREADY_DELEGATED.** The name matches the step; the behaviour
   does not. Classifying on the name would have left the heading rule as prose
   forever while the report claimed it was covered.
2. **`check_headings.py` is not a free name.** Writing the heading linter there
   would silently delete the alt-text check the release pipeline depends on.
   The new script is therefore `scripts/lint_docs.py`, and `check_headings.py`
   is left byte-identical.

### What the target's own data produces

`sample_target_data.py` names the outliers, and the finished script confirms
them against the real tree:

    $ python3 scripts/lint_docs.py docs/ --json      (exit 1)
    file_count: 3
    findings:
      docs/reference/api.md  no_h1          # starts "## API Reference"; no level-1 heading anywhere
      docs/tutorial.md       h1_not_first   # prose on line 1, "# Tutorial" on line 3
    fenced_blocks: getting-started.md 2, reference/api.md 1, tutorial.md 1
    fenced_blocks_total: 4

`docs/getting-started.md` is the only clean file. Both defects are real planted
fixtures the prose step existed to catch, and a linter written against an
imagined tree would have missed the `h1_not_first` case entirely - a naive
"file has no H1" check passes `tutorial.md`, which does have one, just not
first.

### Contract - four finding codes, one per distinct failure

| Code | Condition | Fixture |
|---|---|---|
| `empty_file` | the file has no content at all | `bad/empty/empty.md` |
| `no_h1` | no level-1 heading anywhere in the file | `bad/no_h1/api.md` |
| `h1_not_first` | a level-1 heading exists, but not on line 1 | `bad/h1_not_first/tut.md` |
| `missing_blank_after_h1` | line 1 is an H1 and line 2 is not blank | `bad/missing_blank/x.md` |

`no_h1` and `h1_not_first` are kept apart deliberately. Collapsing them into one
`missing_h1` would report `docs/tutorial.md` - which has an H1 - as missing one,
and step 2 would then publish that wrong label to whoever reads the findings.

### Script written

`docs-linter/scripts/lint_docs.py` (129 lines, stdlib only)

    python3 scripts/lint_docs.py <docs-dir> [--json] [--out FILE]

    stdout  {root, file_count, files[], findings[], fenced_blocks{}, fenced_blocks_total}
    exit    0 every file passes / 1 findings / 2 usage or not a directory
    --out   writes the report to a file, prints a one-line summary - for trees
            large enough that the full JSON would flood context

One script covers s1, s2, and s3 because all three walk the same tree. Three
scripts would mean three subprocesses and three JSON payloads for one pass of
work.

### Smoke test

    $ python3 scripts/smoke_test.py .delegation-review/manifest.json
    PASS  scripts/lint_docs.py  exists
    PASS  scripts/lint_docs.py  help
    PASS  scripts/lint_docs.py  fixture-run[0]   good/  exit 0, fenced_blocks_total 1
    PASS  scripts/lint_docs.py  fixture-run[1]   good/  exit 0, file_count 2
    PASS  scripts/lint_docs.py  fixture-run[2]   bad/h1_not_first
    PASS  scripts/lint_docs.py  fixture-run[3]   bad/no_h1
    PASS  scripts/lint_docs.py  fixture-run[4]   bad/missing_blank
    PASS  scripts/lint_docs.py  fixture-run[5]   bad/empty
    PASS  scripts/lint_docs.py  bad-data
    PASS  scripts/lint_docs.py  bad-args
    PASS  scripts/lint_docs.py  codes-distinct

    11/11 checks passed   (exit 0)

Green before the SKILL.md rewrite and green again after it.

### SKILL.md diff

```diff
--- a/docs-linter/SKILL.md
+++ b/docs-linter/SKILL.md
@@ -10,10 +10,19 @@

 ## Workflow

-1. List every `.md` file under `docs/`, sorted by path, and note the total
-   count.
-2. Check that each file starts with a level-1 heading followed by a blank line.
-   Record every file that does not.
-3. Count the fenced code blocks in each file and total them across files.
-4. Decide which of the flagged files matter most to fix this sprint, given that
+1. Run exactly: `python3 scripts/lint_docs.py docs/ --json`
+
+   One pass over the tree carries the file inventory, the heading rule, and the
+   fence tally. Exit 0 every file passes, 1 findings, 2 usage error.
+
+   - `files` (sorted by path) and `file_count` - the docs inventory.
+   - `findings` - one entry per file that does not start with a level-1
+     heading followed by a blank line, coded `empty_file`, `no_h1`,
+     `h1_not_first`, or `missing_blank_after_h1`.
+   - `fenced_blocks` per file and `fenced_blocks_total`.
+
+   Exit 0 -> report the counts and stop, because nothing needs fixing.
+   Large tree -> add `--out findings.json` and read the file instead.
+
+2. Decide which of the flagged files matter most to fix this sprint, given that
    the tutorial pages get the most traffic.
```

Step 4's judgment sentence survives verbatim, including its "the tutorial pages
get the most traffic" rationale. Steps 1-3 collapse into one invocation because
one script answers all three.

### Follow-ups for you

- **No DEAD steps.**
- **`scripts/check_headings.py` is misnamed and unreferenced.** No step in
  `SKILL.md` invokes it, so the skill never runs the alt-text check it performs
  - and that is the check catching `docs/reference/api.md`'s `![](diagram.png)`.
  Two decisions are yours, and both sit outside this run's scope: rename it to
  `check_alt_text.py` (coordinate with the release pipeline that calls the
  current path), and add a workflow step that actually invokes it. I changed
  neither byte of that file.
- Run `skillit:review` on `docs-linter` as a final check.
