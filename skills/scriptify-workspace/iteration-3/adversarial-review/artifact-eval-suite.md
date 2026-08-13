# Artifact: the scriptify eval suite, with iteration-3 outcomes

The suite under review is `skills/scriptify/evals/evals.json`: 10 evals, 51 pre-registered
assertions. Each eval ran once with the skill and once with no skill (baseline). Below, every
assertion carries the graded outcome for both arms and the grader's evidence.

Headline: with_skill 90% +/- 12%, baseline 76% +/- 18%, delta +0.14.
Cost: with_skill 66,868 tokens / 294.3s; baseline 41,579 tokens / 164.0s.
One run per eval per arm, so every delta is a single draw.

## eval 0 — classify-and-report

**Prompt:** Review the skill in evals/fixtures/changelog-checker/ and tell me which of its workflow steps should be delegated to scripts. Don't change anything yet.

**Expected:** Rendered classification table: steps 1/2/3/5 SCRIPT with concrete proposed interfaces, step 6 HYBRID, steps 4 and 7 CLAUDE (7 despite containing the word 'verify'). Nothing written into the fixture; flow stops at the gate or explicitly notes changes await user selection.

### A1 (structure): output contains a per-step table with SCRIPT/CLAUDE/HYBRID classes and proposed script interfaces for SCRIPT/HYBRID rows

- with_skill: **PASS** — outputs/report.md L5-13 renders a 7-row markdown table with columns '#, Step (line), Current form, Tokens, Class, Why, Proposed script interface'. Class column values are literally SCRIPT (s1,s2,s3,s5), CLAUDE (s4), HYBRID (s6,s7). Every SCRIPT/HYBRID row carries a filled interface cell (`python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json` or `python3 scripts/render_summary.py .changelog-scan.json`) with exit codes; the CLAUDE row s4 has '-'. Checked with `grep -c '| s' outputs/report.md` -> 7, exit 0.
- baseline:   **FAIL** — outputs/report.md L17-25 is a 7-row table with columns '#, Step, Verdict, Why'. It has no proposed-script-interface column at all: the single proposed script (scripts/check_changelogs.py) is described in a later prose section (L27-47), not per row, and no row states an invocation. The class labels are also different vocabulary: **Script** / **Keep in the skill** / **Split** rather than SCRIPT/CLAUDE/HYBRID. Fails on the interface half regardless of labels. `grep -niE 'exit|argv|python3' without_skill/outputs/report.md` returned only the table separator line, exit 0.

### A2 (structure): no new files or directories are created inside evals/fixtures/changelog-checker/

- with_skill: **PASS** — `diff -ru /Users/admin/claude-learning/skills/scriptify/evals/fixtures/changelog-checker with_skill/workspace/changelog-checker` -> no output, exit 0. `find with_skill/workspace -mindepth 1` lists exactly the 4 pristine paths (SKILL.md + 3 changelogs). facts.json target_tree_diff added/removed/modified are all empty and new_script_count is 0. The run kept its scratch under with_skill/scratch/.delegation-review/, outside the target. Also confirmed the shared pristine fixture at skills/scriptify/evals/fixtures/changelog-checker/ still holds only its 4 original files. NON-DISCRIMINATING: the without_skill arm also wrote nothing into the target.
- baseline:   **PASS** — `diff -ru /Users/admin/claude-learning/skills/scriptify/evals/fixtures/changelog-checker without_skill/workspace/changelog-checker` -> no output, exit 0. `find without_skill/workspace -mindepth 1` lists exactly the 4 pristine paths. facts.json target_tree_diff added/removed/modified all empty, new_script_count 0. Transcript-notes and gate.md both record option 4, report only. NON-DISCRIMINATING: the with_skill arm also wrote nothing into the target.

### A3 (content): step 2 (version-header check) is classified SCRIPT with a concrete argv/exit-code interface

- with_skill: **PASS** — report.md row s2 Class = SCRIPT. Interface cell gives a runnable argv line, `python3 scripts/scan_changelogs.py changelogs/ --json --out .changelog-scan.json`, plus an explicit exit contract: 'exit 0 clean / 1 findings / 2 usage'. The row also grounds the check in the target's own data (v1.2.0.md opens with `### Added`, so it fails the `## vX.Y.Z - YYYY-MM-DD` heading).
- baseline:   **FAIL** — Half credit is not available. The verdict for step 2 is **Script** (report.md L20), which matches the SCRIPT class in substance. But no concrete argv/exit-code interface exists anywhere in the output: the script section (L29-43) says only 'One file, scripts/check_changelogs.py ... It takes the changelogs directory and prints JSON' followed by a sample JSON payload. `grep -niE 'exit|argv|python3|--' without_skill/outputs/report.md` matched only the markdown table separator, exit 0 -> zero exit-code statements and zero invocation lines. Fails the 'concrete argv/exit-code interface' clause.

### A4 (content): step 6 (category tags + Misc re-homing) is classified HYBRID

- with_skill: **PASS** — report.md row s6 Class = HYBRID verbatim, with the split stated: the allowed-tag set check goes to scan_changelogs.py, and judging that v1.1.0.md's Misc entry 'Corrected typo in settings page label' belongs under Fixed stays with Claude. Confirmed by `grep -n '| s6' outputs/report.md`, exit 0.
- baseline:   **PASS** — report.md L24 gives step 6 the verdict **Split** and states both halves explicitly: 'Membership in {Added, Fixed, Changed, Removed, Misc} is a set lookup -> script. Deciding that "Corrected typo in settings page label" is really a Fixed is judgment -> skill. The script should emit the list of Misc entries for the model to rule on.' That is the HYBRID classification under a different label; the assertion is about which class the step lands in, and the split-mechanical-plus-judgment call matches. Label divergence noted: the baseline never uses the token HYBRID, which is scriptify's vocabulary.

### A5 (content): step 7 (verify entries clearly written) is classified CLAUDE despite the 'verify' verb

- with_skill: **FAIL** — report.md row s7 Class = HYBRID, not CLAUDE. `grep -o 'HYBRID' <<< row s7` confirms; the row reads 'HYBRID | judging that an entry reads confusingly ... stays Claude's, but enumerating every entry with its file, category, and text is mechanical'. The run assigned s7 a proposed script interface (`python3 scripts/scan_changelogs.py ...`), which is exactly what a CLAUDE classification excludes. Graded as written: the assertion names CLAUDE, the arm produced HYBRID -> fail.
- baseline:   **PASS** — report.md L25 gives step 7 the verdict **Keep in the skill** with the reason 'Clarity has no mechanical definition. A script could only proxy it with length or word lists, which would flag the wrong lines.' The step is assigned wholly to model judgment with no script component, which is the CLAUDE class, and the run did not let the word 'verify' pull it toward a script. Label divergence noted: the baseline writes 'Keep in the skill' rather than scriptify's token CLAUDE. This is the assertion where the arms differ - with_skill classified step 7 HYBRID.

### A6 (content): step 4 (release narrative) is classified CLAUDE

- with_skill: **PASS** — report.md row s4 Class = CLAUDE, interface cell '-', reason 'the whole output is a narrative the user reads, pitched at a non-technical reader; reasonable runs should word it differently.' It is the only CLAUDE row in the table. Confirmed by `grep -n 'CLAUDE' outputs/report.md`, exit 0, single row hit.
- baseline:   **PASS** — report.md L22 gives step 4 the verdict **Keep in the skill**: 'Requires reading intent across releases and choosing a register. No fixed rule produces this.' Assigned wholly to model judgment with no proposed script, i.e. the CLAUDE class. L13 restates it: 'Steps 4 and 7 are judgment.' Label divergence noted as above.


