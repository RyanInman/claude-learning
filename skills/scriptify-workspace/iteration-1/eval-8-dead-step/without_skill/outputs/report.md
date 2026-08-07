# api-docs-checker — which steps should be scripts

Nothing written to the skill. Analysis only, as requested.

Skill: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-1/eval-8-dead-step/without_skill/workspace/api-docs-checker`
Corpus: 3 endpoint files (`create-widget.md`, `delete-widget.md`, `list-widgets.md`).

## Verdict table

| Step | What it does | Verdict |
|---|---|---|
| 1 | List `.md` files in `endpoints/`, sorted, with count | **Script** |
| 2 | Check every file has `summary:` | **Script — but delete it, step 3 already covers it** |
| 3 | Check every file has `summary:` and `description:`, record which is missing where | **Script** |
| 4 | Append endpoint list to `legacy/index.txt` | **Neither — dead step, delete it** |
| 5 | Judge whether each `description:` reads clearly for an outside developer | **Keep in prose (Claude)** |

## Detail

### Steps 1 + 2 + 3 → one script

All three are the same filesystem pass: walk `endpoints/`, parse YAML frontmatter, check key presence. Zero judgment, and re-deriving them in prose every run is what produces run-to-run drift (sort order, whether a file with malformed frontmatter counts, whether an empty `summary:` counts as present).

Step 2 is a strict subset of step 3 — step 3 checks `summary:` *and* `description:`. Two separate prose steps that scan the same files for overlapping conditions invite contradictory output ("delete-widget is fine" in step 2, "delete-widget missing description" in step 3). Collapse them.

One script, one pass, emitting:
- sorted file list + total count
- per-file missing-field table
- each file's `description:` text, so step 5 doesn't need a second read pass

Expected output on the current corpus:

```
3 endpoint files:
  endpoints/create-widget.md
  endpoints/delete-widget.md
  endpoints/list-widgets.md

Missing fields:
  endpoints/delete-widget.md   missing: description
  endpoints/list-widgets.md    missing: summary
```

That result is fully determined by the files. It should never vary, so it should never be re-reasoned.

### Step 4 → delete, do not script it

This is the important finding. Step 4 tells the skill to append to `legacy/index.txt`. The skill's own Notes section says:

> The legacy docs portal was retired in v2, and the `legacy/` output directory went with it.

`legacy/` does not exist in the skill folder. The only two mentions of "legacy" anywhere in the workspace are the step that writes to it and the note saying it is gone.

So step 4 is dead. Scripting it would be the wrong move twice over: it converts a no-op into a *reliable* no-op that either hard-fails on a missing directory or, worse, silently recreates `legacy/` and starts producing files nobody consumes. A script makes a step deterministic; it does not make a step correct. Delete the step and the now-orphaned Notes paragraph that only exists to explain it.

### Step 5 → stays with Claude

"Does this description read clearly for an external developer who has never seen this API" is a semantic judgment about audience and prior knowledge. No rule reproduces it. `Does the listing thing with the standard params.` is vague because "the listing thing" names nothing and "the standard params" assumes context the reader lacks — a length or keyword heuristic would not catch that, and would fire falsely on short-but-clear text.

Keep it in prose. The script from steps 1-3 should hand it the description strings so Claude spends its reasoning on the judgment rather than on file I/O.

## Recommended shape

1. `scripts/check_endpoints.py` — enumerate, count, parse frontmatter, report missing fields, emit description text. Covers old steps 1, 2, 3.
2. SKILL.md step 1: run the script, paste its output.
3. SKILL.md step 2: review each emitted `description:` for clarity to an outside developer; flag the unclear ones.
4. Old step 4 and the trailing Notes paragraph: removed.

Five steps become two, one of which is a single command.

## Note on scope

Step 2 removal and step 4 removal go past a literal reading of "which steps should be scripts." They are included because answering only the literal question would recommend scripting a step whose output goes nowhere, and duplicating a check across two scripts. Say the word and I will apply the changes.
