# Static tier - golden state

Weight: 15%. State capabilities, not tools. Per-ecosystem tool picks are recommendations:
oxlint and oxfmt, or ESLint and Prettier, in JS; analyzers and formatters in .NET.

## Golden state

- **The core four.** Typecheck; lint at zero warnings; format check; a boundary rule wherever
  the repo has an architectural seam worth defending. Example boundary rules: ban API-path
  literals outside the sanctioned client with `no-restricted-syntax`, or a dependency-cruiser
  rule that lets services import each other only through shared packages. With no seam, skip the boundary rule.
- **One aggregate `check` command per repo.** It chains the static steps fail-fast and prints a
  timing row per step. The pattern is canon.
  Any one implementation is replaceable.
  - Lead with `install --frozen-lockfile`, because a stale `node_modules` produces a false green.
  - Include secret scanning (gitleaks, about 1.5 s).
  - Add shellcheck and actionlint where shell scripts or CI workflows exist.
  - Add a cache-correctness guard where a caching runner (turbo, nx) gates tests: the cache key must declare every env var a
    test reads.
  - Include a dependency audit only when de-flaked: a high-severity gate plus a per-advisory
    ignore list with documented reasons. An unqualified audit breaks green with zero code change.
- **Prod-artifact boot smoke.** One per-PR CI job per deployable prunes to prod deps and
  boot-probes the artifact. Dev-dep leaks are invisible to every workspace-installed gate.
- **Custom lint rules for testing idioms.** Add one only on a conscious, human-ratified
  decision. The bar: the idiom was violated more than once, or a violation is expensive to
  diagnose. Enable autofix on every rule that supports
  it, and keep the linter fast. An agent never proposes a new rule
  ad hoc.
- **Hooks.** husky plus lint-staged autofix (`lint --fix` and format) on staged files only. Run
  no tests and no typecheck in hooks, because CI is authoritative. Hooks are default
  equipment: recommend them whenever they are missing.
- **CI.** Lint and typecheck jobs run on every PR.

## Brownfield ramp

Never swap an incumbent formatter or linter. Remediate in the repo's existing ecosystem, in
this order:

1. The missing core-four members.
2. The aggregate command.
3. Hooks.
4. The near-free extras: gitleaks, shellcheck, actionlint.
5. A boundary rule, when a seam emerges.

## Greenfield

Require the core four, hooks, and the aggregate command from day one. Add each extra when its
precondition appears: the first shell script, CI workflow, cached test task, or deployable.

## Operability affordances (also owned by this sub-agent)

Sweep the operability row of `rubric.md` Part 1 from artifacts only. Check for:

- An AGENTS.md routing table: change-type → exact command plus known failure modes.
- A one-command dev stack with an idempotent reset.
- Seeds and test accounts.
- Probe or screenshot tooling.
- Prerequisite errors that name their fix in one line ("run db:seed").
