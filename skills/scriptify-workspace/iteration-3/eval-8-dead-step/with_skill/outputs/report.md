## Delegation review: api-docs-checker

**Verdict:** 3 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~96 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `endpoints/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob endpoints/*.md, sort, count - a pure function of the directory; two runs must not differ | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON {files: sorted paths, count, missing: {file: [fields]}, descriptions: {file: text}}, exit 0 every file complete / 1 missing fields found / 2 usage or unreadable dir |
| s2 | "Check that every endpoint file has a `summary:` field in its frontmatter." (L15-16) | numbered-list | 28 | DEAD | strictly subsumed by s3, which checks summary AND description over the same files; running both rescans endpoints/ and double-reports list-widgets.md | - |
| s3 | "Check that every endpoint file has both a `summary:` field and a" (L17-19) | numbered-list | 40 | SCRIPT | fixed-rule frontmatter validation - required keys present or not, same verdict every run; unit-testable against the three shipped fixtures | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON {files: sorted paths, count, missing: {file: [fields]}, descriptions: {file: text}}, exit 0 every file complete / 1 missing fields found / 2 usage or unreadable dir |
| s4 | "Append the endpoint list to `legacy/index.txt` so the old docs portal can" (L20-21) | numbered-list | 22 | DEAD | writes to legacy/index.txt for a portal the target's own Notes section says was retired in v2; legacy/ does not exist in the skill folder, so the step would create output nothing reads | - |
| s5 | "Judge whether each `description:` reads clearly for an external developer" (L22-24) | numbered-list | 35 | HYBRID | clarity for an unfamiliar external developer is a judgment call reasonable runs disagree on, but the script already extracts every description string, so Claude judges text it no longer has to go gather | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON {files: sorted paths, count, missing: {file: [fields]}, descriptions: {file: text}}, exit 0 every file complete / 1 missing fields found / 2 usage or unreadable dir |

### Short answer

Steps 1 and 3 should be scripts. Step 5 should become a script plus a judgment
call on its output. Steps 2 and 4 should not become scripts at all - they should
be deleted from the skill.

One script covers all three live steps. `check_endpoints.py` scans
`endpoints/`, and emits the sorted file list, the count, the missing frontmatter
fields per file, and every `description:` string. Step 1 reads its file list,
step 3 reads its `missing` map, step 5 judges its `descriptions` map. Splitting
that into three scripts would parse the same three files three times.

### What the target's own data already shows

I digested the three files in `endpoints/`, so each classification is anchored
to a real finding rather than an invented fixture:

- `delete-widget.md` has `summary:` but no `description:`. Step 2 misses this
  file entirely; step 3 catches it. That is the concrete evidence that step 2
  is redundant rather than merely overlapping.
- `list-widgets.md` has `description:` but no `summary:`. Steps 2 and 3 both
  report it, so a run that keeps both steps reports this file twice.
- `create-widget.md` is complete, so the script gets a passing case as well as
  failing ones.
- `list-widgets.md`'s description is "Does the listing thing with the standard
  params." That is the step-5 judgment target: mechanically present, useless to
  an external developer. No script can rule on it, which is why step 5 keeps a
  judgment core instead of becoming pure SCRIPT.
- There is no `legacy/` directory in the skill folder. Step 4 does not append to
  a stale file; it creates one from nothing.

### The two DEAD steps

I do not auto-delete another skill's steps - you own this workflow. Both belong
in a `skillit:review` follow-up:

- **Step 2** - delete it. Step 3 is a strict superset. Keeping it costs a second
  pass over `endpoints/` and produces duplicate findings for `list-widgets.md`.
- **Step 4** - delete it, and delete the `Notes` section that explains it. The
  skill's own note says the legacy portal was retired in v2 and the `legacy/`
  output directory went with it. Scripting this step would harden a write into a
  directory nothing reads.

### End state if you apply the picks

The workflow becomes three steps: run `check_endpoints.py` once, read its
structured output for the file list and the missing-field findings, then judge
the extracted descriptions for clarity. SKILL.md carries one exact command line
and the judgment prose around it.
