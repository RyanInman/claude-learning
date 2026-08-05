# Platform Variants

The workflow in `SKILL.md` assumes Claude Code (subagents, a browser, a filesystem). On Claude.ai and in Cowork some mechanics differ. Read the section for the platform you're on; the core loop (draft → test → review → improve → repeat) is unchanged.

## Claude.ai-specific instructions

Claude.ai has no subagents, so these mechanics change:

**Running test cases**: No subagents means no parallel execution. For each test case, read the skill's SKILL.md, then follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent subagents, because the author also runs the test. Treat it as a sanity check; the human review step compensates. Skip the baseline runs — just use the skill to complete the task as requested.

**Reviewing results**: If you can't open a browser (e.g., Claude.ai's VM has no display, or you're on a remote server), skip the browser reviewer entirely. Instead, present results directly in the conversation. For each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?"

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline comparisons which aren't meaningful without subagents. Focus on qualitative feedback from the user.

**The iteration loop**: Same as before — improve the skill, rerun the test cases, ask for feedback — just without the browser reviewer in the middle. You can still organize results into iteration directories on the filesystem if you have one.

**Description optimization**: This section requires the `claude` CLI tool (specifically `claude -p`), which Claude.ai does not have. Skip it on Claude.ai. (Cowork has the CLI — see below.)

**Blind comparison**: Requires subagents. Skip it.

**Packaging**: The `package_skill.py` script works anywhere with Python and a filesystem. On Claude.ai, you can run it and the user can download the resulting `.skill` file.

**Plugin references**: An uploaded copy of *this* skill lacks the plugin-level `../../references/` files (best-practices, token-economics, writing-style-guide), because packaging only includes the skill folder — and Claude.ai does not substitute `${CLAUDE_SKILL_DIR}`. When a pointer to those files fails to resolve, work from the summaries already in `SKILL.md`; when packaging this skill itself, copy the three files into `references/` first.

**Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. In this case:
- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field -- use them unchanged. E.g., if the installed skill is `research-helper`, output `research-helper.skill` (not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory -- direct writes may fail due to permissions.

---

## Cowork-Specific Instructions

In Cowork:

- Subagents work, so the main workflow (spawn test cases in parallel, run baselines, grade) is unchanged. On repeated timeouts, run the test prompts in series instead.
- You don't have a browser or display, so when generating the eval viewer, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Then proffer a link that the user can click to open the HTML in their browser.
- After running tests, generate the eval viewer with `generate_review.py` (not hand-written HTML) before evaluating the outputs yourself. The human's feedback must anchor the revision pass — self-review first biases you toward your own judgment and wastes the paired-run comparison. Cowork sessions skip this step most often, so treat it as mandatory there and get the results in front of the human as soon as the runs finish.
- Feedback works differently: since there's no running server, the viewer's "Submit All Reviews" button will download `feedback.json` as a file. You can then read it from there (you may have to request access first).
- Packaging works — `package_skill.py` just needs Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) works in Cowork because it uses `claude -p` via subprocess, not a browser. Save it for last: run it only after the user agrees the skill is in good shape.
- **Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. Follow the update guidance in the claude.ai section above.