## eval 1 — apply-and-smoke-test

**Prompt:** Review the skill in evals/fixtures/changelog-checker/ for steps to delegate to scripts, apply all the delegations you find, and verify the generated scripts work.

**Expected:** Scripts written into changelog-checker/scripts/ for steps 1/2/3/5 (and the mechanical half of 6), each with --help support. Manifest includes bad_data_invocations; the header-check script flags v1.2.0.md. SKILL.md rewritten only after smoke test passes; steps 4 and 7 stay prose; step 6 keeps its judgment sentence.

### A1 (structure): changelog-checker/scripts/ contains at least 3 Python scripts and each supports --help

- with_skill: **FAIL** — FAIL on count. `ls with_skill/workspace/changelog-checker/scripts/` shows 2 .py files (scan_changelogs.py, render_summary.py); facts.json new_script_count=2. Both do support --help: `python3 scripts/scan_changelogs.py --help` exit 0 and `python3 scripts/render_summary.py --help` exit 0. 2 < 3, so the assertion as written fails. NON-DISCRIMINATING: the without_skill arm shipped 1 script and also fails.
- baseline:   **FAIL** — FAIL on count. `ls without_skill/workspace/changelog-checker/scripts/` shows 1 .py file (scan_changelogs.py); facts.json new_script_count=1. It does support --help: `python3 scripts/scan_changelogs.py --help` exit 0. 1 < 3. The run chose one script deliberately (report: 'One script, not five'), but the assertion as written fails. NON-DISCRIMINATING: with_skill shipped 2 and also fails.

### A2 (structure): the rewritten SKILL.md invokes each generated script by exact command line

- with_skill: **PASS** — PASS. SKILL.md step 1 gives `python3 scripts/scan_changelogs.py changelogs/ --out .changelog-scan.json` and step 3 gives `python3 scripts/render_summary.py .changelog-scan.json`; a Scripts table repeats both. Ran both verbatim from with_skill/workspace/changelog-checker/: scan exit 1 (findings, its documented code), render exit 0 with the descending table. Every generated script (2 of 2) is invoked by an exact, working command line. NON-DISCRIMINATING: without_skill also passes.
- baseline:   **PASS** — PASS. Only one script was generated. SKILL.md step 1 gives `python3 scripts/scan_changelogs.py changelogs` and step 2 gives `python3 scripts/scan_changelogs.py changelogs --format table`. Ran both verbatim from without_skill/workspace/changelog-checker/: exit 0 (JSON) and exit 0 (markdown table). NON-DISCRIMINATING: with_skill also passes.

### A3 (structure): a smoke-test PASS result is reported before the SKILL.md rewrite is shown

- with_skill: **PASS** — PASS. outputs/transcript-notes.md item 24 records `python3 SKILL/scripts/smoke_test.py .delegation-review/manifest.json` exit 0, 13/13 checks passed, at Step 7; the SKILL.md rewrite is item 27 at Step 8. outputs/report.md carries the full 13/13 PASS block. Graded on the eval's own expected_output framing (`SKILL.md rewritten only after smoke test passes`) rather than section order inside report.md, where the diff block happens to precede the PASS block. NON-DISCRIMINATING: without_skill verified before rewriting too.
- baseline:   **PASS** — PASS. outputs/transcript-notes.md items 9-11 run the script on the real changelogs plus three edge cases (exit 0, 0, 0, 2-as-designed) before item 12 rewrites SKILL.md; outputs/report.md carries a Verification table with all five checks and their results. Graded on the eval's expected_output framing (rewrite only after the smoke test passes). NON-DISCRIMINATING: with_skill also verified before rewriting.

### A4 (content): the header-check script, run against changelogs/, flags v1.2.0.md and exits nonzero

- with_skill: **PASS** — PASS. Ran `python3 scripts/scan_changelogs.py changelogs/ --out <tmp>.json` from with_skill/workspace/changelog-checker/: stdout `header_not_first v1.2.0.md: first non-empty line is "### Added", not a "## v" heading`, exit=1. Flagged and nonzero. DISCRIMINATING: without_skill flags v1.2.0.md in `bad_headings` but exits 0.
- baseline:   **FAIL** — FAIL on the exit code. Ran `python3 scripts/scan_changelogs.py changelogs` from without_skill/workspace/changelog-checker/: JSON contains `"bad_headings": ["v1.2.0.md"]` and `heading_ok: false`, so the file is flagged, but exit=0. `--format table` also exits 0. The script reserves nonzero only for a bad path (exit 2). Flagged, not nonzero. DISCRIMINATING: with_skill exits 1 on findings.

### A5 (content): step 4 (release narrative) remains a prose instruction with no script

- with_skill: **PASS** — PASS. In the rewritten SKILL.md the narrative is step 2: `Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader. Source it from .changelog-scan.json.` No command, no script. classification.json and report.md both class s4 CLAUDE. `grep -c narrative` over scripts/ finds no generator. NON-DISCRIMINATING: without_skill keeps it as prose step 3.
- baseline:   **PASS** — PASS. Rewritten SKILL.md step 3: `Write a one-paragraph release narrative for a non-technical reader, using the entry text from the JSON.` No command. The report's classification table marks step 4 'Keep - audience judgment, no correct output to compute'. NON-DISCRIMINATING: with_skill keeps it as prose step 2.

### A6 (content): step 6's judgment about re-homing Misc entries remains prose

- with_skill: **PASS** — PASS. Rewritten SKILL.md step 4: `For each entry under misc_entries in .changelog-scan.json, judge whether it actually fits Added, Fixed, Changed, or Removed, and suggest the move.` The script only collects Misc entries (report and SKILL.md both state a Misc entry is not a finding, because re-filing is a judgment call); confirmed by the live run, which listed `misc v1.1.0.md: Corrected typo in settings page label` without deciding it. NON-DISCRIMINATING: without_skill keeps it as prose step 4.
- baseline:   **PASS** — PASS. Rewritten SKILL.md step 4: `For each item in misc_entries, judge whether it belongs under Added, Fixed, Changed, or Removed, and recommend the move with a one-line reason.` The live run confirms the script only extracts the text (`misc_entries: [{file: v1.1.0.md, entry: 'Corrected typo in settings page label'}]`) without deciding. NON-DISCRIMINATING: with_skill keeps it as prose step 4.


## eval 2 — nothing-to-delegate

**Prompt:** Which parts of the skill in evals/fixtures/well-delegated/ should be scripts?

**Expected:** Report acknowledging scripts/check.py as already delegated (mentioned in body, argparse, working --help), classifying the remaining judgment steps CLAUDE, and recommending no new scripts.

### A1 (structure): no new files are written into evals/fixtures/well-delegated/

- with_skill: **PASS** — Ran `diff -r /Users/admin/claude-learning/skills/scriptify/evals/fixtures/well-delegated with_skill/workspace/well-delegated` -> exit 0, no output. facts.json target_tree_diff is empty (added/removed/modified all []), new_script_count 0, skill_md_changed false. Run's own scratch went to with_skill/scratch/.delegation-review/, outside the fixture. NON-DISCRIMINATING: the without_skill arm also left the fixture byte-identical.
- baseline:   **PASS** — Ran `diff -r /Users/admin/claude-learning/skills/scriptify/evals/fixtures/well-delegated without_skill/workspace/well-delegated` -> exit 0, no output. facts.json target_tree_diff empty, new_script_count 0, skill_md_changed false. The run did create a probe fixture, but at without_skill/scratch/notes-bad/bad.md, outside the target and outside evals/fixtures/. NON-DISCRIMINATING: the with_skill arm also left the fixture byte-identical.

