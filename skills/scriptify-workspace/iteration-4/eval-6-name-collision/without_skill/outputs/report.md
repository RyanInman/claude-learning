# Scriptified: docs-linter

## What I delegated

Steps 1-3 of the workflow were deterministic — list the files, check each one
opens with a level-1 heading plus a blank line, count fenced code blocks. Every
run should produce the same numbers, and prose re-derivation does not guarantee
that. All three now run in one script: `scripts/lint_docs.py`.

Step 4 stayed in the skill body. Choosing which flagged files to fix first
weighs traffic against effort, which is a judgment call with no single right
answer.

## The name collision

The obvious name for a heading checker is `scripts/check_headings.py`, and that
file already exists. It does not check headings — it checks image alt text, and
its own docstring says the release pipeline calls it by that exact path. Writing
the new logic there would have broken the pipeline and destroyed a check nothing
else performs.

I left it untouched and named the new script `scripts/lint_docs.py`, which also
reads better now that it covers listing and code block counting as well. The
SKILL.md gotchas section records why the old name must stay as it is, so the
next person to open the skill does not repeat the mistake.

## Files changed

| File | Change |
| --- | --- |
| `scripts/lint_docs.py` | New. Covers workflow steps 1-3, prints JSON. |
| `SKILL.md` | Rewritten workflow: step 1 runs the script, step 2 is the judgment call, step 3 reports. Added a gotchas section. |
| `scripts/check_headings.py` | Unchanged, deliberately. |

## The script

`python3 scripts/lint_docs.py [docs-dir]` — `docs-dir` defaults to `docs`.

It prints JSON with `docs_dir`, `file_count`, `files` (sorted), `missing_h1`
(each entry carrying the file and the reason), `code_blocks` per file, and
`total_code_blocks`. Exit code 0 means the scan completed and 2 means the
directory is missing. Findings do not change the exit code, because the caller
needs the data either way and a nonzero exit would read as a crash.

Two details worth knowing. The fence counter toggles on ``` and ~~~ and counts
only opening fences, so a fence character inside an open block does not
double-count. The heading check reports a distinct reason per failure — empty
file, first line is not a level-1 heading, or no blank line after it — so the
report can quote it instead of paraphrasing.

## Verification

Run against the bundled `docs/` tree:

```
$ python3 scripts/lint_docs.py docs
{
  "docs_dir": "docs",
  "file_count": 3,
  "files": [
    "docs/getting-started.md",
    "docs/reference/api.md",
    "docs/tutorial.md"
  ],
  "missing_h1": [
    {
      "file": "docs/reference/api.md",
      "reason": "first line is not a level-1 heading"
    },
    {
      "file": "docs/tutorial.md",
      "reason": "first line is not a level-1 heading"
    }
  ],
  "code_blocks": {
    "docs/getting-started.md": 2,
    "docs/reference/api.md": 1,
    "docs/tutorial.md": 1
  },
  "total_code_blocks": 4
}
```

I checked those numbers against the three files by hand. `api.md` opens with
`## API Reference`, `tutorial.md` opens with prose before any heading, and the
code blocks are 2 + 1 + 1. Exit code 0.

Also confirmed no regression on the neighbouring script:

```
$ python3 scripts/check_headings.py docs
missing alt text: docs/reference/api.md
$ echo $?
1
```

That is its documented behaviour — `api.md` carries `![](diagram.png)` with an
empty alt attribute — so the pipeline check still works.
