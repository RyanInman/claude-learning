# User notes

## Assumptions made (no live user to ask)

1. **"After I merged main" could not be verified.** The fixture arrived as a snapshot with no git history (`git log --oneline --all` → only my own `baseline` commit). `git bisect`, which the skill's `references/tactics.md` is pointed at for regressions of unknown origin, was therefore unavailable. Assumed the current `pricing.py` is the post-merge state and debugged it directly.
2. **The tests are correct; `pricing.py` is what must change.** `test_half_cent_rounds_up` carries an explicit comment stating the billing intent ("1.995, which bills as 2.00"), so I treated it as the spec rather than as a test to adjust. Per the skill's gotcha, no test was edited.
3. **ROUND_HALF_UP is the intended rounding mode.** Inferred from that same comment. Real billing systems sometimes use half-even or jurisdiction-specific rules; if this codebase has a documented money policy elsewhere, it should be checked against this change.
4. **Kept `order_total`'s round-per-line-then-sum semantics.** The original did this and the test expectation (2.00 + 10.00 = 12.00) is consistent with it. Summing unrounded lines and rounding once would be a behavior change beyond the reported bug.

## Workaround required

`git stash pop` failed mid-verification: the fixture commits `__pycache__/*.pyc` and `.pytest_cache/`, and running pytest rewrote those tracked binaries, so git refused to restore my stashed fix over them.

```
error: Your local changes to the following files would be overwritten by merge:
	__pycache__/pricing.cpython-314.pyc
```

Recovered with `git checkout -- '*.pyc' && git stash pop`. Left the tracked cache files in place rather than deleting them, since removing them is outside the reported bug — flagged to the user in the response instead. A `.gitignore` for `__pycache__/` and `.pytest_cache/` would prevent a repeat.

## Reviewer caveat

The `feature-dev:code-reviewer` subagent had no Bash tool in its session and hand-verified the Decimal arithmetic instead of executing it. Its conclusions were independently confirmed by my own executed overfit checks (six `line_total` cases plus two `order_total` cases, all run), so the review is not resting on unexecuted reasoning alone.
