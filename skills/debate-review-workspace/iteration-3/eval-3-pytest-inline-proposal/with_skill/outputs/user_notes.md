# User notes — judgment calls and workarounds

1. **Inline proposal written to a file.** The skill requires every role to read the same fixed text, so I wrote the request's inline proposal verbatim (plus a structured restatement) to `work/pytest-migration-proposal.md` before Phase 1.

2. **Overkill check passed without asking.** The skill says to offer a single-pass review when the artifact is tiny or the decision cheaply reversible. The artifact is short, but the decision (6k-test monorepo migration) is not cheaply reversible, and the run is unattended, so I ran the full debate.

3. **Defender played as non-author.** The proposal is the user's, not mine. Per the role brief I presented only the case the artifact makes plus real context from the request, answered most clarifying questions "unknown" (CI setup, parallel safety, team size, counts), and flagged general pytest facts (unittest compatibility limits) as general knowledge rather than codebase facts.

4. **Session interruption.** The session was terminated after transcribing the Adversary's Phase 5 rebuttal and restarted by the coordinator. On resume I verified transcript state on disk before continuing. The Advocate's Phase 5 rebuttal had not yet been transcribed; I transcribed it from the retained tool result verbatim.

5. **Self-inflicted transcript defect, fixed.** My Phase 1 edit accidentally left a duplicate empty "Phase 2" heading block in the transcript. The Phase 4/5 subagents read the transcript with that duplicate present (harmless: empty placeholders, then the filled sections). I removed the duplicate on resume. Side effect: the Advocate's rebuttal cites "transcript line 27" for the Defender's compatibility note; after the fix that content sits ~10 lines earlier. The quoted text is unambiguous, so I left the citation untouched per the verbatim-transcription rule. The Judge repeated the line-27 citation; same caveat applies.

6. **Subagent choice.** Role subagents ran as the read-only Explore type, per the roles.md instruction to spawn roles read-only where the harness supports it, so transcript edits by subagents were impossible rather than forbidden.

7. **metrics.json definitions.** `total_steps` counts assistant messages that issued tool calls. `errors_encountered` = 2: the session termination and the duplicate-heading defect I had to repair. `output_chars` = size of answer.md; `transcript_chars` = size of the completed transcript.
