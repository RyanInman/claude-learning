# Debate review: switch the Python monorepo from unittest to pytest

I ran your proposal through a structured four-role debate: a Defender presented your case, a fresh-eyes Adversary attacked it (5 objections), a fresh-eyes Advocate steelmanned it, both sides rebutted, and a neutral Judge ruled. Full transcript and the Judge's complete report are saved alongside this reply. Here is the outcome. You get final say.

## Bottom line

**The Judge recommends approving the switch, with preconditions.** Nothing in the debate argues for staying on unittest. But the debate materially changed which arguments should carry the decision, and it surfaced one risk that would have hurt you.

## What happened to your three arguments

- **"Fixtures beat setUp inheritance"** survived, narrowed. The monorepo version is the strong form: conftest.py scopes fixtures by directory, which maps onto team ownership, and composition by request beats single-lineage inheritance. Two corrections stuck: a root conftest.py can ossify exactly like a shared base TestCase, and fixtures reach your existing TestCase tests only through autouse, the least visible form. Also, a session-scoped fixture runs once per xdist worker, so the fixture and parallelism wins do not stack without lock coordination.
- **"parametrize kills copy-pasted variants"** survived fully on mechanism. The Adversary conceded outright that subTest is not close: per-case selection, per-case reporting, per-case xfail, and a one-line cost to add a case. Caveat: parametrize does not work on TestCase methods, so this pays off only on new and converted tests.
- **"Plugins give xdist parallelism for free"** was the weakest claim and the Judge struck it from the justification for now. Parallel safety of your suite is unverified, the safe day-one mode (--dist loadfile) is behaviorally close to CI-level file sharding you could do without pytest, and nobody knows your current CI wall-clock. A one-day spike (run pytest and pytest-xdist over the tree unchanged, record three numbers) reprices this claim with data.

The two arguments that emerged strongest were ones you did not make: **the asymmetry** (pytest runs unittest.TestCase natively, unittest cannot run pytest-style tests, so every week of delay grows the conversion inventory) and **the ecosystem** (pytest-django, pytest-asyncio, pytest-mock, Hypothesis all target pytest; unittest is frozen at the stdlib; new hires arrive knowing pytest). The Adversary called the ecosystem point the strongest directional argument in the transcript and conceded the direction because of it.

## The risk the debate caught

pytest silently ignores the `load_tests` protocol and bypasses custom `TestRunner`/`TestResult` subclasses. If your monorepo uses any of those (unknown), tests stop being collected or reporting stops firing, and CI stays green while running fewer tests. Both sides agreed this is a hard precondition: **diff collected test IDs between the two runners and require an empty or fully explained diff, grep for `load_tests`/`TestRunner`/`TestResult`/custom base classes, and run both runners in CI for one to two weeks before removing the old one.** Run the parity diff before enabling xdist, or a shrunken suite masquerades as a parallelism speedup.

## What both sides agreed you should add (about two days of work)

1. The collection-parity gate above.
2. A scope sentence: adopt pytest as the runner now; convert TestCase files only when already modifying them; any wholesale conversion of the 6k tests is a separate future decision that needs its own price.
3. The one-day xdist spike, before flipping CI but not gating the go/no-go.
4. Two baselines: CI wall-clock p50/p90 from history, plus a written success criterion.
5. Name the dual-idiom period honestly: under opportunistic conversion it is permanent, not transitional. Accept that in writing, and build a `testsupport` bridge on day one (shared setup as plain functions; a fixture wraps it, setUp calls it) so setup logic is never written twice.
6. Add one downside line: a pinned third-party runner and plugin matrix on every merge's critical path, replacing a stdlib dependency.

Your "some devs know unittest well" downside was judged near-zero: nobody unlearns unittest, pytest keeps running their tests, and the authoring model they would adopt is simpler, not harder.

## Your decision

- **Option 1 (Judge's recommendation):** approve the switch with the six items above attached.
- **Option 2:** split into two formal decisions, runner swap now, conversion priced later. Choose this if you expect the runner-swap approval to be treated organizationally as approval of a full conversion campaign.
- **Option 3:** approve as-is with only the collection-parity gate. Cheapest, but the deflated xdist claim stays in your pitch as justification.
- **Option 4:** decide nothing until the spike and CI numbers land. The Judge argues against this, since the direction rests on an argument no measurement can overturn.

My read matches the Judge: Option 1. Your pitch gets stronger, not weaker, if you drop "xdist for free," lead with the asymmetry and ecosystem arguments, and show up with the parity gate already run.
