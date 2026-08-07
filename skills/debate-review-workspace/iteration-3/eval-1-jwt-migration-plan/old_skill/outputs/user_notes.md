# Judgment calls

1. **Overkill check ran silently.** The skill's setup step 1 offers the user a single-pass review for tiny artifacts. Run was unattended, and an auth migration for a 40k-DAU product is clearly above the bar, so I proceeded with the full debate without asking.

2. **Defender without author context.** The skill assumes the main agent authored the artifact and holds private context (deadlines, past incidents, rejected alternatives). I had only jwt-migration-plan.md. Per the phase-3 rule, I answered every unmeasured operational fact (XSS posture, Redis costs, revocation frequency, deploy duration, rollback testing) as "unknown" rather than stipulating plausible answers.

3. **Keypair-wording ambiguity.** For "generated at deploy time" I stated the likely intent (generate once, carry forward in env vars) but flagged the literal per-deploy reading as an unguarded ambiguity instead of asserting the intent as fact, since the Judge inherits Defender answers as evidence.

4. **Read-only subagents.** roles.md says to spawn role subagents read-only where the harness supports it. I used general-purpose subagents (not read-only) and added an explicit "do not create or edit any files" line to every role prompt. No subagent edited any file.

5. **Transcription of scaffolding.** Some subagent replies wrapped their section in scaffolding ("Ready to paste under ...", a duplicate top-level heading). I transcribed the section bodies verbatim and dropped only the scaffolding lines and duplicate headings, so the transcript keeps the template's heading hierarchy. No role's argument text was altered; heading levels of the Adversary's phase-4 objections were shifted one level (## to ####) to nest under the template's section heading.

6. **Session interruption.** A session limit terminated the run after the debate finished, during output saving. On resume I verified the disk state: the transcript held all six phases with no template placeholders left, the outputs copy was byte-identical to the working copy, and final-report.md, answer.md, and user_notes.md had already been written. Only metrics.json was missing; I wrote it on resume. Counted as 1 in errors_encountered.

7. **metrics.json definitions.** "total_steps" counts assistant messages in the run, including the final reply. "output_chars" is the byte count of answer.md; "transcript_chars" is the byte count of the completed transcript.md. "files_created" lists files this run created, not the pre-existing input.
