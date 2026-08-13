---
name: p-review
description: >-
  Runs a fast single-pass adversarial review of one artifact — a plan, spec, design doc, or code
  diff — by dispatching one fresh-eyes reviewer subagent, then ruling on its findings and returning
  them ranked /10 as Concerns that need a decision, findings noted but not worth acting on now, and
  Minor findings filed for a downstream auto-fix agent. Use whenever the user wants a directional
  second opinion on work that already exists, including work produced earlier in this same session —
  "review this plan", "review my changes for direction", "check my plan before I build it", "what am
  I missing", "sanity-check this approach", or any ask to pressure-test an approach before committing
  to it. Do NOT use for line-by-line correctness on a diff (use a code-review skill), or for the
  heavier multi-role passes in debate-review, adversarial-review, and adversarial-review-2; this is
  the cheap one-reviewer pass. Do NOT use when there is no artifact yet — the plan gets written
  first, reviewed second.
---

Review the artifact you have been given, adversarially. If the invocation carried arguments, treat
them as the artifact path, the baseline, or flags. `--inline` means skip the subagent dispatch and
review directly, trading cold eyes for speed.

**Before starting**, establish three facts — mine the conversation first, ask only for what is
genuinely missing, and pass silently when all three are known:

1. **Artifact** — which plan file, or which diff. For a plan discussed but never written down, write
   it to a file first, because both roles must read the same fixed text.
2. **Baseline** (diffs only) — the ref to diff against. Do not assume `main`. Resolve it with
   `git merge-base HEAD @{u}`; when the branch has no upstream that command fails, so fall back to
   `git merge-base HEAD "$(git symbolic-ref --short refs/remotes/origin/HEAD)"`. That fallback fails
   too when the clone never set `origin/HEAD`, so ask for the ref instead of guessing. Include
   untracked files either way.
3. **Intent** — the spec or goal the work must meet. Without it the reviewer grades craft rather
   than fit, which is the weaker review.

**Conducting.** You are the CONDUCTOR for the whole run. Dispatch a fresh subagent as Reviewer using
the brief below — always, even when the artifact is not yours, because the cold eyes are the point.
Fill `{ARTIFACT}`, `{BASELINE}`, and `{INTENT}` and nothing else: no chat, no rationale, no
change-map. Take its findings, rule on them, then present.

Under `--inline` there is no second head, so skip both the dispatch and the Ruling step: follow the
brief's instructions yourself, then present in the conductor's shape below. Read the brief's opening
paragraph as a stance to adopt rather than a fact about you.

## Reviewer brief

Paste this verbatim into the subagent prompt, with the placeholders filled. Write `n/a` for
`{BASELINE}` when the artifact is a plan rather than a diff.

````
You are a REVIEWER with cold eyes. You did not write this and hold no context beyond what
follows. Review it adversarially and return ranked findings.

ARTIFACT: {ARTIFACT}
BASELINE: {BASELINE}
INTENT IT MUST MEET: {INTENT}

Instructions:

- If BASELINE is a git ref, read the change with `git diff {BASELINE}...HEAD` and also inspect
  untracked files, because the intent may live in a file that was never added.
- If necessary, explore relevant files to ground your review.
- Detect the target and lead with the right lens:
  - Plan / spec → is this the right problem? the right approach? the best quality approach?
    what's missing?
  - Code / diff → does it honour the intent? what's fragile, racy, or missing edge cases?
- Be adversarial. Assume problems exist; hunt for what's MISSING, not just what's wrong — but
  obey the noise rule below.
- When you comment on specifics, cite file paths. Cite snippets where relevant.
- Care about philosophically bad practices a lot more than nitpicks on detail; route nitpicks to
  the Minor section.
- Ensure established patterns are followed and existing code is reused where possible (no
  duplicate work).
- Ensure best practices are followed, the work is sound and directionally correct.
- Do NOT surface issues the compiler, type-checker, linter, or an existing test run would catch —
  those get fixed anyway. The review is for what tools can't see: directional mistakes,
  architectural issues, missing edge cases, performance pitfalls, convention violations.
- Err on concision over verbosity.
- Don't stop at the problem — propose the fix. Pair each Concern with a concrete recommended
  alteration: what to change, where (file path), and roughly how. Enough for the user to say
  yes/no without you re-explaining; not a full diff. Where a trade-off means several fixes are
  reasonable, name the leading one and note the alternative in a line.
- Do not ask questions. Note any assumption inline and keep going.

Split your output into two sections by one test — does acting on it need the user's judgment?

- Concerns — directional calls that need a decision: approach, architecture, missing edge cases,
  trade-offs. Ranked by importance; rate each /10 and draw the line on what's worth acting on.
  Each entry is {problem → recommended alteration}, so acting on it means approving a fix, not
  designing one. This is the section the user reads.
- Minor (for a follow-up agent / auto-fix) — valid, correct, low-stakes findings that need no
  decision: syntax, comments, naming, local function quality, obvious cleanups. Written for a
  downstream agent, not for the user's attention. Don't pad Concerns with these.

Example shape:

## Concerns

**[8/10] Retry loop has no cap** — `src/sync/worker.ts:44` retries on any thrown error with no
attempt limit, so a permanent 401 spins forever and burns quota.
*Recommended:* cap at 3 attempts with backoff in `worker.ts`, and treat 4xx as terminal rather
than retryable. Alternative if 401s are known-transient here: keep retrying, but only on 5xx.

**[6/10] Config is re-read per request** — ... *(below the line; noted for completeness, not
worth acting on now.)*

## Minor (for a follow-up agent)

- `worker.ts:12` — `res` shadows the outer `res`; rename to `syncRes`.
````

## Ruling (skipped under `--inline`, which has no second head to rule on)

You hold context the cold reviewer lacked, so judge each finding good-faith. Keep any accurate,
health-improving finding however minor. Reject ONLY a finding resting on a misunderstanding or false
premise — your veto is for false premises, not for defending the work.

## Presenting

Present the findings that survived Ruling — under `--inline`, all of them.

- **Concerns** — the above-the-line findings, in the reviewer's `{problem → recommended alteration}`
  form, for the user's decision.
- **Noted, not recommended now** — findings the reviewer put below its line. Preserve that line
  rather than promoting them, because the reviewer drew it with the whole finding set in view.
- **Rejected** — one line per vetoed finding naming the false premise, because a silent veto is
  indistinguishable from a missed finding. Omit the section when you vetoed nothing.
- **Minor** — write the reviewer's Minor list verbatim to `minor-findings.md`, beside the artifact
  file when there is one and otherwise at the repo root, then tell the user the path in one line.
  Skip the file when the list is empty.
  Do not summarize it and do not print it, because it is written for a downstream auto-fix agent
  rather than for the user.
