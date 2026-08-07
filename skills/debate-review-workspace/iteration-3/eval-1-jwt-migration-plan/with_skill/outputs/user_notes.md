# User notes — judgment calls and workarounds

1. **Session interruption mid-run.** The session terminated after transcribing the Adversary's phase-5 rebuttal. The Advocate's rebuttal had already been returned by its subagent but was not yet on disk. On resume I verified the transcript state (phases 1 through 5-Adversary complete), transcribed the Advocate's rebuttal verbatim from the retained subagent reply, and continued with phase 6. No phase was re-run, so the fresh-eyes constraint held. Counted as 1 in `errors_encountered`.

2. **Defender role without authorship.** I did not write the plan, so per the skill I presented only the case the artifact makes and answered all six clarifying questions from its text, marking every unstated fact "unknown" (session TTL behavior, Redis usage beyond sessions, deploy/rollback mechanism, keypair lifecycle, threat model, origin topology). No facts were stipulated.

3. **Overkill check.** The skill requires offering a single-pass review instead when the artifact is small or cheaply reversible. An auth migration for a 40k-DAU product is neither, and the run is unattended, so I proceeded with the full debate without asking.

4. **Judge report title in transcript.** The Judge returned a top-level `# Debate Review — Judge's Final Report` heading. The standalone `final-report.md` keeps it and the `##` sections verbatim. In the transcript I dropped that title line (it duplicates the phase heading — packaging, not wording) and demoted section headings one level to nest under `## Phase 6`, per the skill's transcription rule.

5. **Subagent type.** Role subagents ran as the read-only `Explore` agent type, matching the skill's "spawn each role subagent read-only where the harness supports it," so transcript edits by subagents were impossible rather than forbidden.

6. **metrics.json interpretations.** `output_chars` = character count of answer.md (the user-facing reply); `transcript_chars` = outputs/transcript.md. `total_steps` = number of assistant turns that invoked tools, plus the final reply turn. `files_created` lists files this run created (the transcript working copy and the five outputs); the input plan already existed.
