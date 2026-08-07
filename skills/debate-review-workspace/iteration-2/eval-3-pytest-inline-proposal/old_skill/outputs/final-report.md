
## Agreed changes

All three roles converged on six amendments. Each is ready to act on, and per the
Adversary's condition (accepted by the Advocate in Phase 6), every one must be written
into the proposal text itself — an amendment living only in this transcript is not policy.

1. **Named conversion owner.** One person owns the incremental migration and its progress.
   (From Adversary Objection 1; accepted Phase 4, drop conditioned and confirmed Phases 5–6.)
2. **New-tests-are-pytest rule.** New test files must be pytest-style from cutover onward,
   so the TestCase count only falls. (Same provenance as item 1.)
3. **Collection-parity hard gate.** Before CI switches runners, diff unittest discovery
   against `pytest --collect-only -q` and require the test-ID sets to match, or every
   difference explained in writing. (Adversary Objection 3; conceded in full by the
   Advocate — the debate's cleanest exchange.)
4. **One-page interop guide with the seam rule.** Suite-wide autouse fixtures must be
   TestCase-safe: ambient effects only (per-worker database names, tmp roots, ports keyed
   off worker id), no arguments the test body must receive. Value-consuming isolation for
   an unconverted subtree is written in unittest idiom until that subtree converts.
   (Adversary Objection 4, narrowed; Advocate accepted the rule while winning the
   severity argument — see Contested points.)
5. **Three pre-cutover checks as hard gates, roughly two days of read-only work:**
   the CI coupling audit, the collect-only diff (item 3), and a `pytest -n auto` spike
   against a recorded unittest wall-clock baseline. (Adversary Objections 2 and 5;
   endorsed by the Advocate in Phase 4.)
6. **Conditional-approval structure.** Approval of the direction is written as
   conditional: the three gates carry pre-agreed pass criteria, and any failed gate
   returns the proposal for re-decision, not remediation-by-default. (Adversary's Phase 5
   compromise, accepted by the Advocate in Phase 6 "in full and as worded.")

## Contested points

None remain. For the record, how each resolved — and who won where the sides genuinely
disagreed:

- **Objection 1 (headline benefits deliver nothing).** The Advocate won on the merits.
  The denominator correction — fixtures and parametrize pay on every new test, and a
  monorepo writes test 6,001 next week — was a real refutation, and the Adversary said so
  when dropping it. The ratchet items survived as agreed changes 1–2.
- **Objection 2 (xdist unmeasured, non-differentiating).** The Advocate won the argument
  (CI sharding costs exactly the runner infrastructure the proposal avoids); the
  Adversary won the procedure (the spike is now a hard gate). Both halves stand.
- **Objection 3 (silent test drops).** The Adversary won outright; the Advocate conceded
  in Phase 4 and never wavered.
- **Objection 4 (two-idiom tax).** Split, and fairly so. The Adversary's technical claim
  was correct — conftest autouse fixtures cross the seam with no one deliberately mixing
  idioms, which broke the Advocate's Phase 4 defense. The Advocate then won on severity:
  xdist isolation work is overwhelmingly ambient, not injected, so it reaches all 6,000
  TestCase tests as ordinary pytest. The accepted seam rule (agreed change 4) codifies
  the Advocate's design under the Adversary's constraint.
- **Objection 5 (sequencing).** The Adversary's proof that "tests born pytest-style
  during the spike fortnight" is technically impossible was exact, and the Advocate
  conceded it. The conditional-approval compromise then genuinely dissolved the dispute:
  it answers the Advocate's relitigation concern and the Adversary's anchoring concern
  with one mechanism. Both sides declared the distance zero; I verified the exchange and
  agree.

## Compromises

None needed — all objections resolved in debate. (The one formal compromise, conditional
approval with pre-agreed gate criteria, was proposed by the Adversary inside Phase 5 and
accepted by the Advocate inside Phase 6, so it appears above as agreed change 6 rather
than as a Phase 7 brokered item.)

## Judge's recommendation

**Adopt the amended proposal under the conditional-approval structure — with one task the
debate left unfinished: quantify the two gate criteria that are still words, not numbers.**

The convergence here is real, not performative. I checked each drop and concession
against the argument that produced it: Objection 1 fell to an actual counter-argument,
Objection 3 was conceded against interest, and Objection 5's resolution required the
Advocate to abandon a claim the Adversary had proven impossible. No one split differences
to look agreeable.

The amended proposal is also strictly stronger than the original. The Defender's opening
honestly flagged three unknowns (CI coupling, shared state, compatibility limits); the
debate converted all three from open risks into gated checks. The Advocate's best
structural point holds throughout: the compatibility-bridge cutover is what makes every
one of these checks cheap, which is evidence the core design was right.

The unfinished task: agreed change 6 requires "pre-agreed pass criteria," but two of the
three gates still lack numbers. Gate 1's criterion is "no runner-API coupling beyond an
agreed effort bound" — no bound was agreed. Gate 3's is "a measured wall-clock gain" —
any gain, or a meaningful one? A conditional approval whose conditions are vague
reintroduces exactly the remediation-by-default risk the compromise exists to prevent.
Set both numbers (for example: an effort bound in engineer-days for CI remediation, and a
minimum speedup or pass-rate threshold for the xdist spike) before signing the approval.
Gate 2, collection parity, is already precise.

## Your decision

You are choosing between four options:

1. **Conditional approval as amended** (my recommendation). Approve pytest as the
   destination now; write agreed changes 1–6 into the proposal text; set the two missing
   gate numbers; run the ~2-day checks; cut over only if all three gates pass, and return
   to re-decision if any fails.
2. **Split decision.** Approve only the 2-day spike now and re-present the proposal with
   the three measurements attached. This was the Adversary's original Objection 5
   position; he moved off it, but it remains coherent if you distrust conditional
   approvals surviving bad news in your team's culture.
3. **Runner switch only.** Re-scope to the cutover benefits alone (unified invocation,
   reporting, selection, xdist on TestCase tests) with no conversion program. The debate
   established this floor is positive, but both sides agreed the ratchet items are cheap,
   so choosing this forfeits value for little saved cost.
4. **Reject / status quo.** Keep unittest. Nothing in the debate supports this — even the
   Adversary opened by accepting pytest as the better tool — but it is the null option
   you are entitled to.
