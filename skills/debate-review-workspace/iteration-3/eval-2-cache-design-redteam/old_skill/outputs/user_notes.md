# User notes — judgment calls and workarounds

1. **Overkill check resolved without asking.** The skill's setup step 1 says to offer the user a single-pass review if the artifact is small. Running unattended, I judged a full debate warranted: the design precedes a build commitment, and the user explicitly asked to "argue both sides properly." I proceeded without offering the lighter option.

2. **Defender role without authorship.** The skill assumes the main agent authored the artifact. I did not write cache-design.md and had no codebase to consult, so the Defender's opening argued only from the document, and Phase 3 answered the roles' questions "unknown" wherever the design is silent (pricing placement, traffic numbers, PM sign-off scope, worker class) rather than inventing plausible facts, per the skill's rule.

3. **Subagent meta-text trimmed during transcription.** The Phase 4 Adversary and both Phase 5 agents wrapped their sections in delivery notes ("ready to paste", "The section above ... is ready to paste verbatim", a ranking-rationale sentence outside the section boundary the agent itself defined). I transcribed each agent's self-delimited section verbatim and dropped only the wrapper text outside it.

4. **Judge heading levels adjusted in the transcript only.** The Judge returned its report with `##` section headings. Inside the transcript those would collide with the phase-level `##` headings, so I demoted them to `###` under "Phase 6". The standalone final-report.md keeps the Judge's original `##` levels. Wording unchanged in both.

5. **Session interruption.** The session hit a limit and was terminated after final-report.md and outputs/transcript.md were written; the coordinator restarted it to finish answer.md, metrics.json, and user_notes.md. No debate content was affected — all seven subagent runs and the full transcript completed before the interruption. Counted as 1 in metrics.json errors_encountered.

6. **Metrics definitions.** No metric schema beyond the key names was given. total_steps counts assistant turns that invoked tools (16). output_chars is the byte count of answer.md; transcript_chars is the byte count of outputs/transcript.md. files_created lists files this run created, including the working transcript.