### A2 (content): scripts/check.py is acknowledged as already delegated

- with_skill: **PASS** — report.md classifies step s1 (`python3 scripts/check.py notes/ --json`) as ALREADY_DELEGATED with the interface audit spelled out: 'mentioned in body, argparse present, --help works, exit codes 0/1/2 documented'. I reproduced the audit: `python3 scripts/check.py --help` -> exit 0, usage block printed; `python3 scripts/check.py notes/ --json` -> `[]`, exit 0. facts.json records scripts[0] preexisting true, help exit 0, ok true. NON-DISCRIMINATING: the without_skill arm also acknowledged it (as 'SCRIPT - already done').
- baseline:   **PASS** — report.md verdict names check.py as the delegated deterministic step, classifies workflow step 1 'SCRIPT - already done', and adds a section 'Why scripts/check.py counts as properly delegated' covering exact invocation in the body, argparse/--help, exit codes 0/1/2, and the --json handoff into step 2. I reproduced `python3 scripts/check.py --help` -> exit 0 and `python3 scripts/check.py notes/ --json` -> `[]`, exit 0, matching facts.json (preexisting true, help ok). NON-DISCRIMINATING: the with_skill arm also acknowledged it (as ALREADY_DELEGATED).

### A3 (content): the judgment steps (audience-fit decision, explanations) are classified CLAUDE, not forced into scripts

- with_skill: **PASS** — report.md classifies s2 (which flagged items matter for this release's audience) CLAUDE -- 'reasonable runs should differ' -- and s3 (plain-worded explanation in the project's voice) CLAUDE -- a script 'would only re-gather the findings JSON Claude already holds'. Zero SCRIPT and zero HYBRID rows; the 'Why nothing else converts' section argues against encoding the audience call as policy. gate.md is `none` and no script was produced (new_script_count 0). NON-DISCRIMINATING: the without_skill arm classified both steps CLAUDE too.
- baseline:   **PASS** — report.md classifies step 2 (audience-fit) CLAUDE -- 'A script has no way to know an internal note may skip its heading' -- and step 3 (house-voice explanations) CLAUDE -- 'Prose in a house voice is generative'. A 'What I deliberately did not recommend' section rejects both scripting the audience call and templating the explanations. gate.md is `none`, changes made: none, new_script_count 0. NON-DISCRIMINATING: the with_skill arm classified both steps CLAUDE too.


## eval 3 — partial-selection

**Prompt:** Review evals/fixtures/changelog-checker/ for delegable steps, but apply only the delegations for steps 1 and 3. Leave everything else untouched.

**Expected:** Exactly two scripts generated (file listing, category counting), both smoke-tested. Step 2's prose is byte-identical to before; the SKILL.md diff touches only steps 1 and 3.

### A1 (structure): exactly two generated scripts exist in changelog-checker/scripts/

- with_skill: **FAIL** — `ls -1 with_skill/workspace/changelog-checker/scripts/*.py | wc -l` -> 1 (exit 0); only scripts/scan_changelogs.py exists. facts.json agrees: new_script_count=1, target_tree_diff.added=['scripts/scan_changelogs.py']. The run deliberately merged steps 1 and 3 into one script (report: "Rows s1 and s3 share one script"), so both selected steps are delegated, but the assertion as written asks for two scripts and one exists. FAIL.
- baseline:   **PASS** — `ls -1 without_skill/workspace/changelog-checker/scripts/*.py | wc -l` -> 2 (exit 0): count_categories.py and list_changelogs.py, one per selected step. facts.json agrees: new_script_count=2, both preexisting=false, target_tree_diff.added lists exactly those two.

### A2 (structure): the SKILL.md rewrite touches only steps 1 and 3; step 2's text is unchanged

- with_skill: **PASS** — `diff -u fixture-baseline/changelog-checker/SKILL.md with_skill/workspace/changelog-checker/SKILL.md` -> exit 1 (differences present) with only the step 1 and step 3 lines replaced; frontmatter, intro, and steps 2,4,5,6,7 appear as context lines. `grep -n '^2\.'` returns the byte-identical step 2 text in baseline and run ('Check that each file starts with a heading of the form `## vX.Y.Z - YYYY-MM-DD`. Record every file that does not.'), only its line number shifts from 13 to 14 because step 1 grew to two lines. NON-DISCRIMINATING: without_skill passes this too.
- baseline:   **PASS** — `diff -u fixture-baseline/changelog-checker/SKILL.md without_skill/workspace/changelog-checker/SKILL.md` -> exit 1 (differences present) with exactly two replaced lines, step 1 and step 3; everything else is context. `grep -n '^2\.'` shows step 2 at line 13 in both baseline and run with byte-identical text. NON-DISCRIMINATING: with_skill passes this too.

### A3 (content): both generated scripts pass the smoke test before the rewrite

- with_skill: **PASS** — Only one script was generated, and it passes every smoke check: `python3 scripts/scan_changelogs.py --help` exit 0 with non-empty usage; `python3 scripts/scan_changelogs.py changelogs/ --json` exit 0 emitting valid JSON (file_count 3, totals Added 4/Fixed 2/Changed 1/Removed 0, other_categories {"Misc":1}, total_entries 8); no-arg invocation exit 2 with argparse usage on stderr. facts.json: help exit 0, new_scripts_all_help_ok=true. Ordering: transcript-notes step 23 records `smoke_test.py manifest.json` exit 0, 6/6 PASS, before step 25's two Edits to SKILL.md, and the report reproduces the 6/6 PASS block. Graded on 'pass the smoke test before the rewrite', which every generated script did; the two-script count is graded in assertion 1 and not re-charged here.
- baseline:   **FAIL** — Neither script is agent-callable. `python3 scripts/list_changelogs.py --help` -> exit 1, empty stdout, stderr 'error: not a directory: --help'; same for count_categories.py (exit 1). facts.json records both: help exit 1, ok=false, new_scripts_all_help_ok=false. The smoke test in play (scriptify/scripts/smoke_test.py) checks 'help: `python3 <script> --help` exits 0 with non-empty usage' and 'bad-args: the bad invocation exits nonzero AND writes to stderr'; both scripts also fail bad-args, because a no-arg run silently defaults to the `changelogs` directory and exits 0 instead of erroring. The run's own check was only `python3 scripts/<name>.py changelogs` (both exit 0, output hand-verified) and it did run before the two Edits (transcript-notes step 9 precedes steps 10-11), so the ordering half holds, but the scripts do not pass the smoke test. FAIL.


## eval 4 — prose-only-headings

**Prompt:** Which parts of the skill in evals/fixtures/prose-only-reviewer/ should be scripts? Don't change anything yet.

**Expected:** Report covering all three heading-fallback anchors: link collection and target resolution SCRIPT with concrete interfaces, the fix-order decision CLAUDE. The skill does not report 'nothing to delegate' just because the target has no numbered steps.

### A1 (structure): the report contains a row for every anchor; the flow does not stop at '0 steps extracted'

