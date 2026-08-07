# unittest → pytest: debate review result

**Bottom line: switch, but sign it as a conditional approval with three hard gates, and write six amendments into the proposal first.** That is the Judge's recommendation after a full four-role debate (Defender, Adversary, Advocate, Judge). You have final say; your four options are at the end.

Full transcript: `outputs/transcript.md`. Judge's report: `outputs/final-report.md`.

## How the debate went

The Adversary opened by accepting that pytest is the better tool, then attacked the proposal as argued with five objections. None survived as a pure attack. Two fell to counter-arguments, one the Advocate conceded outright, and two resolved into amendments both sides accepted word for word. The Judge verified each concession traced to real evidence, not politeness.

## What happened to your three arguments

1. **Fixtures beat setUp inheritance: survived, with a correction.** Unconverted TestCase tests cannot receive fixtures as arguments, so the payoff comes from every *new* test, not the existing 6,000. The Adversary's strongest framing ("the headline benefits deliver near-zero value under an opportunistic migration") collapsed when the Advocate pointed out the denominator: a monorepo writes test 6,001 next week, and every test from cutover onward gets fixtures immediately.
2. **Parametrize kills copy-pasted variants: survived, same correction.** It pays on new tests at once and on old tests only as they convert. The fix is structural, not aspirational: a rule that new test files must be pytest-style, plus a named conversion owner.
3. **Plugins give xdist parallelism "for free": survived the argument, not the word "free."** Building parallelism on unittest means owning shard assignment, balancing, and result merging, exactly the infrastructure the proposal avoids, so pytest genuinely differentiates here. But the speedup is unmeasured, and it only arrives if tests are isolated (no shared databases, ports, globals). A half-day `pytest -n auto` spike against a recorded baseline is now a hard gate.

## What the downsides turned into

- **6,000 existing tests.** Not a rewrite: pytest runs TestCase classes natively, so the cutover touches zero test files and rollback is a one-line revert. The real risk hides elsewhere: pytest's collection is not identical to unittest discovery (`load_tests` is not honored, subtest support is partial), so a naive switch can silently drop tests while CI stays green. The Advocate conceded this in full. Fix: a collection-parity gate, one script that diffs test IDs between the two runners before CI switches.
- **CI churn.** Still unscoped, and honestly flagged as the least-certain point. It becomes a one-day audit gate: if CI only invokes a command line and reads JUnit XML, the churn is a config edit; if it couples to unittest's runner API, the cost estimate must grow and the proposal returns for re-decision.
- **Devs know unittest well.** The learning curve argument mostly ran the other way (pytest is the ecosystem default; new hires arrive knowing it). The one real trap the Adversary proved: `conftest.py` autouse fixtures apply to TestCase tests implicitly, so the two-idiom seam leaks even when nobody mixes idioms on purpose. Fix: a one-page interop guide with a seam rule (suite-wide autouse fixtures must be TestCase-safe, ambient effects only).

## The six agreed amendments

All three roles converged on these; each must go into the proposal text, not just the debate record.

1. Named conversion owner.
2. New test files must be pytest-style from cutover onward.
3. Collection-parity hard gate before CI switches runners.
4. One-page interop guide with the TestCase-safe autouse-fixture seam rule.
5. Three pre-cutover checks (~2 days, read-only): CI coupling audit, collect-only diff, xdist spike against a recorded wall-clock baseline.
6. Conditional-approval structure: the three gates carry pre-agreed pass criteria, and any failed gate returns the proposal for re-decision, not remediation-by-default.

## Judge's recommendation

Adopt the amended proposal under the conditional-approval structure, with one task the debate left unfinished: two gate criteria are still words, not numbers. Set an effort bound (engineer-days) for acceptable CI remediation, and a minimum speedup or pass-rate threshold for the xdist spike, before signing. A conditional approval with vague conditions reintroduces the "we decided; find a way" risk the structure exists to prevent.

## Your decision

1. **Conditional approval as amended** (Judge's recommendation): approve pytest as the destination now, write in amendments 1–6, set the two missing numbers, run the ~2-day checks, cut over only if all three gates pass.
2. **Split decision:** approve only the 2-day spike now and re-decide with the three measurements in hand. Coherent if you distrust conditional approvals surviving bad news in your team's culture.
3. **Runner switch only:** take the cutover benefits (unified invocation, reporting, selection, xdist on TestCase tests) with no conversion program. Positive value, but forfeits the cheap ratchet items.
4. **Status quo:** keep unittest. Nothing in the debate supports this; even the Adversary opened by accepting pytest as the better tool.
