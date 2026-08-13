## Delegation review: api-docs-checker

**Verdict:** 2 of 5 steps become pure script invocations. Replacing the 2 SCRIPT step(s) removes ~61 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `endpoints/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | globbing endpoints/*.md, sorting by path and counting is a pure function of the directory; two runs must not differ | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON: {count, files[sorted], missing:{file:[fields]}, descriptions:{file:text}}, exit 0 all files complete / 1 missing fields found / 2 usage or unreadable dir |
| s2 | "Check that every endpoint file has a `summary:` field in its frontmatter." (L15-16) | numbered-list | 28 | DEAD | superseded by s3, which checks summary AND description in one pass; running both re-reads the same frontmatter and reports the same summary gaps twice | - |
| s3 | "Check that every endpoint file has both a `summary:` field and a" (L17-19) | numbered-list | 40 | SCRIPT | fixed-rule frontmatter validation: required keys present or absent, same verdict every run, unit-testable today | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON: {count, files[sorted], missing:{file:[fields]}, descriptions:{file:text}}, exit 0 all files complete / 1 missing fields found / 2 usage or unreadable dir |
| s4 | "Append the endpoint list to `legacy/index.txt` so the old docs portal can" (L20-21) | numbered-list | 22 | DEAD | the target's own Notes section says the legacy docs portal was retired in v2 and legacy/ went with it; the directory does not exist in the target, so this step writes to a consumer that is gone | - |
| s5 | "Judge whether each `description:` reads clearly for an external developer" (L22-24) | numbered-list | 35 | CLAUDE | 'reads clearly for an external developer who has never seen this API' is a judgment reasonable runs should disagree on; a script would encode one arbitrary readability rule, and it would only hand back the description strings Claude must read in full anyway | - |

### What your own `endpoints/` data says

The three shipped endpoint files already produce every finding the workflow
looks for, and they show why the classification lands where it does:

- `list-widgets.md` has `description:` but no `summary:`.
- `delete-widget.md` has `summary:` but no `description:` — s2 misses this file
  entirely, s3 catches it. That is the concrete evidence that s2 is subsumed by
  s3 rather than complementary to it.
- `create-widget.md` has both fields and is clean.
- `list-widgets.md`'s description reads "Does the listing thing with the
  standard params." That is the real s5 case: mechanically present, useless to
  an external developer. No field-presence check flags it, which is exactly why
  s5 keeps its judgment core.
- There is no `legacy/` directory in the skill folder, so s4 appends to a path
  that does not exist, for a portal your own Notes section says was retired in
  v2.

### The two DEAD steps

Nothing is deleted from your SKILL.md by this review. s2 and s4 get no script,
because scripting a step that should not run pins a stale workflow in place.
Route both to a `skillit:review` follow-up, or drop them yourself:

- s2 — delete it and let s3 cover both fields.
- s4 — delete it, or restore `legacy/` if the portal is coming back.

### Script count

One script covers both SCRIPT rows. s1 needs the sorted file list and the
count; s3 needs the per-file missing-field map. `check_endpoints.py` emits both
in one JSON payload, so the rewritten workflow makes one invocation, not two.