- with_skill: **PASS** — `grep -c '^| s' with_skill/outputs/report.md` (exit 0) -> 4 rows: s1 'Collect the link inventory', s2 'Resolve each target', s3 'Decide what to fix now', s4 'Gotchas'. That is one row per body-bearing heading in the target SKILL.md (4 `##` sections). transcript-notes step 6 shows inventory.py reported 'steps: 4 ... no numbered steps found -- anchored on section headings instead', and the report states 'Heading-fallback is not "nothing to delegate"'. The flow continued to a full classification and gate. NON-DISCRIMINATING: the baseline arm also rows every anchor.
- baseline:   **PASS** — `grep -n` over without_skill/outputs/report.md (exit 0) -> the 'Verdict per section' table has 6 rows covering all four `##` anchors ('Collect the link inventory', 'Resolve each target', 'Decide what to fix now', 'Gotchas') plus frontmatter and the intro line. transcript-notes step 4 records 'no numbered steps, no bundled scripts' and the run classified by heading anyway; nothing stopped at 0 steps. NON-DISCRIMINATING: the with_skill arm also rows every anchor.

### A2 (structure): no new files are written into evals/fixtures/prose-only-reviewer/

- with_skill: **PASS** — `ls -laR /Users/admin/claude-learning/skills/scriptify/evals/fixtures/prose-only-reviewer/` (exit 0) -> only SKILL.md, 796 bytes. `git status --porcelain` on that path (exit 0) -> empty, no untracked or modified files. facts.json target_tree_diff is {added: [], removed: [], modified: []} and workspace_extra is []; new_script_count 0. Run kept its scratch in <RUN_DIR>/scratch/.delegation-review/. NON-DISCRIMINATING: both arms wrote nothing there.
- baseline:   **PASS** — `ls -laR /Users/admin/claude-learning/skills/scriptify/evals/fixtures/prose-only-reviewer/` (exit 0) -> only SKILL.md, 796 bytes. `git status --porcelain` on that path (exit 0) -> empty. facts.json target_tree_diff {added: [], removed: [], modified: []}, workspace_extra [], new_script_count 0; transcript-notes state the fixtures path 'was never touched'. NON-DISCRIMINATING: both arms wrote nothing there.

### A3 (content): 'Collect the link inventory' and 'Resolve each target' are classified SCRIPT with concrete argv/exit-code interfaces

- with_skill: **PASS** — report.md rows s1 and s2 are both Class=SCRIPT. s1 interface: `python3 scripts/collect_links.py docs/ --out .link-check/links.json` with 'exit 0 links found / 1 no markdown files under the root / 2 usage or unreadable root'. s2 interface: `python3 scripts/resolve_links.py .link-check/links.json --out .link-check/broken.json` with 'exit 0 all links resolve / 1 broken links found / 2 usage or unreadable input'. Both name argv and a distinct meaning per exit code.
- baseline:   **PASS** — Verdict table marks both sections '**Script**'. The interface is given under 'The one script to add': argv `python3 scripts/check_links.py <docs_root>` (default docs/), JSON on stdout with a shown schema, and an explicit exit-code contract: 'exit 0 when it ran, regardless of how many links are broken. Reserve a non-zero exit for a missing or unreadable docs_root'. The two sections are merged into one script rather than two, which the assertion does not forbid; argv and exit codes are concrete.

### A4 (content): 'Decide what to fix now' is classified CLAUDE, since the deadline trade-off varies by run

- with_skill: **PASS** — report.md row s3 'Decide what to fix now' (L20-24) has Class=CLAUDE, reason 'the release deadline arrives from the conversation, not from disk, so reasonable runs should rank the same broken links differently'. No proposed script interface (cell is '-'). The prose section 'What the two scripts buy' repeats that s3 keeps only the deadline trade-off.
- baseline:   **PASS** — Verdict table: 'Decide what to fix now' -> 'Stays prose', reason 'Weighs broken links against a release deadline. Judgment against context the script cannot see.' Section 'What I would not script' repeats it: a script 'would be wrong the first time the deadline moved. Leave it in prose.' DEFINITIONAL on the label only: 'CLAUDE' is the scriptify rubric's class name, which the baseline had no reason to use; its equivalent label 'Stays prose' carries the same classification and the same deadline reason, so the substance passes. NON-DISCRIMINATING on substance.


## eval 5 — agent-tool-steps

**Prompt:** I want my research-brief-writer skill to stop re-deriving the same busywork on every run. Which of its steps should become scripts? The skill is at evals/fixtures/research-brief-writer/. Report only for now, don't change anything.

**Expected:** Report covering all 7 steps. Steps 1, 4, 7 SCRIPT with concrete interfaces. Step 2 (WebFetch), step 3 (AskUserQuestion) and step 5 (notion MCP) are never pure SCRIPT: a script may prepare input or digest output, but the tool call itself stays in the step. Step 6 keeps its prose-writing core. Nothing written into the target.

### A1 (structure): the report contains a row for every one of the 7 workflow steps, each with a class

- with_skill: **PASS** — with_skill/outputs/report.md holds one markdown table with rows s1-s7, one per SKILL.md workflow step, and a populated Class column: s1 SCRIPT, s2 HYBRID, s3 HYBRID, s4 SCRIPT, s5 HYBRID, s6 CLAUDE, s7 SCRIPT. Checked with `grep -c '^| s' report.md` -> 7, exit 0. NON-DISCRIMINATING: without_skill also covers all 7 steps with a Verdict class.
- baseline:   **PASS** — without_skill/outputs/report.md lines 11-19 hold a table with rows 1-7, one per workflow step, each with a Verdict class: 1 Script, 2 Keep (agent), 3 Keep (agent), 4 Script, 5 Split, 6 Keep (model), 7 Script. NON-DISCRIMINATING: with_skill also covers all 7.

### A2 (structure): no new files or directories are created inside the target skill folder

- with_skill: **PASS** — `find with_skill/workspace/research-brief-writer -mindepth 1` (exit 0) returns only SKILL.md and topics.txt. facts.json target_tree_diff has empty added/removed/modified and skill_md_changed=false, new_script_count=0. The run's scratch dir holds .delegation-review/ but that lives under with_skill/scratch/, outside the target. NON-DISCRIMINATING: without_skill target is likewise untouched.
- baseline:   **PASS** — `find without_skill/workspace/research-brief-writer -mindepth 1` (exit 0) returns only SKILL.md and topics.txt. facts.json target_tree_diff has empty added/removed/modified, skill_md_changed=false, new_script_count=0. The run wrote scratch/parse_topics_demo.py, but that is in without_skill/scratch/, outside the target folder. NON-DISCRIMINATING: with_skill target is likewise untouched.

### A3 (content): step 2 (WebFetch the top source) is NOT classified pure SCRIPT, and no proposed script reimplements the fetch with curl, requests, or urllib

- with_skill: **PASS** — Row s2 is classed HYBRID; the proposed plan_fetch.py only emits the slug-to-path list of missing sources, never the fetch. `grep -niE 'curl|requests|urllib' report.md` (exit 0) returns one hit, line 64, which forbids the curl reimplementation ('A script that reimplements them with curl loses auth, the permission model, and rate limiting'). NON-DISCRIMINATING: without_skill also keeps step 2 agent-side and warns against curl.
- baseline:   **PASS** — Step 2 is classed 'Keep (agent)' - 'WebFetch is an agent tool; picking the top source is judgment'. `grep -niE 'curl|requests|urllib' report.md` (exit 0) returns one hit, line 123, which forbids it: 'Do not try to script step 2 with curl.' Neither proposed script (parse_topics.py, index_report.py) fetches. NON-DISCRIMINATING: with_skill also classes step 2 non-SCRIPT and rejects curl.

### A4 (content): step 5 (notion MCP page lookup and append) is NOT classified pure SCRIPT

