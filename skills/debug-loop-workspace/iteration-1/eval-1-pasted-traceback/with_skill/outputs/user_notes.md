# User notes

- **No live user.** Stated assumption: the checked-in `data/sales-2026-08.csv` is the exact file that failed, so I debugged against it rather than asking where the export came from.
- **Workaround, unrelated to the bug.** The baseline commit tracked `__pycache__/*.pyc`, which made `git stash pop` fail during the revert-and-confirm check (`error: Your local changes to the following files would be overwritten by merge: __pycache__/report.cpython-314.pyc`). Resolved with `git checkout -- __pycache__` before the pop, then added a `.gitignore` and untracked the bytecode. This touches files outside the bug's blast radius and is flagged to the user in `response.md` as revertible.
- **Skipped subagent diff review** (SKILL.md Step 5 calls for it "for anything non-trivial"). The fix is a single-token encoding change with a committed red-to-green test and a revert check; a review agent would cost more context than the diff carries.
