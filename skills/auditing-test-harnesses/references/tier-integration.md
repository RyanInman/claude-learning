# Integration tier - audit lens

Weight: 30%, the heaviest tier.

The golden state for this tier lives in one place: the `scaffolding-integration-tests` skill.
Invoke it with the argument `evaluation-only`. It runs its discover and plan phases, then stops
before implementation. Its plan is this tier's golden-state evidence. Cite the skill in the
working doc and the report. Restate its content nowhere, because two copies drift apart.

## What to check

The golden state of each item lives in the scaffold skill.

- **DB isolation.** Which ladder rung is the repo on? Does every merge-gating suite sit at or
  above rung 1 (fresh state per run)? Where rung 0 appears, is a move-up path stated?
- **Post-run inspectability.** Does cleanup run at next-run start? Are connection coordinates
  printed? Is auto-reap CI-only?
- **Provisioning.** Who boots the DB: the suite (Testcontainers), compose plus a preflight
  check, or a human with tribal knowledge?
- **Parallelism.** Is the suite serial, or clone-per-file with every stateful dependency
  per-worker and the connection budget sized? Parallel workers on one shared schema are a
  finding.
- **System tier.** Do the triggers exist (queues, outbox or relay, workflow engines, SSE)? The
  booted-stack lane must exist exactly when they do. A missing lane and an unjustified lane
  are both findings.
- **Live tier.** Does each costly external seam have a documented default-off flag, absence from
  the PR gate, a paired default-suite substitute, and a routing-table entry?
- **Auth.** Is auth real when light and minted when heavy? Is any mirrored authz drift-checked
  against the real catalog?
- **Breadth.** Do API servers have an endpoint-coverage gate? Once the suite runs longer than about one
  minute, does it offer suite / one / tag granularity?

## Remediation

Route every remediation row to `scaffolding-integration-tests` as the action. That skill owns
the brownfield climb order, the jump-to-rung-3 preconditions, and the greenfield choices.
