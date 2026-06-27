# Building a characterization net when no trustworthy tests exist

The zero-regression guarantee is a property of the test net, not of the model.
When the baseline is red, broken, or absent, the honest move is not "refactor
anyway and hope" — it's to **build a behavior-locking net first**, then refactor
under it. This is the inversion at the heart of safe AI refactoring: you cannot
prove behavior was preserved against a suite that doesn't exist.

Characterization tests (a.k.a. golden-master / approval / snapshot tests) capture
**what the code actually does right now**, not what it should do. A bug in current
behavior gets locked in too — that's correct. The job here is detecting *drift*,
not judging correctness. A human decides later whether a detected change was
intended.

## When to build a net vs. when to stop

Build a net when current behavior is observable and characterizable: pure
functions, request→response handlers, CLI in→out, serializable transforms.

Do **not** proceed with direct edits at all — net or no net — when:

- Behavior can't be characterized (heavy nondeterminism, external side effects you
  can't capture or stub), **or**
- The code touches auth, crypto, payments, or sensitive data.

In those cases use the model for analysis and explanation only, and tell the user
why. A flimsy net is worse than an admitted gap: it reads as proof when it isn't.

## The fast path — approval / golden-master testing

The quickest way to get untested code under a net is to pin its output:

1. Pick the surface the audit findings touch (the module/file/function set).
2. Drive it with a broad range of representative inputs — include edge cases the
   findings hint at (the null path, the empty list, the boundary value).
3. Capture the serialized output and commit it as the approved baseline.
4. On every later run the test re-drives the code and diffs against the approved
   output. Any difference fails the test.

Scrub non-deterministic values before approving — timestamps, GUIDs, random
seeds, ordering that isn't guaranteed — or the baseline is unstable and the net
cries wolf. An unscrubbed snapshot is a net with holes.

Framework pointers (use what the project already has; match its conventions):

- **.NET / C#** — Verify (`.verified.*` snapshot files, rich scrubbing, diff-tool
  launch on mismatch). ApprovalTests.Net is the older alternative.
- **React / TypeScript** — Vitest/Jest + React Testing Library; test behavior the
  way a user interacts (`getByRole`) so tests survive the refactor. Add a
  Playwright flow for user-visible paths. Keep snapshots small and scoped — a
  giant auto-snapshot that reviewers rubber-stamp is not a net.
- **Python** — pytest with a captured-output fixture, or syrupy for snapshots.

## Prove the net actually holds (optional, for high-stakes refactors)

Coverage lies: high line coverage with weak assertions lets regressions ship
green. Mutation testing (Stryker.NET / StrykerJS) deliberately introduces faults
and checks your tests catch them — the only practical way to prove the net is real
before trusting it to guard an AI's edits. A surviving mutant means a fix the net
can't see; strengthen that test before refactoring. It's expensive — reserve it
for logic-heavy or high-risk modules, run it once before the refactor (not per
finding), and skip it for low-stakes mechanical cleanups.

LLMs left to pad coverage write a large fraction of assertion-light tests that
execute lines without checking anything — mutation testing is what prunes them.

## After the net is green

Re-run Phase 1's baseline capture against the new suite. Now `ok: true` and the
full guarantee is in force — proceed to scope negotiation with a real net under
you, not an `unverified` tag.
