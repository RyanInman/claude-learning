# api-docs-checker — which steps should be scripts

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-8-dead-step/without_skill/workspace/api-docs-checker/`

Analysis only. Nothing was written into the target skill folder.

## Classification table

| # | Step (abbreviated) | Class | Verdict |
|---|---|---|---|
| 1 | List every `.md` in `endpoints/`, sorted by path, note total count | SCRIPT | Fold into one `check_endpoints.py` with step 3 |
| 2 | Check every file has `summary:` in frontmatter | SUPERSEDED | Duplicate of step 3 — no separate script |
| 3 | Check every file has both `summary:` and `description:`, record which is missing where | SCRIPT | Primary script; subsumes steps 1 and 2 |
| 4 | Append endpoint list to `legacy/index.txt` | DEAD | No script. Do not automate a retired output |
| 5 | Judge whether each `description:` reads clearly for an external developer | CLAUDE | Keep judgment with Claude; script only feeds it the descriptions |

Net proposal: **one script**, covering steps 1 + 2 + 3. Step 4 gets nothing. Step 5 stays prose, optionally fed by the same script's output.

## Reasoning per step

### Step 1 — SCRIPT
Enumerating `endpoints/*.md`, sorting by path, and counting is pure mechanical file I/O. Nothing about it needs a model. Re-deriving the listing in prose on every run burns tokens and invites run-to-run drift (missed files, inconsistent ordering, off-by-one counts). It is not worth its own script file though — the listing is the first thing the step-3 checker has to do anyway, so it belongs in that script and its output should include the sorted file list plus the total count.

### Step 2 — SUPERSEDED (no script)
Step 2 checks for `summary:`. Step 3 checks for `summary:` **and** `description:` and reports which field is missing from which file. Everything step 2 produces is a strict subset of step 3's output. Scripting it separately would mean parsing every file twice and emitting two overlapping "missing field" lists that can disagree.

Recommendation: implement the field check once (step 3's version) and let step 2's requirement be satisfied by that result. This is a SKILL.md wording observation, not a licence to delete step 2 — the request was which steps should be scripts, so the reporting stops here. Removing the redundancy from the prose is a separate, explicit edit.

Evidence from the fixture data (three endpoint files):
- `create-widget.md` — has both fields
- `delete-widget.md` — missing `description:`
- `list-widgets.md` — missing `summary:`

Step 3 alone catches both defects; step 2 alone catches only the `list-widgets.md` one.

### Step 4 — DEAD (no script, and no deletion)
The skill's own Notes section says:

> The legacy docs portal was retired in v2, and the `legacy/` output directory went with it.

Confirmed on disk: there is no `legacy/` directory in the skill folder (`ls legacy` → `No such file or directory`). The step writes to a consumer that no longer exists, at a path that no longer exists.

So this step gets **no script**. Scripting it would be the worst outcome available: it would make a no-op permanent, create a `legacy/index.txt` that nothing reads, and add a file-writing side effect to a skill that is otherwise read-only. Writing that script is fast to do and hard to notice afterwards, which is exactly why the step needs calling out instead.

Step 4 is also **not** deleted from the target SKILL.md. The request was an assessment, not an edit, and removing a workflow step is a product decision about the skill rather than a scriptification decision. Flagging it dead is the deliverable; the skill's owner decides whether to drop step 4 and its Notes paragraph together.

### Step 5 — CLAUDE (keep the judgment)
"Does this description read clearly for an external developer who has never seen this API" is a semantic quality call. No deterministic rule separates `Creates a new widget owned by the calling account and returns its id.` (clear) from `Does the listing thing with the standard params.` (vague, self-referential, undefined "standard params"). Length heuristics, word counts, and banned-phrase lists all produce false positives and false negatives here, and a script that pretends to make this call gives confident wrong answers.

The mechanical part that can be scripted is input assembly: have the step-3 script emit each file's `description:` value alongside its path, so Claude reads one compact structured list instead of opening every endpoint file. Judgment stays with Claude; retrieval moves to the script.

## Suggested script shape (not written)

`scripts/check_endpoints.py`
- Walks `endpoints/*.md`, sorted by path
- Parses YAML frontmatter per file
- Emits: total count, sorted file list, per-file missing-field report (`summary`, `description`), and each present `description:` string for step 5's review
- Read-only; exits non-zero only on unreadable input, not on doc defects

One script, one pass over the files, covering steps 1-3 and feeding step 5.