- with_skill: **PASS** — Row s5 is classed HYBRID: 'the notion MCP page lookup and append carry auth and the permission model, so they stay agent-side'; render_index.py only renders the summary block passed to the MCP append. NON-DISCRIMINATING: without_skill classes step 5 'Split' with the MCP call staying.
- baseline:   **PASS** — Step 5 is classed 'Split': 'The MCP call stays; the summary block it appends is rendered by script', and the section 'The nuance on step 5' states 'Script the payload, not the call.' NON-DISCRIMINATING: with_skill classes step 5 HYBRID.

### A5 (content): step 3 (AskUserQuestion which sources to keep) is NOT classified pure SCRIPT

- with_skill: **PASS** — Row s3 is classed HYBRID: 'AskUserQuestion cannot be reimplemented in a script'; source_stats.py only builds the option list from sources/. NON-DISCRIMINATING: without_skill classes step 3 'Keep (agent)'.
- baseline:   **PASS** — Step 3 is classed 'Keep (agent)' - 'Interactive; a script cannot ask'. Line 70 keeps the AskUserQuestion call in the step and only sources its options from step 1's JSON. NON-DISCRIMINATING: with_skill classes step 3 HYBRID.

### A6 (content): steps 1 (dedupe and slugify topics), 4 (word counts and thin-source flags) and 7 (render sorted index table) are classified SCRIPT with concrete argv/exit-code interfaces

- with_skill: **PASS** — s1, s4, s7 are all classed SCRIPT. Each carries an argv line and an exit-code contract: s1 `python3 scripts/normalize_topics.py topics.txt --out .brief/topics.json` -> exit 0 topics kept / 1 no usable topics / 2 usage; s4 `python3 scripts/source_stats.py sources/ --thin-under 200 --out .brief/stats.json` -> exit 0 sources found / 1 sources/ missing or empty / 2 usage; s7 `python3 scripts/render_index.py .brief/stats.json --format table --sort words-desc` -> exit 0 rendered / 1 no kept sources / 2 usage. `grep -c 'exit 0' report.md` -> 6, exit 0. DISCRIMINATING: without_skill gives argv but zero exit codes.
- baseline:   **FAIL** — All three steps are classed Script, and argv is concrete: `parse_topics.py topics.txt` for step 1 and `index_report.py --sources sources/ --kept kept.json [--thin 200]` for steps 4 and 7. The exit-code half is absent. `grep -niE 'exit|status code|returns [0-9]' without_skill/outputs/report.md` exits 1 with no matches - the report never states an exit-code contract for either script, only stdout shape ('JSON array to stdout', 'JSON to stdout'). Graded as written: the assertion requires concrete argv/exit-code interfaces, so this fails. DISCRIMINATING: with_skill gives 0/1/2 exit codes on all three (`grep -c 'exit 0'` -> 6).

### A7 (content): step 6 (write the 200-word brief in the house voice) keeps its prose-writing core with Claude

- with_skill: **PASS** — Row s6 is classed CLAUDE with no proposed script ('-'), and the report repeats it under 'Two things I did not propose scripting': 's6, the briefs, stays Claude.' The only script touching s6 re-uses source_stats.py to check the 200-word bound after the fact, leaving the writing with Claude. NON-DISCRIMINATING: without_skill classes step 6 'Keep (model)' and says 'Do not script step 6.'
- baseline:   **PASS** — Step 6 is classed 'Keep (model)' - 'Prose judgment; the only step that needs a model' - the rewritten workflow marks it '(unchanged)', and line 128 says 'Do not script step 6. A 200-word brief in a house voice is the reason this skill uses a model.' NON-DISCRIMINATING: with_skill classes step 6 CLAUDE.


## eval 6 — name-collision

**Prompt:** Scriptify the docs-linter skill at evals/fixtures/docs-linter/ — find the steps worth delegating and apply all of them.

**Expected:** The natural script name for step 2 is check_headings.py, which already exists in the target and does something unrelated (image alt text). The run must surface the collision to the user or pick a different name. The existing file stays byte-identical. Steps 1, 2, 3 get scripts; step 4 (which files matter this sprint) stays prose.

### A1 (structure): the pre-existing scripts/check_headings.py is byte-identical to its baseline copy (sha256 d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54)

- with_skill: **PASS** — Ran `shasum -a 256 with_skill/workspace/docs-linter/scripts/check_headings.py` (exit 0) -> d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54, matching the baseline hash in the assertion; facts.json collision.byte_identical_to_baseline=true. NON-DISCRIMINATING: without_skill matches the same hash.
- baseline:   **PASS** — Ran `shasum -a 256 without_skill/workspace/docs-linter/scripts/check_headings.py` (exit 0) -> d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54, matching the baseline hash; facts.json collision.byte_identical_to_baseline=true. NON-DISCRIMINATING: with_skill matches the same hash.

### A2 (structure): the run either asks the user about the check_headings.py name collision or names its generated heading-check script something else; it does not silently overwrite

- with_skill: **PASS** — outputs/gate.md carries a dedicated 'Question 3 - Name collision' with three options (new name / overwrite / rename first) and recommends the new name; the generated script is scripts/lint_docs.py, and facts.json target_tree_diff lists only scripts/lint_docs.py added and SKILL.md modified, with check_headings.py unmodified. Both branches of the assertion satisfied. NON-DISCRIMINATING: without_skill also asks and renames.
- baseline:   **PASS** — outputs/gate.md presents 'The naming conflict' with options A (new file), B (fold into check_headings.py), C (rename), and recommends A; the generated script is scripts/lint_docs_structure.py. facts.json target_tree_diff shows only scripts/lint_docs_structure.py added and SKILL.md modified. SKILL.md also gained a Gotchas entry explaining why the two files coexist. NON-DISCRIMINATING: with_skill also asks and renames.

### A3 (structure): at least 2 newly generated Python scripts exist in docs-linter/scripts/ and each supports --help

- with_skill: **FAIL** — Only one new script exists. `ls with_skill/workspace/docs-linter/scripts/` -> check_headings.py (pre-existing), lint_docs.py (new); facts.json new_script_count=1. The one new script does support --help (`python3 scripts/lint_docs.py --help` exit 0, argparse usage text printed), but the count requirement of >=2 is not met. NON-DISCRIMINATING: without_skill also produced exactly 1 new script.
- baseline:   **FAIL** — Fails on both halves. Count: `ls without_skill/workspace/docs-linter/scripts/` -> check_headings.py (pre-existing), lint_docs_structure.py (new); facts.json new_script_count=1, so >=2 is not met. Help: `python3 scripts/lint_docs_structure.py --help` -> 'not a directory: --help', exit 2, and `-h` likewise exit 2 - the script hand-rolls argv parsing instead of using argparse, so it has no --help at all (facts.json new_scripts_all_help_ok=false). NON-DISCRIMINATING on the count (with_skill also produced 1), but with_skill's single new script does support --help (exit 0).

### A4 (structure): a smoke-test PASS result is reported before the SKILL.md rewrite is shown

