# Scenario design

Use this file when writing the scenario index, and when judging existing scenarios in
evaluation-only mode.

## The survives-a-rewrite rule

A scenario must still pass when the internals are rewritten from scratch, as long as observable
behaviour is preserved. Move any assertion that breaks under a non-behavioural refactor down to
a unit or integration test.

## Rules

- **Boundary first.** Write no scenario until both boundary lists (outside and inside) exist and
  share no item.
- **Given / When / Then.**
  - Given is the world state: seeded data and the minted identity.
  - When is one observable user action.
  - Then asserts only on observable outputs.
- **Stop sign.** "And the FooService was called" is an internal assertion. Replace it with the
  resulting observable, or move the test down a tier.
- **"And nothing else happened" is valid.** Use it in fan-out and dedup scenarios: no extra
  emails, no extra rows.
- **Negative pinning.** When current behaviour is deliberately nothing (a swallowed error, an
  intentional no-op), write a test that pins the absence. A future change then has to be
  deliberate.
- **Provider recorders.** When a third-party side effect (email, push, payment) is the
  observable under test, specify one recorder per provider with a `received()` or
  `waitFor(predicate)` shape. Name the seam the recorder attaches to.
- **Async waits by design.** At plan time, name how each eventual-consistency seam is waited
  on: an event-driven wait, a polled predicate with a deadline, or a stepped stage (rung 3).
  Deciding this flake by flake produces retries and sleeps.

## Example

Before (breaks under a refactor):

```text
Given a signed-in user / When they upload a PDF / Then DocumentQueue.enqueue was called once
```

After (observable only):

```text
Given a fresh user / When they upload a PDF / Then the document list shows it as "Processing", and within 60 s as "Ready"
```
