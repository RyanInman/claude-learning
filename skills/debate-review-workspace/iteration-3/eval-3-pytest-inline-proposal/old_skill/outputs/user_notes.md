# User notes — judgment calls and workarounds

1. **Overkill check passed without asking.** The skill says to offer a single-pass review for tiny or cheaply reversible artifacts. Migrating a 6k-test monorepo is neither, and the run is unattended, so I proceeded with the full debate and recorded the call here instead of asking.

2. **Inline proposal written to a file.** Per skill Setup step 2, I wrote the request verbatim plus a structured restatement to `work/pytest-migration-proposal.md` so every role reads the same fixed text. The restatement adds no facts beyond the quoted request.

3. **Defender did not author the artifact.** The proposal is the user's, not mine. I played the Defender from the user's stated case only. Nearly every clarifying question (suite metrics, CI integrations, end state) had no answer in the request, so Phase 3 answers are mostly "unknown", as the skill requires, rather than plausible stipulations.

4. **Subagent type.** roles.md says to spawn role subagents read-only where supported. I used the read-only `Explore` agent type for all six Adversary/Advocate/Judge spawns so transcript edits were impossible rather than forbidden.

5. **Duplicate headings dropped during transcription.** Some subagents returned their section with its own top heading (e.g. `## Phase 4 — Advocate's case`, `# Phase 6 — Judge's Final Report`) duplicating the template's existing heading. I pasted the body verbatim under the template heading and dropped only the duplicate heading line. No body text was altered.

6. **Session interruption.** The session was terminated by a session limit after the Phase 5 rebuttals were returned but before they were transcribed. On resume I verified phase state from the transcript on disk (Phases 1–4 present, Phase 5 placeholders intact), transcribed the already-returned rebuttals, and continued with Phase 6. Counted as 1 in `errors_encountered`; no debate content was lost or regenerated.

7. **final-report.md extraction.** I generated the standalone Judge report by extracting the Phase 6 section from the transcript (awk) and prepending a title line, rather than retyping it, to guarantee it matches the transcript verbatim.

8. **metrics.json definitions.** `total_steps` counts assistant messages that invoked tools. `output_chars` is the byte count of answer.md; `transcript_chars` is the byte count of outputs/transcript.md. `files_created` lists files this run created (the outputs/transcript.md copy included); it excludes nothing else.
