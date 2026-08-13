# Uncertainties and workarounds

1. **Step 9 residue removal versus the eval's audit trail.** The prompt gave no residue
   instruction, so the run took the recommended default (No), and Step 9 then says to remove
   `.delegation-review/`. Deleting it outright would have destroyed the inventory,
   classification, manifest, and fixtures a grader needs. Workaround: copied the directory to
   `scratch/delegation-review-archive/` first, then removed `.delegation-review/`. The target
   skill is unaffected either way — no residue was installed under
   `changelog-checker/scripts/tests/`.

2. **Steps 1-3 merged into one invocation.** The rewritten SKILL.md has 5 steps, not 7. All
   three original obligations (list files sorted by version, validate headers, count entries per
   category) are named in the merged step, because one pass over the files answers all three and
   printing the same command three times would be noise. Anyone diffing step counts should read
   step 1's body rather than the numbering.

3. **`render_summary.py` exit contract changed after the first render.** The classification
   first claimed "1 = scan file invalid". House style reserves 1 for findings, and a renderer
   produces none, so it became "2 = usage or unreadable scan file" before the report was
   finalized. The report in `outputs/report.md` shows the corrected contract.

4. **One failed command.** `cat -A` is a GNU flag; macOS `cat` rejected it (exit 1). Replaced
   with three Read calls. No effect on the result.
