Debate review complete. Four roles ran the full six-phase debate: I defended the plan from its text, a fresh Adversary attacked it, a fresh Advocate steelmanned it, fresh agents rebutted both cases, and a neutral Judge ruled. Full transcript: `debate-review/transcript.md`. Judge's report: `outputs/final-report.md`. Here is what survives.

**Survives intact — the plan's core judgment:**
- Migrating to JWTs for shared web+mobile auth and Redis retirement. The Adversary withdrew his "misleading pitch" charge; the drivers are real.
- **RS256 over HS256.** The Adversary conceded this outright: with a mobile client one quarter out, asymmetric keys are correct, and their rotation story beats a shared HMAC secret.
- **Keys in environment variables.** No secret manager needed; both sides agreed the existing secret channel is fine.
- **24-hour access token for this migration** — narrowly, and only paired with the compromise below. The Advocate's unanswered point won it: shortening the TTL 96x in the same release that changes the auth mechanism makes cutover telemetry uninterpretable.
- **`localStorage`** survives as defensible-pending-facts, not vindicated. The unified-client argument moved the Adversary off "use cookies"; the remaining ask is to state your origin topology and CSP status and justify the choice against them in one sentence.

**Does not survive — both sides now agree:**
1. **The Goal sentence is technically wrong.** A shared session store is what *enables* horizontal scaling; JWTs remove a per-request round-trip, not a ceiling. Rewrite before pitching — a reviewer will catch it in five minutes.
2. **The "refresh tokens add server state, which defeats the purpose" justification is false as written.** The mandate is retiring Redis; a Postgres table retires Redis. The sentence underpins decisions 3 and 4 and has to come out even if you keep their outcomes.
3. **Single-release cutover.** The killer argument: rollback is not a revert. The cutover deploy destroys every session, so redeploying the previous image logs everyone out a second time and cannot verify the JWTs now in their browsers. Replace with a three-step staged cutover — dual-accept middleware (failing closed on a present-but-invalid `Authorization` header), canaried `/login` flag flip, then delete sessions and Redis once a `session_auth_used` counter reads zero for longer than the session TTL.
4. **Key management as specified.** "Generated at deploy time" is a production incident on either reading (per-deploy = mass logout every release; once = no rotation path for a leaked signing key). Fix in sprint 1: generated-once keys the pipeline never touches, `kid` in the header, current-plus-previous key set, JWKS endpoint.
5. **The claim set.** Add `iss`, `aud`, `jti`, and pin `algorithms=["RS256"]` explicitly. About an hour of work; parts become impossible to retrofit after the mobile binary ships.

**The one contested point:** refresh tokens now versus at mobile GA. The Judge split it: the Adversary won the diagnosis (24-hour unrevocable tokens mean password reset, suspension, and admin demotion are no-ops for a day — a real privilege-persistence bug), but the Advocate won the schedule. The compromise: keep the 24-hour token for this migration, add a `tokens_valid_after` column on `users` checked against `iat` (hours of work — closes password reset, suspension, and "log out everywhere"), and write refresh tokens plus a short TTL into the plan as a dated prerequisite for mobile GA rather than an unscheduled v2.

**Before you pitch, establish four facts (under a day, and two can reshape the plan):**
1. What else lives in Redis (`SCAN` + grep). If it also serves Celery, rate limiting, or cache, Redis does not get retired and the plan needs re-justifying on the mobile goal alone.
2. Whether any server-side session invalidation exists today (grep). If yes, the plan silently deletes a live security control, and by the Advocate's own concession the full refresh design moves into this migration.
3. Whether today's session TTL is fixed or sliding. If sliding, "matches our current session TTL" is false and the plan hides a policy change to hard daily logout.
4. Origin topology and CSP status — they decide the `localStorage`-vs-cookie question.

The Judge's recommendation is Option 4 in the report: run those four checks first, then adopt the ten agreed changes plus the `tokens_valid_after` compromise (roughly a day and a half of additions plus one extra release). The full option set is in `outputs/final-report.md` under "Your decision" — the call is yours.
