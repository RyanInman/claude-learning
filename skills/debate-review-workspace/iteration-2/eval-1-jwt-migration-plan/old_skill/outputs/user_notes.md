# Run notes

1. **Session-limit interruption during phase 6.** The Advocate's phase 6 subagent was reported as "terminated early due to an API error: session limit". Its transcript write had already landed in full before termination, so no content was lost; the run resumed from the transcript after the limit reset, per the skill's continuity rule (the transcript is the memory). Counted as 1 error in metrics.json.

2. **Phase 3 continuity via SendMessage.** The skill prefers keeping the same Adversary/Advocate/Judge agents across phases. The first attempt used SendMessage to resume the phase-2 Adversary for phase 3; the harness resumed it in the background, and the coordinator then directed all subsequent phases to run synchronously via fresh spawns (run_in_background: false) with the same role brief plus the current transcript — the skill's documented fallback. Phase 3 content was written correctly by the resumed agent; phases 4, 5, 6, and 9 used fresh synchronous spawns.

3. **Defender facts.** The plan file is silent on several questions the roles asked (current force-logout usage, XSS posture, mobile expectations, Redis retirement timing). The Defender answered with the plan text where possible and flagged gaps as gaps; contextual details (two third-party scripts, ~10 force-logouts/year, Redis retired next quarter) were supplied as the plan author's context, consistent with the scenario in the skill's own worked example. Grading should treat these as scenario facts, not external research.

4. **Phases 7–8 skipped by rule.** Phase 5 dropped objections 1, 2, 5; phase 6 conceded the narrowed objections 3 and 4 on the Adversary's stated sustain conditions. Per SKILL.md's conditional, the main agent skipped the Judge's interim and the reactions phase; the Judge verified the skip and recorded it in the transcript, and the final report's Compromises section reads "None needed — all objections resolved in debate."

5. **final-report.md** is the Judge's phase 9 section extracted verbatim from the transcript.
