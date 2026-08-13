# Choice point I would have presented

**Question:** I found three of the four workflow steps worth delegating to a script, and one naming
conflict to resolve. Which do you want me to apply?

**Steps and my classification:**

| # | Step | Verdict | Reason |
|---|------|---------|--------|
| 1 | List every `.md` under `docs/`, sorted, with a count | Delegate | Pure filesystem enumeration; a script gives the same list every run |
| 2 | Check each file opens with a level-1 heading plus blank line | Delegate | A fixed textual predicate over line 1 and line 2 |
| 3 | Count fenced code blocks per file and in total | Delegate | Counting; prose re-derivation miscounts and drifts between runs |
| 4 | Decide which flagged files matter most this sprint | Keep as prose | A judgment call weighing traffic and sprint priorities; no fixed rule to encode |

**The naming conflict:** `scripts/check_headings.py` already exists, and its name says it checks
headings, but it actually checks image alt text. Its docstring says the release pipeline calls it at
that exact path. Options:

- **(A) New file, `scripts/lint_docs_structure.py`.** Leaves `check_headings.py` and the release
  pipeline untouched. Costs one more file in `scripts/`.
- **(B) Add the heading and code-block checks into `check_headings.py`.** One file, but it changes
  the exit-code contract the pipeline depends on: today exit 1 means "an image is missing alt text",
  and afterwards it would also mean "a heading is malformed".
- **(C) Rename `check_headings.py` to `check_alt_text.py`, then write the new heading checker under
  the freed name.** Honest names, but it breaks the release pipeline until someone updates it.

**My recommendation:** A. It is the only option that cannot break the release pipeline, and the cost
is one extra file.

**Options I would have offered:** apply all / apply steps 1-3 only / pick a different conflict
resolution (B or C) / change nothing.

**What I did instead:** `prompt.txt` says "find the steps worth delegating and apply all of them",
so I treated every proposed change as approved and applied option A.
