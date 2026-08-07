# Judge's Final Report

## Agreed changes

The Advocate conceded five concrete amendments in rebuttal. Both sides now support all of them; they are ready to act on.

1. **One-day compatibility audit, gating the runner swap** (from Objection 2, conceded in full). Grep the estate for `load_tests`, custom `TestRunner`/`TestResult`, `subTest`, and `setUpModule`; attach the hit list to the proposal with per-item dispositions. Make collected-count parity between `unittest discover` and `pytest --collect-only` a per-package release blocker. The Advocate also conceded that its own steelman point 6 ("none of them gates the first step") falls on this item: the swap's failure mode is silently dropped tests that fail green, so reversibility does not cover it.
2. **Time-boxed xdist pilot before parallelism is cited as a benefit** (from Objection 1, gate conceded). Two or three representative packages under `pytest -n auto`; record speedup and count of parallel-only failures. Record baseline CI wall-clock while doing it.
3. **Governance page** (from Objection 3, fix conceded). Named conftest.py owner, lint/CI rule that new test files are pytest-style, per-package migration tracker, and an explicit written choice between a funded finish line and an accepted permanent mixed estate.
4. **Shadow CI job before cutover** (from Objection 5, conceded and adopted). Non-blocking parallel pytest job for two to four weeks comparing collected counts, pass/fail parity, and coverage deltas; per-package cutover only on parity. Both sides note this one mechanism retires the isolation-evidence, collection-parity, and cutover-safety risks, and makes the "revertible in a day" claim checkable rather than asserted.
5. **Half-day baseline scripts** (from Objection 4's remedy, adopted by the Advocate even after the Adversary dropped the objection as a gate). CI wall-clock from the last 20 runs, TestCase inheritance-depth count, sampled variant-family count.

## Dropped objections

- **Objection 4 (no numbers) — dropped by the Adversary as a standalone gate.** Two arguments answered it: the runner swap is cheaply reversible, so it does not need a fully quantified justification, and three of the four benefits (fixtures, parametrize, ecosystem default) do not depend on any of the demanded numbers — only the parallelism claim does, and its baseline measurement folds into the pilot. The measurements still happen (item 5 above), but they no longer block the decision.
- **The destination itself.** The Adversary's opening summary declined to contest pytest as the destination and its rebuttal conceded steelman 4 (ecosystem default) outright, calling it the strongest argument and noting it needs no in-house measurement. The record shows no live argument for staying on unittest.

## Contested points

Only two disputes survive rebuttal, and both are severity framings, not action items.

**A. How costly is the mixed-framework estate under opportunistic migration?**
- *Adversary:* without a finish line, benefits may reach 20% of tests while 100% pays the mixed-codebase tax; worse, the Advocate's own steelman 2 tied safe parallelization to explicit-dependency tests, making parallelism downstream of a migration that has no finish line — the flag is not "free."
- *Advocate:* opportunistic migration is benefit-weighted, not uniform-random — files migrate when touched, so migration concentrates in hot packages where readability and triage pay most, while cold packages generate little of the targeted pain.

**B. How fragile is the parallelism claim?**
- *Adversary (narrowed):* still the least-verified claim, but credits the per-package fallback — failure now means "the benefit shrinks to the isolable subset," not "the benefit evaporates."
- *Advocate:* xdist fails gracefully per-package, parallelism is one argument of three, and isolation failures the pilot surfaces are partly latent test defects worth finding anyway.

## Rulings

**Point A — split, with the sharper catch going to the Adversary.** The Advocate wins the entropy argument on mechanism: touch frequency correlates with the pain the proposal targets, so unmanaged migration lands where it pays most, and the Adversary offered no evidence for the 20% figure. But the Adversary landed a real hit that the Advocate never answered: steelman 2 claimed fixtures are "the enabling work" for xdist, which quietly converts parallelism from "flip a flag" into "downstream of migration progress." On this record that inference stands, and it means the finish-line-versus-permanent-mix choice in the governance page is not cosmetic — in packages where the pilot shows isolation failures, the parallelism benefit waits on funded migration, not entropy. No compromise is needed; the agreed governance page is where the author resolves this, now with the stakes correctly priced.

**Point B — Advocate wins.** The Adversary itself narrowed the objection after crediting the per-package fallback. The realistic downside of the parallelism claim is a smaller speedup, not zero, and the pilot both sides agreed to will replace this dispute with two numbers. Nothing further to rule.

## Judge's recommendation

Adopt the proposal amended with a "gates before commitment" section, ordered by the failure mode each gate prevents:

1. Compatibility grep plus collect-count parity blocker — before the runner swap, because its failure mode (fail-green test loss) is invisible after the fact. One day.
2. Shadow CI job, non-blocking, with per-package cutover on parity — because it is the single mechanism that proves the reversibility the whole risk story rests on. Two to four weeks of wall time, little labor.
3. xdist pilot on two or three representative packages, recording baseline and speedup — before the proposal cites parallelism as a benefit. About a week.
4. Governance page, including the explicit funded-finish-line-or-accepted-mix decision — before declaring the plan complete. A day of writing, plus one genuine decision only you can make.

My reasoning: this debate ended in near-total convergence. The destination went uncontested, four of five objections resolved into amendments the Advocate adopted, and the fifth was dropped. The total gate cost is roughly two days of work plus shadow-CI calendar time, all before any hard-to-reverse step. The one decision the gates cannot make for you is Point A's residue: whether to fund a migration finish line. The Adversary's steelman-2 catch means that choice partly controls whether the parallelism benefit ever reaches isolation-unsafe packages — decide it with the pilot results in hand, not by default.

## Your decision

1. **Adopt as amended (recommended).** Run gate 1 this week, start the shadow job, run the pilot, write the governance page. Within the governance page, choose: (a) funded finish line with a date, or (b) permanent mixed estate accepted in writing.
2. **Adopt as originally written.** Swap the runner now, defer all gates. This accepts the fail-green collection risk that both debaters, independently, called the worst failure mode. No one in the transcript defends this option.
3. **Defer the decision until gates 1 and 3 report.** Costs one to two weeks; buys hard numbers before commitment. Rational only if you doubt the destination — which neither side does.
4. **Reject; stay on unittest.** The ecosystem-default argument stands unrebutted on this record. Choosing this means supplying an argument the debate did not produce.
