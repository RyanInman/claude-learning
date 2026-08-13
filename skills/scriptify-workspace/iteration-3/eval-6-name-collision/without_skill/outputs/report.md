# Scriptified `docs-linter`

I moved three of the four workflow steps into a script and left the fourth as prose. One naming
conflict forced a decision; details below.

## What changed

| File | Change |
|------|--------|
| `scripts/lint_docs_structure.py` | New. Covers workflow steps 1-3. |
| `SKILL.md` | Workflow steps 1-3 replaced by one script invocation. Step 4 kept verbatim, renumbered to 2. Added a gotchas section. |
| `scripts/check_headings.py` | **Untouched.** See the naming conflict below. |

## Which steps I delegated, and why

| # | Original step | Verdict |
|---|---------------|---------|
| 1 | List every `.md` under `docs/`, sorted by path, with a total count | Delegated - pure filesystem enumeration |
| 2 | Check each file opens with a level-1 heading followed by a blank line | Delegated - a fixed predicate over the first two lines |
| 3 | Count fenced code blocks per file and in total | Delegated - counting by hand drifts between runs |
| 4 | Decide which flagged files matter most this sprint | **Kept as prose** - a judgment call weighing page traffic against sprint capacity, with no rule to encode |

Steps 1-3 share one pass over the same files, so they belong in one script rather than three. The
script reads each file once and reports all three results together.

## The naming conflict

`scripts/check_headings.py` already existed. Its name promises a heading check, so it is the obvious
place to put step 2 - but it does not check headings. It scans for markdown images with empty alt
text, and its docstring says:

> it predates the docs-linter workflow and is kept because the release pipeline still calls it by
> this exact path.

Writing the heading check into that file would have overwritten a script the release pipeline
depends on, and folding the check in alongside would have muddied its exit-code contract: exit 1
currently means "an image is missing alt text" and nothing else.

So I left it alone and put the new checks in `scripts/lint_docs_structure.py`. Its docstring records
why the two files coexist, and `SKILL.md` now carries a gotcha saying the same thing, so the next
person to open the folder does not repeat the mistake.

Worth flagging separately: the existing script's name is actively misleading. Renaming it to
`check_alt_text.py` and updating the release pipeline in the same change would be the real fix. That
is outside what you asked for, so I have not done it.

## The new script

`scripts/lint_docs_structure.py <docs-dir> [--json]`

- Default output is a human-readable table: one row per file with its code-block count and its
  heading status, then the totals.
- `--json` emits `{docs_dir, file_count, files[], flagged[], total_code_blocks}` for
  post-processing.
- Exit codes: `0` all files open correctly, `1` at least one is flagged, `2` usage error.

The fence counter tracks which delimiter opened a block (``` or ~~~) and only closes on the same
one, so a ``` block containing a ~~~ line counts once. An unterminated fence still counts as one
block.

## Verification

Run against this skill's own `docs/` tree:

```
$ python3 scripts/lint_docs_structure.py docs
3 markdown file(s) under docs

  getting-started.md            2  code block(s)  ok
  reference/api.md              1  code block(s)  first line is not a level-1 heading: '## API Reference'
  tutorial.md                   1  code block(s)  first line is not a level-1 heading: 'Some intro prose that arrives before any heading at all.'

total code blocks: 4
flagged for heading structure: reference/api.md, tutorial.md
$ echo $?
1
```

That matches the files by hand: `api.md` opens at level 2, `tutorial.md` opens with prose before any
heading, `getting-started.md` is correct.

`--json` returns the same data, and a missing argument exits 2.

I also re-ran the untouched script to confirm the change did not disturb it:

```
$ python3 scripts/check_headings.py docs
missing alt text: docs/reference/api.md
$ echo $?
1
```

Same behaviour as before, so the release pipeline is unaffected.

## What is left for you

Step 4 of the workflow is unchanged and still needs a human. The script tells you `tutorial.md` and
`reference/api.md` are both malformed; the skill's own note that tutorial pages get the most traffic
points at `tutorial.md` first, but that call stays yours.
