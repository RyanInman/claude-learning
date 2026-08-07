# User notes

Workarounds and judgment calls during the run:

1. **Inline proposal written to a file.** The skill requires every role to read the same
   fixed text, so I wrote the user's argument to `work/proposal.md` before starting.
2. **No codebase to inspect.** The debate concerns a monorepo that does not exist in this
   workspace. As Defender, I answered the Phase 2 questions honestly with "unmeasured /
   unknown / not stated" where the user's message gave no data. The debate therefore
   converged on verification gates (audit, pilot, shadow CI) rather than on numbers — the
   correct outcome given the missing data.
3. **Transcription trimming.** Two subagent replies wrapped their sections in meta lines
   ("My case is ready to paste", a note to the transcriber about line numbers). I
   transcribed the section content verbatim and dropped only the meta framing, which was
   addressed to me, not to the debate.
4. **Judge heading markers.** The Judge returned section headings as `### ## Agreed
   changes` (doubled markers). The transcript keeps them verbatim per the skill's
   transcription rule; in the standalone `final-report.md` I normalized them to `##` for
   readability. No words were changed.
5. **Session interruption.** The session hit a limit after answer.md and final-report.md
   were saved. The remaining outputs (transcript copy, metrics.json, this file) were
   written after the reset. No debate content was lost; the transcript was already
   complete on disk.