- with_skill: **PASS** — outputs/report.md section '### Smoke test' (lines 83-100) prints 11 PASS lines and '11/11 checks passed (exit 0)', and it precedes the '### SKILL.md diff' section (lines 102-133). transcript-notes.md corroborates the ordering: Step 7 smoke_test.py exit 0 11/11, then Step 8 rewrites SKILL.md, then re-runs 11/11. DIFFERS from without_skill, which reports no PASS-labelled smoke test and shows its SKILL.md change before its verification section.
- baseline:   **FAIL** — No smoke test with a PASS result appears anywhere in outputs/report.md. The '## Verification' section pastes raw invocations (`python3 scripts/lint_docs_structure.py docs` exit 1, --json, missing-arg exit 2, plus a re-run of check_headings.py exit 1) with no pass/fail assertions and no PASS lines; no test harness, manifest, or fixtures were created (transcript-notes.md lists only the script and the outputs files). Ordering also fails: the report announces the SKILL.md rewrite in the 'What changed' table at line 11, well before the Verification section at line 62. DIFFERS from with_skill, which reports 11/11 PASS before showing its SKILL.md diff.

### A5 (content): the heading-check script, run against docs/, flags tutorial.md (prose before the H1) and reference/api.md (starts at H2)

- with_skill: **PASS** — Ran `python3 scripts/lint_docs.py docs/ --json` in with_skill/workspace/docs-linter (exit 1). findings = [{path: reference/api.md, code: no_h1}, {path: tutorial.md, code: h1_not_first}]. Both target files flagged with the correct distinct causes. NON-DISCRIMINATING: without_skill's script flags the same two files.
- baseline:   **PASS** — Ran `python3 scripts/lint_docs_structure.py docs` in without_skill/workspace/docs-linter (exit 1). Output flags reference/api.md ("first line is not a level-1 heading: '## API Reference'") and tutorial.md ("first line is not a level-1 heading: 'Some intro prose that arrives before any heading at all.'"), and the summary line reads 'flagged for heading structure: reference/api.md, tutorial.md'. NON-DISCRIMINATING: with_skill's script flags the same two files.

### A6 (content): step 4 (which flagged files matter most this sprint) remains a prose instruction with no script

- with_skill: **PASS** — Read with_skill/workspace/docs-linter/SKILL.md: the former step 4 survives verbatim as step 2 - 'Decide which of the flagged files matter most to fix this sprint, given that the tutorial pages get the most traffic.' No script invocation attached. skill_md_diff in facts.json confirms the sentence is carried over unchanged. NON-DISCRIMINATING: without_skill keeps the same sentence as prose.
- baseline:   **PASS** — Read without_skill/workspace/docs-linter/SKILL.md: the former step 4 survives verbatim as step 2 - 'Decide which of the flagged files matter most to fix this sprint, given that the tutorial pages get the most traffic.' No script invocation attached; report.md classifies it 'Kept as prose - a judgment call'. NON-DISCRIMINATING: with_skill keeps the same sentence as prose.


## eval 7 — keep-residue

**Prompt:** Review evals/fixtures/changelog-checker/ for steps to delegate to scripts and apply all of them. Keep the test fixtures and the manifest inside the skill afterward so I can re-run the checks myself later.

**Expected:** Scripts written and smoke-tested, then the fixtures and manifest moved into changelog-checker/scripts/tests/ with every absolute fixture path rewritten to the new location, then the smoke test re-run green against the moved manifest. The rewritten SKILL.md carries the smoke-test command.

### A1 (structure): changelog-checker/scripts/tests/ exists and contains manifest.json plus the fixture files

- with_skill: **PASS** — `ls with_skill/workspace/changelog-checker/scripts/tests/` (exit 0) -> fixtures/, manifest.json, smoke_test.py. facts.json target_tree_diff.added lists manifest.json plus 14 fixture files under scripts/tests/fixtures/ (check_changelogs good+bad, render_summary good+bad, scan_changelogs good+bad). residue.tests_dir_exists=true.
- baseline:   **FAIL** — `ls without_skill/workspace/changelog-checker/scripts/tests` -> 'No such file or directory' (exit 1). The run put its residue at tests/ under the skill root (tests/manifest.json, tests/run_tests.py, tests/fixtures/, tests/expected/), per facts.json target_tree_diff.added; facts.json residue.tests_dir_exists=false for the scripts/tests/ path. DEFINITIONAL: scripts/tests/ is the scriptify keep-residue path convention, which the baseline had no reason to produce - it did keep fixtures and a manifest, just at tests/.

### A2 (structure): every fixture path recorded in the moved manifest.json resolves on disk; no path still points into .delegation-review/

- with_skill: **PASS** — Walked every string in scripts/tests/manifest.json with python3 (exit 0), expanded {skill} to target_skill: all 10 fixture path tokens resolve on disk (scan_changelogs/good, scan_changelogs/bad, check_changelogs/good, check_changelogs/bad x5, render_summary/good/scan.json, render_summary/bad/scan.json). No token in the manifest contains '.delegation-review'; `grep -rn delegation-review` in the workspace hits only the smoke_test.py docstring, never the manifest. facts.json residue.unresolved_paths is an artifact of the collector not expanding {skill}; expanded, none are unresolved, and residue.stale_delegation_review_paths is empty.
- baseline:   **PASS** — Walked every string in tests/manifest.json with python3 (exit 0): tests/fixtures/clean, tests/expected/clean.json, tests/fixtures/messy, tests/expected/messy.json all resolve relative to the skill root. No '.delegation-review' string anywhere in the workspace (`grep -rn` returned no hit in this arm). The manifest was authored in place rather than moved out of .delegation-review, but the assertion's literal check passes. NON-DISCRIMINATING: both arms pass.

### A3 (content): re-running scriptify's smoke_test.py against the moved manifest exits 0

