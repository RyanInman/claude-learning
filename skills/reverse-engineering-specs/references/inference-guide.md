# Turning Scanned Code into Requirements

## Contents
1. The six lenses
2. Evidence discipline
3. Confidence levels
4. Diff mode differences

---

## 1. The six lenses

Apply each lens to `scan.json` plus any file you opened directly; skip a lens
only when it genuinely yields nothing for this target, and say so ("No
side-effect signals observed"). A requirement can come from more than one
lens — cite all of them.

1. **Public interface / contract** — every exported function, class,
   route, or CLI flag in `signatures` is a promise to callers. Its
   parameters and return shape imply a requirement even before you read the
   body ("the endpoint accepts a `userId` and returns a `Session`").
2. **Validation & error handling** — every `behavior_signals` hit
   (`raise`, `throw`, `validate`, `required`, `if not ...`) is a rejected
   input or state, and a rejected input is a requirement: "the system
   rejects X" is just as real as "the system accepts Y." Read the
   surrounding excerpt to get the exact condition, not just the keyword.
3. **Business logic branches** — `if`/`else`/`switch`/pattern-match
   branches in a signature's excerpt each imply a conditional requirement
   ("when the account is suspended, the request is rejected with 403").
   A branch with no corresponding test is still a requirement — it just
   gets `confidence: medium` or `low` (see §3) instead of `high`.
4. **Side effects & integrations** — writes, external calls, events,
   queue publishes, cache invalidations. These are requirements about what
   the system *does*, not just what it *returns* — easy to miss if you only
   read the return statement.
5. **Tests as requirement evidence** — a `paired_test` is the strongest
   evidence available: a passing assertion is a requirement someone already
   agreed to in code. Open the paired test and cite the specific assertion,
   not just "has a test." A signature with no paired test is not
   unrequired — it is lower-confidence and worth a note in Open Questions
   ("no test found for the retry-limit branch").
6. **Non-functional signals** — timeouts, retries, rate limits, auth
   checks, idempotency keys. These read as incidental code but are usually
   deliberate requirements ("requests are retried up to 3 times with
   backoff") — don't fold them into a functional requirement's AC; give
   them their own.

## 2. Evidence discipline

- Every requirement cites at least one `path:line` from `scan.json`'s
  `signatures`/`behavior_signals`, or a test name from a `paired_test`. A
  requirement with no citation does not go in the Requirements table — it
  goes in Open Questions instead (see `references/spec-format.md`).
- `scan.json` excerpts are truncated for budget reasons (see the skill's
  Gotchas). If an excerpt is truncated exactly where the interesting branch
  would be, open the file directly and cite the real line number from
  there, not the truncated one.
- Quantify where cheap: "rejects 4 of the 5 fields in the payload if
  empty" carries more weight than "validates the payload."

## 3. Confidence levels

- **high** — directly observed in a signature body or behavior signal, and
  either has a paired test or is unambiguous from the code alone (e.g. a
  type check that raises).
- **medium** — observed in code but no test found, or inferred from a
  branch whose exact trigger condition required judgment to read.
- **low** — inferred from absence (e.g. "no validation seen for field X, so
  presumably any value is accepted") or from a signature name/shape without
  reading the full body. Low-confidence items still get a Requirements row
  (do not silently drop them) but stay out of any Acceptance Criteria until
  confirmed — write the AC as a question in Open Questions instead.

## 4. Diff mode differences

- Lead with what the diff's `diffs` entries show as *new or changed*
  behavior; use the post-change `signatures`/`behavior_signals` (already
  extracted at `--head`) to write the requirement, and cite the commit
  range alongside the file:line (e.g. "`c94fa06`, `extract_branch.py:81`").
- A requirement already present before the diff (untouched by it) does not
  belong in this spec — Diff mode specs describe what changed, not the
  whole surrounding system. If the change touches a file without changing
  its observable behavior (e.g. pure refactor), say so in Out of scope
  rather than inventing a requirement.
