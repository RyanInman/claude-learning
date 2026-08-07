# api-docs-checker — which steps should be scripts

Report only. Nothing written into the target skill, per the request.

## Step 0 — eligibility

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/with_skill/workspace/api-docs-checker`

Writable, user-owned, outside every plugin cache path. Eligible for the full
workflow.

One warning: `git status` reports the target SKILL.md as untracked (`??`), so
there is no committed restore point in git. Backed it up to
`scratch/.delegation-review/SKILL.md.orig` before touching anything.

## Step 1 — inventory (deterministic)

    python3 /Users/admin/claude-learning/skills/scriptify/scripts/inventory.py \
      <target> --out .delegation-review/inventory.json

    inventory: .../with_skill/workspace/api-docs-checker
    steps: 5  existing scripts: 0  references: 0  body: ~204 tokens
      s1 numbered-list L13-14 ~21tok verbs=count,sort,list tools=-
      s2 numbered-list L15-16 ~28tok verbs=check tools=-
      s3 numbered-list L17-19 ~40tok verbs=check tools=-
      s4 numbered-list L20-21 ~22tok verbs=list tools=-
      s5 numbered-list L22-24 ~35tok verbs=- tools=-

    EXIT=0

5 numbered steps, no existing scripts, so nothing is ALREADY_DELEGATED.

## Steps 2-3 — classification report (rendered verbatim)

    python3 /Users/admin/claude-learning/skills/scriptify/scripts/render_report.py \
      .delegation-review/classification.json .delegation-review/inventory.json
    EXIT=0

---

## Delegation review: api-docs-checker

**Verdict:** 3 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~96 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `endpoints/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob endpoints/*.md, sort by path, count: pure function of the directory, identical every run | `python3 scripts/check_endpoints.py endpoints/ --json` -> {count, files[], missing[{file, fields[]}]}, exit 0 clean / 1 findings / 2 usage |
| s2 | "Check that every endpoint file has a `summary:` field in its frontmatter." (L15-16) | numbered-list | 28 | DEAD | duplicative: step 3 checks summary AND description, a strict superset of this summary-only check. Same files, same frontmatter, same finding reported twice. Flag for skillit:review; the step 3 script covers the check with no loss | - |
| s3 | "Check that every endpoint file has both a `summary:` field and a" (L17-19) | numbered-list | 40 | SCRIPT | fixed-rule frontmatter validation: required keys present or not, with no interpretation of their values | `python3 scripts/check_endpoints.py endpoints/ --json` -> {count, files[], missing[{file, fields[]}]}, exit 0 clean / 1 findings / 2 usage |
| s4 | "Append the endpoint list to `legacy/index.txt` so the old docs portal can" (L20-21) | numbered-list | 22 | DEAD | writes legacy/index.txt for the legacy docs portal, which the skill's own Notes section says was retired in v2 along with the legacy/ directory. No consumer exists; scripting it would make dead output deterministic instead of removing it | - |
| s5 | "Judge whether each `description:` reads clearly for an external developer" (L22-24) | numbered-list | 35 | HYBRID | clarity for an unfamiliar external developer is genuine judgment and reasonable runs should differ, but the mechanical shell is scriptable: extract each description with pre-computed facts, then Claude judges only the text | `python3 scripts/list_descriptions.py endpoints/ --json` -> [{file, description, words, chars, has_placeholder, vague_terms[]}] sorted by path, exit 0 always when readable / 2 usage |

---

## Summary

**Script these three (2 scripts total):**

- **s1 + s3 -> `check_endpoints.py`.** One walk of `endpoints/` gives the sorted
  file list, the count, and the missing-frontmatter findings. File discovery,
  counting, and fixed-rule validation are three of the rubric's plainest SCRIPT
  categories. Two runs should never differ here. Against the current fixtures
  the script reports `delete-widget.md` missing `description` and
  `list-widgets.md` missing `summary` — findings a script gets right every
  time and prose re-derives every time.
- **s5 -> `list_descriptions.py` + judgment (HYBRID).** "Reads clearly for an
  external developer" is real judgment; reasonable runs should disagree, so it
  never becomes pure SCRIPT. The shell around it is mechanical: find the files,
  parse frontmatter, pull each `description:`, pre-compute word count and
  placeholder or vague-term markers. Claude then judges only the extracted
  text. On the current fixtures that surfaces `list-widgets.md`'s "Does the
  listing thing with the standard params." for a human rewrite.

**Do not script these two — delete them instead:**

- **s2 is duplicative.** Step 3 checks `summary:` and `description:`; step 2
  checks `summary:` alone. Step 3 strictly subsumes it, so the skill reports
  the same missing field twice. Dropping step 2 loses no coverage. If you would
  rather keep a standalone summary-only check, `check_endpoints.py` already
  answers it from the same output — but the step still does not need to exist.
- **s4 is superseded.** It appends to `legacy/index.txt` for the legacy docs
  portal, and the skill's own Notes section says that portal was retired in v2
  along with the `legacy/` directory. The step writes output nothing reads, and
  it writes it into a directory that no longer exists. Scripting it would only
  make dead output deterministic. Route both s2 and s4 to a `skillit:review`
  follow-up rather than auto-deleting — you own the target's workflow.

**Net shape after delegation:** step 1 becomes one exact invocation covering
old steps 1 and 3, step 2 becomes "run `list_descriptions.py`, then judge the
descriptions", steps 2 and 4 disappear. Five prose steps collapse to two
script-led ones, and the ~96 tokens of mechanical reasoning per run drop to a
pair of command lines.

## What was not run

Stopped after Step 3 at the Step 4 gate, since the request was report-only. No
scripts written, no fixtures, no smoke test, target SKILL.md byte-identical to
its baseline. See `gate.md`. To apply, re-run from Step 5 — the recorded
decisions live in `scratch/.delegation-review/classification.json`.
