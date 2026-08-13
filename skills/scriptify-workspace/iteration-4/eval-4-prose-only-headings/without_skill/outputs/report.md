# Scripting review: `prose-only-reviewer/` (frontmatter name: `link-checker`)

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-4-prose-only-headings/without_skill/workspace/prose-only-reviewer/SKILL.md`
Folder contents: `SKILL.md` only (27 lines). No `scripts/`, no `references/`, no `evals/`.
Nothing was changed. This is a recommendation only.

The skill has no numbered steps. Its work units are the four `##` headings, so I treated each
heading as one anchor and classified it on its own.

## Verdict table

| # | Anchor (heading) | Verdict | Why |
|---|---|---|---|
| 1 | Collect the link inventory | **SCRIPT** | Walking a tree and regex-extracting link targets is deterministic file I/O. Prose re-derivation misses files and miscounts line numbers, and the answer must be identical every run. |
| 2 | Resolve each target | **SCRIPT** | Path resolution plus `exists()` plus two counters. Pure computation over the step-1 output, with a checkable pass/fail signal. |
| 3 | Decide what to fix now | **CLAUDE** | The input is the docs owner's release deadline and what each broken link costs a reader. That trade-off changes run to run and is not on disk, so no fixed rule reproduces it. |
| 4 | Gotchas (skip `#section` links) | **SCRIPT (fold into #1)** | It is a filter predicate on the extraction, not a separate judgement. Encoding it in the collector is the only way it applies every time. |

Two of four anchors become scripts, one stays with Claude, and the gotcha becomes a line of code
inside anchor 1 rather than a rule Claude must remember.

## Proposed script interfaces

### `scripts/collect_links.py` — anchor 1

```
usage: collect_links.py <docs_root> [--out PATH]
```

- Walks `<docs_root>` recursively for `*.md`.
- Extracts inline links `[text](target)` and reference definitions `[label]: target`.
- Emits JSON to stdout, or to `--out PATH`:

```json
{"docs_root": "docs",
 "links": [{"source": "docs/guide/setup.md", "line": 12, "raw": "[config](../config.md)", "target": "../config.md"}]}
```

- Skips, and does not report as broken: anchor-only targets starting with `#`; absolute URLs
  matching `^[a-z][a-z0-9+.-]*://`; `mailto:`. This is the Gotchas rule, enforced in code.
- Keeps the fragment off the path when a target carries one: `../config.md#tls` records
  `target: "../config.md"`.
- Exit codes: `0` walk completed, including the zero-links case, because an empty docs tree is a
  valid answer and not an error. `2` `<docs_root>` missing or not a directory. `1` a matched file
  could not be read; the path goes to stderr.

### `scripts/resolve_links.py` — anchor 2

```
usage: resolve_links.py <inventory.json|-> [--docs-root DIR]
```

- Reads the anchor-1 JSON (`-` means stdin). Resolves each `target` relative to the directory of
  its `source`, not relative to `docs_root`, because that is how a Markdown renderer resolves it.
- Emits JSON to stdout:

```json
{"total": 214, "broken": 3,
 "links": [{"source": "docs/guide/setup.md", "line": 12, "target": "../config.md",
            "resolved": "docs/config.md", "status": "broken"}]}
```

- `status` is `ok` or `broken`. `total` and `broken` are the two counts the skill body already
  asks for, so the body can stop describing how to count and just read these fields.
- Exit codes: `0` every link resolved. `1` at least one broken link, which lets a CI caller gate on
  the exit status alone. `2` unreadable or malformed input JSON.

Pipeline: `collect_links.py docs | resolve_links.py - > report.json`.

If you would rather keep the folder to one file, ship these as `check_links.py collect` and
`check_links.py resolve` subcommands. The argv, JSON, and exit codes above stay as written.

## What anchor 3 keeps

Claude reads `report.json` and, for each `broken` entry, weighs the deadline the user states, how
many readers hit that page, and whether the target moved (fixable in seconds) or was deleted
(needs a real decision). It returns a ranked fix list with a one-line reason each. Do not turn
this into a scoring formula: the weights are supplied by the user per run, so a hardcoded formula
would look objective while being wrong.

## Suggested rewrite shape (not applied)

Anchors 1 and 2 collapse from "walk every file and record…" prose into two command lines plus a
description of the JSON fields. That drops roughly 8 lines of procedure from the body and removes
the two places where Claude currently improvises a traversal. Anchor 3's prose stays as is; it is
already pointed at the right judgement.

## Also noticed, no action taken

The folder is `prose-only-reviewer/` but the frontmatter `name:` is `link-checker`. A skill's
`name` should match its directory, or loaders that key off the path will not find it. Flagging
only; you said not to change anything.
