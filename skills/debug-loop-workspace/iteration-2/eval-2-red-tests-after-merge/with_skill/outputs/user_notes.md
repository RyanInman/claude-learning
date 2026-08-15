# User notes

**Missing fact, assumption made.** The report said "after I merged main," but the fixture is a single baseline commit with no merge history, so there was no pre-merge `pricing.py` to diff and no commit range for the brief's Scope line. Assumption stated in the response: debug current behavior directly instead of bisecting the merge. Every hypothesis was testable against the working tree, so this cost nothing here — on a real repo the commit range would have been the first thing to read.

**Judgment call, no user available.** The reviewer surfaced that `ROUND_HALF_UP` rounds negative amounts away from zero, changing refund-line behavior (`-1.99` → `-2.00`). Whether "half a cent bills up" means "toward positive" or "larger magnitude" is a product decision with nothing in the repo to settle it. I left the behavior as-is, out of scope for the two failing tests, and surfaced it in the response as an open question rather than silently picking a side.

**Deliberately not fixed.** The `float` round-trip inside `order_total` and the `InvalidOperation` on exotic inputs (inf, `Fraction`, >1e26) are both real but neither causes a failing test. Per the skill's proportional-diff rule, noted for the user instead of expanding the change.

**One tool error.** A foreground `sleep 25` to wait on the reviewer was blocked by the harness; switched to `run_in_background`. No effect on the work.
