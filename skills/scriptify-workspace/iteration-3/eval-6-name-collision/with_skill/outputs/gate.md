# Step 4 gate — the questions I would have asked

Delivery: one `AskUserQuestion` call carrying both questions below.

## Question 1 — Which rows to apply?

header: `Apply`

Rows s1, s2, s3 are the SCRIPT rows; 3 rows is 4 or fewer, so this is a
`multiSelect: true` question with one option per row, each marked
"(Recommended)".

| Option | Description |
|---|---|
| `s1 — list + count docs files (Recommended)` | Delegate to `scripts/lint_docs.py`: glob `docs/**/*.md`, sort by path, report `file_count`. |
| `s2 — H1-then-blank-line check (Recommended)` | Delegate to `scripts/lint_docs.py`: flag every file whose first line is not a level-1 heading followed by a blank line. |
| `s3 — count fenced code blocks (Recommended)` | Delegate to `scripts/lint_docs.py`: per-file fence counts plus the total. |

(s4 — "decide which flagged files matter most this sprint" — is classified
CLAUDE and is not offered; it stays prose.)

## Question 2 — Keep the verification residue?

header: `Residue`

Keep the smoke-test fixtures and manifest in the target's `scripts/tests/`
afterward?

| Option | Description |
|---|---|
| `No (Recommended)` | Delete `.delegation-review/` after a green run. The target ships only `scripts/lint_docs.py`. |
| `Yes` | Install fixtures, manifest, and a vendored `smoke_test.py` under `docs-linter/scripts/tests/`, and prove they survive relocation. |

## Question 3 — Name collision (would have been a follow-up at Step 6)

Step 6 of `references/applying.md` says: "Name collision with an existing file
→ ask the user. Never overwrite silently."

The target already ships `scripts/check_headings.py`. Its name suggests it
backs step s2, but its docstring and code check **image alt text**, not
headings, and it says the release pipeline calls it by that exact path. So s2
is not ALREADY_DELEGATED, and `check_headings.py` is not a free name.

| Option | Description |
|---|---|
| `Use a new name — scripts/lint_docs.py (Recommended)` | Leaves the alt-text checker and the release pipeline that calls it untouched. |
| `Overwrite scripts/check_headings.py` | Breaks the release pipeline's alt-text check. Not recommended. |
| `Rename the existing script to check_alt_text.py first` | Fixes the misleading name but changes a path outside this skill's scope, so it needs the pipeline owner's sign-off. |

## What the prompt already decided

`prompt.txt` says "find the steps worth delegating and **apply all** of them",
so Question 1 resolves to all three SCRIPT rows selected. Question 2 takes its
recommended default, `No`. Question 3 takes its recommended default: write
`scripts/lint_docs.py` and leave `scripts/check_headings.py` byte-identical.