- with_skill: **PASS** — Four runs, exit code taken from the python3 process itself (echo $? immediately after, no pipeline). (A) shipped copy from its own dir: `python3 <skill>/scripts/tests/smoke_test.py <skill>/scripts/tests/manifest.json` -> EXIT 0, 21/21 checks passed. (B) canonical /Users/admin/claude-learning/skills/scriptify/scripts/smoke_test.py against the same manifest -> EXIT 0, 21/21. The shipped copy is byte-identical to the canonical one (`diff` exit 0). (C) whole target copied to a scratchpad path, relocated copy's own smoke_test.py + relocated manifest -> EXIT 0, 21/21, with stderr note 'residue manifest sits in <new path>; using that as target_skill instead of the recorded <old path> (the skill was moved).' (D) canonical smoke_test.py against the relocated manifest -> EXIT 0, 21/21, same note. Both requested checks (own directory and relocated target) exit 0.
- baseline:   **FAIL** — This arm ships no smoke_test.py (`find` over the workspace finds none; the only copies are skills/scriptify/scripts/smoke_test.py and the with_skill arm's vendored one). Ran the canonical `python3 /Users/admin/claude-learning/skills/scriptify/scripts/smoke_test.py without_skill/workspace/changelog-checker/tests/manifest.json`, exit code read from the python3 process itself -> EXIT 2, stderr 'manifest invalid: missing field: target_skill' and 'manifest invalid: missing or empty field: scripts'. The manifest is a bespoke schema (script/runner/cases), not the scriptify manifest schema. The arm's own runner does pass: `python3 tests/run_tests.py` -> exit 0, '2 case(s), 0 failure(s)'. DEFINITIONAL: the assertion names scriptify's smoke_test.py and its manifest schema.

### A4 (structure): the rewritten changelog-checker SKILL.md body contains the smoke-test command

- with_skill: **PASS** — SKILL.md lines 23-26 add a '## Verifying the scripts' section: 'Run exactly: `python3 scripts/tests/smoke_test.py scripts/tests/manifest.json`' plus the exit-code legend (0 pass, 1 check failed, 2 manifest missing/malformed). The command is in the body, not only in report.md, and it is the command that exits 0 when run.
- baseline:   **FAIL** — SKILL.md has a '## Tests' section with `python3 tests/run_tests.py`, its own bespoke runner, and no smoke_test.py invocation (`grep -n smoke` in the SKILL.md returns nothing). Read against the preceding assertion, the smoke-test command is the scriptify smoke_test.py run against the manifest, which this SKILL.md does not carry. DEFINITIONAL: the command names a scriptify artifact absent from this arm; the arm does document an equivalent re-run command of its own.

### A5 (content): steps 4 (release narrative) and 7 (entries clearly written) remain prose with no script

- with_skill: **PASS** — SKILL.md step 4 is unchanged from the baseline ('Write a one-paragraph release narrative...'), confirmed by skill_md_diff showing it as an unmodified context line. Step 7 reads 'Read `entries` in `scan.json` and flag any entry a reader would find confusing' - it consumes step 1's artifact and invokes no script; the judgment stays with the reader. `grep -niE 'narrative|confusing|clearly written|readab'` over the three new scripts returns no narrative/clarity logic (only two 'Usage error' lines matched on 'readab'-adjacent text). report.md classifies s4 CLAUDE and s7 HYBRID with only the extraction half scripted.
- baseline:   **PASS** — In the rewritten SKILL.md the narrative step survives as step 4 ('Write a one-paragraph release narrative for a non-technical reader, using `totals` and the entry text') and the original step 7 survives as step 6 ('Read the entries themselves and flag any a reader would find confusing, quoting the entry and naming what is unclear'). Both are prose and invoke no script. `grep -niE 'narrative|confusing|clearly written|readab' scripts/check_changelogs.py` returns no match, so neither judgment was encoded in the script. NON-DISCRIMINATING: both arms pass.


## eval 8 — dead-step

**Prompt:** Which steps in the api-docs-checker skill at evals/fixtures/api-docs-checker/ should be scripts? Just tell me — don't write anything yet.

**Expected:** Report covering all 5 steps. Step 4 (append to legacy/index.txt) is DEAD: the Notes section says the legacy portal was retired in v2. Step 2 is superseded by step 3. No script is proposed for a DEAD step and no step is deleted from the target.

### A1 (structure): the report contains a row for every one of the 5 workflow steps

- with_skill: **PASS** — Read with_skill/outputs/report.md. Its verdict table has one row per step: s1 (L13-14), s2 (L15-16), s3 (L17-19), s4 (L20-21), s5 (L22-24) - all 5 workflow steps of the target SKILL.md, each with a class and a rationale. Cross-checked against the target: `grep -c '^[0-9]\.' workspace/api-docs-checker/SKILL.md` -> 5, exit 0. PASS. NON-DISCRIMINATING: without_skill also tables all 5 steps.
- baseline:   **PASS** — Read without_skill/outputs/report.md. Its table rows 1-5 name each of the 5 workflow steps with a verdict (Script / Delete / Script / Delete / Keep as prose), and the prose sections cover each. Target step count verified: `grep -c '^[0-9]\.' workspace/api-docs-checker/SKILL.md` -> 5, exit 0. PASS. NON-DISCRIMINATING: with_skill also covers all 5.

### A2 (structure): no new files or directories are created inside the target skill folder

- with_skill: **PASS** — facts.json target_tree_diff is {added: [], removed: [], modified: []} and skill_md_changed is false. Reproduced with `find with_skill/workspace -type f -o -type d | sort` (exit 0): only api-docs-checker/SKILL.md and the three pristine endpoints/*.md. `find . -name '*.py'` (exit 0) returned nothing, so new_script_count 0 holds. The run's scratch/.delegation-review/ artifacts sit under RUN_DIR/scratch, outside the target folder. PASS. NON-DISCRIMINATING: without_skill also left the target untouched.
- baseline:   **PASS** — facts.json target_tree_diff is empty and skill_md_changed is false. Reproduced with `find without_skill/workspace -type f -o -type d | sort` (exit 0): only SKILL.md plus the three pristine endpoints/*.md. `find . -name '*.py'` (exit 0) returned nothing. transcript-notes.md confirms scratch/ was never used. PASS. NON-DISCRIMINATING: with_skill also left the target untouched.

### A3 (content): step 4 (append the endpoint list to legacy/index.txt) is classified DEAD, citing the retired legacy portal

- with_skill: **PASS** — with_skill report row s4 carries Class = DEAD with the reason 'writes to legacy/index.txt for a portal the target's own Notes section says was retired in v2; legacy/ does not exist in the skill folder'. The 'two DEAD steps' section repeats the citation. The target's Notes section (SKILL.md L26-28) does say the legacy portal was retired in v2, so the citation is accurate. PASS. NON-DISCRIMINATING: without_skill also classifies step 4 dead with the same citation.
- baseline:   **PASS** — without_skill report table row 4 reads 'Delete - dead step', and the prose heading is 'Step 4 is dead - do not script it', citing 'The Notes section of the skill says the legacy docs portal was retired in v2 and the legacy/ output directory went with it' plus a verified absence of legacy/. Matches target SKILL.md L26-28. The word used is 'dead' rather than the token 'DEAD', but the classification and the required citation are both present. PASS. NON-DISCRIMINATING: with_skill classifies it DEAD too.

### A4 (content): no script is proposed for the DEAD step and the step is not deleted from the target SKILL.md

- with_skill: **FAIL** — READING APPLIED: neither arm wrote to the target (facts.json skill_md_changed false, skill_md_diff empty, target_tree_diff empty), so per the grading directive the second clause is judged against what the arm's REPORT RECOMMENDS, not against the on-disk file. Clause 1 PASSES: with_skill's s4 row has '-' in the 'Proposed script interface' column, and gate.md states the DEAD rows s2/s4 are not offered as apply options. Clause 2 FAILS under the directed reading: report.md L51-54 says 'Step 4 - delete it, and delete the Notes section that explains it', and L15-17 says steps 2 and 4 'should be deleted from the skill'. Conjunction of the two clauses -> false. Under the alternative mechanical reading (was the step actually removed from the target file?) this would PASS, since `git diff`-equivalent facts show SKILL.md byte-identical to the fixture. NON-DISCRIMINATING: without_skill recommends the same deletion, so both arms land the same way under either reading.
- baseline:   **FAIL** — READING APPLIED: same as with_skill - the target was untouched (facts.json skill_md_changed false, target_tree_diff empty), so clause 2 is judged against the report's recommendation per the grading directive. Clause 1 PASSES: report.md L30 says 'Step 4 is dead - do not script it', and no script contract is proposed for it. Clause 2 FAILS under the directed reading: report.md L33-35 says 'It should be deleted, along with the Notes paragraph that explains its absence'; gate.md option 3 is 'Delete step 4 and the Notes paragraph'; report.md L58 says 'SKILL.md loses steps 2 and 4 and the Notes paragraph'. Conjunction -> false. Under the mechanical reading this would PASS, since nothing was written. NON-DISCRIMINATING: with_skill recommends the same deletion.

### A5 (content): step 2 is identified as superseded by or duplicative of step 3, rather than getting its own separate script

- with_skill: **PASS** — with_skill report row s2 is classified DEAD with 'strictly subsumed by s3, which checks summary AND description over the same files; running both rescans endpoints/ and double-reports list-widgets.md', and its proposed-script cell is '-'. The evidence section grounds it in delete-widget.md (caught only by step 3) and list-widgets.md (double-reported). No separate script proposed. PASS. NON-DISCRIMINATING: without_skill reaches the same conclusion.
- baseline:   **PASS** — without_skill report table row 2 reads 'Delete - step 3 already does this', and the prose section 'Step 2 is redundant' says 'Step 3 checks summary: and description:, so it is a strict superset of step 2 ... Fold step 2 into step 3 and drop it.' Only one script (check_frontmatter.py, for steps 1+3) is proposed anywhere. PASS. NON-DISCRIMINATING: with_skill reaches the same conclusion.

### A6 (content): step 5 (does the description read clearly for an external developer) keeps its judgment core with Claude

- with_skill: **PASS** — with_skill report row s5 is HYBRID: 'clarity for an unfamiliar external developer is a judgment call reasonable runs disagree on, but the script already extracts every description string, so Claude judges text it no longer has to go gather'. Report L38-40 states 'No script can rule on it, which is why step 5 keeps a judgment core instead of becoming pure SCRIPT'; gate.md lists s5 as HYBRID with 'I judge clarity from its output'. Judgment stays with Claude; the script only feeds it data. PASS. NON-DISCRIMINATING: without_skill keeps it with the model too.
- baseline:   **PASS** — without_skill report table row 5 reads 'Keep as prose', and the prose section says 'Reads clearly for an external developer who has never seen this API is exactly the judgment a script cannot make. Keep it in SKILL.md and let it run on the description: values the step 1/3 script already extracted.' The run also performs the judgment itself on list-widgets.md. PASS. NON-DISCRIMINATING: with_skill keeps it with the model too.


## eval 9 — ineligible-target

**Prompt:** Scriptify the release-notes skill at <run>/workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes and apply whatever delegations you find.

**Expected:** The target sits inside a plugin cache, so it is ineligible for writes. The run produces the classification report, states why writing there is unsafe (the next plugin update clobbers it), offers to copy the skill into the project and continue on the copy, and writes nothing into the cache path.

### A1 (structure): no file anywhere under the plugins/cache/ path is created or modified; the tree is identical to its baseline

- with_skill: **PASS** — Ran `diff -r fixture-baseline/plugin-cached-release-notes with_skill/workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes` -> no output, exit 0. Confirmed byte-identity independently with sha256 over the sorted file list: SKILL.md 68c88fb7..., notes/pr-101.md d559b209..., notes/pr-104.md e59365b4..., notes/pr-109.md a58ac75c... all match the baseline. No added/removed files. facts.json target_tree_diff is empty, and the real diff agrees. NON-DISCRIMINATING: the without_skill arm's cache tree is byte-identical to the same baseline.
- baseline:   **PASS** — Ran `diff -r fixture-baseline/plugin-cached-release-notes without_skill/workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes` -> no output, exit 0. sha256 over the sorted file list matches the baseline on all four files (SKILL.md 68c88fb7..., notes/pr-101.md d559b209..., notes/pr-104.md e59365b4..., notes/pr-109.md a58ac75c...). facts.json target_tree_diff is empty and workspace_extra is empty. NON-DISCRIMINATING: with_skill's cache tree is byte-identical too.

### A2 (content): the run states the target is ineligible because it lives in a plugin cache, and gives the reason (the next plugin update overwrites anything written there)

- with_skill: **PASS** — outputs/report.md heading is 'Step 0 - eligibility: the target is INELIGIBLE' and the body says 'That path is a plugin cache. Anything I write there is silently clobbered by the next update of the `release-tools` plugin, so I did not write into it'. outputs/gate.md repeats it: 'so it is ineligible: the next plugin update silently clobbers any script written there'. Both the ineligibility claim and the plugin-update-overwrite reason are present. NON-DISCRIMINATING: without_skill states the same substance.
- baseline:   **PASS** — outputs/report.md heading 'Stopped before writing: the target is a plugin cache copy' identifies `<config>/plugins/cache/` as Claude Code's installed-plugin cache and gives the reason: 'the plugin manager replaces the directory wholesale when the plugin version changes... A script I add there disappears at the next `/plugin update` or reinstall.' outputs/gate.md repeats it. It does not use the literal word 'ineligible', but it states the target cannot be written to and gives the overwrite reason the assertion names. NON-DISCRIMINATING: with_skill states the same.

### A3 (structure): the run still produces the per-step classification report for the target

- with_skill: **PASS** — outputs/report.md 'Step 3 - report' contains a per-step table with one row per numbered step (s1-s5), each with line numbers, current form, token count, class (SCRIPT/CLAUDE), a why, and a proposed script interface, plus 'No DEAD and no ALREADY_DELEGATED steps.' Report was produced against the plugin-cache original (transcript-notes.md commands 5-8 run inventory.py/sample_target_data.py/render_report.py read-only on the target). NON-DISCRIMINATING: without_skill also produces a per-step classification table.
- baseline:   **PASS** — outputs/report.md section 'What to scriptify' contains a per-step table covering all 5 numbered steps, each with what it does and a Delegate/Keep verdict with a reason (step 4 kept as prose judgment). Produced against the cache target itself, read-only. NON-DISCRIMINATING: with_skill also produces a per-step classification table, though a richer one (tokens, class labels, proposed interfaces).

### A4 (content): the run offers to copy the skill into the project and continue from the apply stage on the copy

- with_skill: **PASS** — outputs/gate.md 'Question 1 - ineligible target: copy it?' asks 'Copy it into the project and continue from Step 4 on the copy?' with the recommended option 'Copy the skill to `workspace/.claude/skills/release-notes`, then apply the delegations to that copy. The plugin-cache original stays untouched.' Step 4 is the apply gate, so the offer resumes at the apply stage on the copy. The run then took that option (transcript-notes.md cmd 9 `cp -R <target> workspace/.claude/skills/release-notes`), and facts.json workspace_extra lists the copy plus its two generated scripts. DISCRIMINATING: without_skill offers the plugin source repo or `~/.claude-personal/skills/`, never a copy into the project.
- baseline:   **FAIL** — Checked outputs/gate.md and outputs/report.md for a copy-into-the-project offer. gate.md offers exactly three destinations: (1) 'The plugin's source repo (recommended)' - apply in the user's clone of release-tools; (2) 'A personal copy' - copy to `~/.claude-personal/skills/release-notes`, i.e. the user-level config dir, not the project; (3) 'The cache anyway' - a throwaway write that gets wiped. None of the three is a copy into the project, so the run never offers to continue the apply stage on a project copy. Option 2 is the closest, but it names the personal skills directory, and the assertion as written requires the project. DISCRIMINATING: with_skill offers `workspace/.claude/skills/release-notes` and continues from Step 4 on it.

### A5 (structure): no scripts are generated into the cache target and its SKILL.md is not rewritten

- with_skill: **PASS** — Verified directly: `find <cache target> -name '*.py'` returns nothing, and SKILL.md sha256 68c88fb728df3414ee745e7361c2902814297930fe9a15e50234e3750dc9ca04 equals the baseline's. facts.json scripts=[], new_script_count=0, skill_md_changed=false. The two generated scripts (scan_notes.py, render_notes.py) and the rewritten SKILL.md live only under workspace/.claude/skills/release-notes. NON-DISCRIMINATING: without_skill also generated nothing into the cache.
- baseline:   **PASS** — Verified directly: `find <cache target> -name '*.py'` returns nothing, and the cache SKILL.md sha256 equals the baseline's. facts.json scripts=[], new_script_count=0, skill_md_changed=false, workspace_extra=[]. The proposed collect_notes.py exists only as a code block in report.md and as scratch/collect_notes.py outside the target. NON-DISCRIMINATING: with_skill also wrote nothing into the cache.

