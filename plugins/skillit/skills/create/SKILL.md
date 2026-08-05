---
name: create
description: Create new skills, modify and improve existing skills, and measure skill performance. Use whenever the user wants to create a skill from scratch, turn a workflow into a reusable skill, edit or optimize an existing skill, run evals or benchmark a skill with variance analysis, or sharpen a skill's description for better triggering accuracy, even if they don't say the word "skill" but describe wanting Claude to do a repeatable task the same way every time. Do NOT use when the user wants Claude to perform the task itself (write code, fix a bug, draft a doc) rather than package it, or when a lighter container fits - an always-true convention belongs in CLAUDE.md, a per-path rule in .claude/rules, and a guarantee that must hold every time in a hook, not a skill. Do NOT use for a read-only audit or feedback pass on a skill with no edits requested - use skillit:review for that.
---

# Skill Creator

The core loop:

1. Decide what the skill should do and roughly how.
2. Write a draft.
3. Run claude-with-access-to-the-skill on a few realistic test prompts in the background; draft quantitative evals while they run.
4. Show the user the results with `scripts/generate_review.py` — qualitative outputs and quantitative metrics.
5. Rewrite based on their feedback and any flaws the benchmarks expose; repeat, then expand the test set and rerun at larger scale.

Find where the user is in this loop and jump in. They might say "I want to make a skill for X" (start at step 1) or arrive with a draft (skip to eval and iterate). Stay flexible: if they say "skip the evals, just vibe with me," do that. After the skill is solid, run the Description Optimization loop (below) to improve triggering.

## Communicating with the user

Users span a wide range of coding-jargon familiarity. Read context cues and calibrate:

- "evaluation" and "benchmark" are borderline but usually OK.
- For "JSON" and "expectation," wait for clear signals the user knows the terms before using them unexplained.

When in doubt, briefly define a term rather than assume.

---

## Creating a skill

### Is this a skill?

Before writing a skill, confirm a skill is the right container. A skill body loads into context every time it triggers and stays there for the session, so reach for one only when nothing lighter does the job:

- **Always-true convention** (naming, style, a one-line gotcha) → a line in `CLAUDE.md`, not a skill.
- **Rule scoped to certain paths** → a path-scoped rule (`.claude/rules/*.md` with a `paths:` glob), so it loads only when Claude touches a matching file.
- **Guarantee that must hold every time** → a hook. Prose is a polite request re-issued every turn; a hook is enforced once and free forever, so it's the right tool for "never push to main"-style invariants.
- **Multi-step procedure, needs scripts, or only matters in one corner of the work** → a skill. That's the case the rest of this section covers.

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. Ask the user to fill the gaps and confirm before you proceed.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest a default based on the skill type, but let the user decide.

A verbatim capture, request → intent:

> User: "make a skill that turns my messy release notes into a changelog"
>
> Captured intent: enable = transform raw notes into a CHANGELOG.md section; triggers = "changelog", "release notes", "version notes"; output = keep-a-changelog format; test cases = yes (verifiable transform).

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until these answers are settled.

Check available MCPs. If they help research (searching docs, finding similar skills, looking up best practices), run the research through parallel subagents when available, otherwise inline. Come prepared with context to reduce burden on the user.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Claude tends to "undertrigger" skills, so make the description a little bit "pushy": instead of "How to build a simple fast dashboard to display internal Anthropic data.", write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'" The full description criteria (negative triggers, weak-opening test, length limits) are canon in `${CLAUDE_SKILL_DIR}/../../references/best-practices.md` §1 — read it when you finalize the description.
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill** — the sections below cover how to write it

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context on demand
    └── assets/     - Files used in output (templates, icons, fonts)
```

Name skills in gerund form (`processing-pdfs`, `writing-documentation`); avoid vague names like `helper` or `utils`. For the full folder layout and the complete frontmatter field reference (including Claude Code's invocation-control fields), read `references/skill-anatomy.md`. The full naming rules live in `${CLAUDE_SKILL_DIR}/../../references/best-practices.md` §3.

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - On demand (unlimited, scripts can execute without loading)

These limits are approximate; exceed them when the content earns the space.

The economics: push anything not needed on every run *down* a tier. When you weigh what stays in the body, read `${CLAUDE_SKILL_DIR}/../../references/token-economics.md` §1–2 — the canonical statement of recurring vs one-time cost; §8–9 there cover the Claude Code listing budget and compaction behavior.

**Key patterns:**
- Keep SKILL.md under 500 lines. Near the limit, move detail into references and leave clear pointers that say when to read each one.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: when a skill spans multiple domains/frameworks, split references by variant (e.g., `references/aws.md`, `references/gcp.md`) so Claude reads only the relevant one. `references/skill-anatomy.md` covers the folder scaffolding, frontmatter fields, and the split procedure.

#### Principle of Lack of Surprise

Skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though. Treat installed skills as a security surface too. Install only from trusted sources. Audit bundled scripts and references for unexpected network calls. The harness injects frontmatter into the system prompt, so frontmatter is itself an injection vector.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Step 0 intake gate** - Open every produced skill's workflow with a "Step 0: Before starting" section: the concrete facts the skill needs before acting, an instruction to mine the conversation for answers before asking the user, and a silent pass when everything is known. Clarifying questions only help before work starts; `references/writing-instructions.md` §Step 0 has the pattern and an example.

**Defining output formats** - When the skill produces a recurring deliverable (a report, a message, a file set), define an exact output template with placeholder slots. A fixed template makes run 50 look like run 1 — usually why the user wanted a skill. State the template rule with its reason, not bare caps; `references/writing-instructions.md` §Templates has the worked example.

**Examples pattern** - Include at least one concrete example — one input→output pair teaches more than paragraphs of abstract rules. `references/writing-instructions.md` §Examples beat rules has the format (deviate a little if "Input"/"Output" already appear in your example text).

**Calibrate degrees of freedom**: give text-level direction when many approaches are valid (e.g., code review), and exact, unparameterized script commands when an operation is fragile and consistency matters. Favor concrete input→output examples over abstract rules, and capture real failure points in a **Gotchas** section — often the highest-signal content in a skill. See `references/writing-instructions.md` for voice, templates, and validation loops; the anti-pattern catalog is canon in `${CLAUDE_SKILL_DIR}/../../references/best-practices.md` §4–5.

### Writing Style

All prose in the skill you produce — the SKILL.md body and every reference file — follows the house style in `${CLAUDE_SKILL_DIR}/../../references/writing-style-guide.md`. Draft naturally first, then apply the guide as a dedicated editing pass using its pre-ship checklist. Writing to the rules from a blank page produces stiffer prose than editing toward them. Two zones are exempt from its sentence-level rules and the guide explains why: the frontmatter description (optimized for triggering, colloquial phrasings included) and verbatim input→output examples (never edited to conform).

Aim for **one skill, one job** — skills that straddle several purposes confuse the agent. When a mechanical step repeats across runs, bundle it as a script rather than re-describing it each time; see `references/bundling-scripts.md` for agent-friendly script interfaces and dependency management. When authoring specifically for Claude Code (invocation control, slash-command behavior, argument substitution, proven skill categories), read `references/claude-code-specifics.md`.

### Grade and Tighten

Before writing test cases, grade the draft with the **skillit:review** skill. It runs the deterministic `audit.py` (description length, body size, frontmatter, anti-pattern counts) then applies best-practice and token-economics judgment, returning a confidence-scored, high-impact-first list. Apply every high-confidence fix before moving on; don't re-derive these checks inline here.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write expectations yet — just the prompts. Draft the expectations in the next step while the runs are in progress. See `references/schemas.md` for the evals.json structure (including the `expectations` field, which you'll add later).

## Running and evaluating test cases

Read `references/running-evals.md` at this step and follow it end to end. It covers one continuous sequence: spawn paired runs in one turn, capture `total_tokens`/`duration_ms` from each task notification, grade against expectations, aggregate the benchmark, launch the viewer, read the feedback. Don't stop partway through — the sequence pairs every with-skill run against a baseline, and a partial pass loses that comparison. Don't use `/skill-test` or any other testing skill: they skip the paired baseline and the feedback viewer this loop depends on.

---

## Improving the skill

This is the heart of the loop. Once the user has reviewed the test results, improve the skill based on their feedback.

### How to think about improvements

1. **Generalize from the feedback.** The skill will serve countless future prompts; you iterate on a few examples only because they're fast to check. A skill that works only for those examples is useless. Avoid fiddly overfitted changes and constrictive MUSTs. Branch out instead — try a different metaphor or a different recommended pattern of working. A variant is cheap to test and might land on something great.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Read the transcripts, not just the final outputs — if the skill is making the model waste time on unproductive work, try cutting the parts that cause it and see what happens.

3. **Explain the why.** Attach the reason behind everything you ask the model to do, because with a good harness models go beyond rote instructions. When the user's feedback is terse or frustrated, work out what they meant and why, then transmit that understanding into the instructions. ALL-CAPS ALWAYS/NEVER and rigid structures are a yellow flag — reframe as rule plus reason so the model can generalize.

4. **Look for repeated work across test cases.** Run exactly: `python3 ${CLAUDE_SKILL_DIR}/scripts/find_repeated_work.py <workspace>/iteration-<N> --json`. Exit 1 → its JSON lists files with the same name written independently by 2+ runs; judge each repeat. If all 3 test runs each wrote a `create_docx.py` or a `build_chart.py`, that's a strong signal the skill should bundle that script. Write it once, put it in `scripts/`, and tell the skill to use it. This saves every future invocation from reinventing the wheel. Exit 0 → no repeated files, but still read the transcripts and notice if the subagents took the same multi-step approach to something — the file scan can't see approaches.

Spend the thinking time — it isn't the blocker here. Draft a revision, then reread it cold from the user's point of view before applying.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

One stopping condition worth stating plainly: run exactly `python3 ${CLAUDE_SKILL_DIR}/scripts/benchmark_trend.py <workspace> --json` — it reports the with-skill vs baseline pass-rate delta for every iteration. Exit 1 (`"tie": true`) means the latest iteration only **ties** (or loses to) the baseline; if that holds across iterations, retire the skill instead of shipping it. The model already handles the task on its own, so the skill is pure recurring token cost for no gain — a skill has to *beat* baseline to earn its place.

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

This is a self-contained late-stage procedure: generate ~20 trigger eval queries, review them with the user via an HTML template, run the automated optimization loop (`scripts.run_loop`), and apply the winning `best_description`. Read `references/description-optimization.md` and follow it end to end when you reach this step.

---

## Final review

The last step before shipping: run the **skillit:review** skill on the finished skill folder for a final pass. This is a different check from the earlier Grade and Tighten step — that one caught structural problems in a draft; this one audits the final artifact after all the iteration, description optimization, and script bundling have settled.

Apply every fix it surfaces, then run it again. Repeat until the only remaining findings are optional polish or nits (the reviewer's lower-confidence 6–7 band, or an empty verdict). High-confidence findings (8–10) always get fixed, not deferred — a known material gap in a skill that's about to be reused across many future sessions is the worst kind of debt.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
cd ${CLAUDE_SKILL_DIR} && python3 -m scripts.package_skill <path/to/skill-folder>
```

The `cd` matters — `-m` resolves the `scripts` package relative to the working directory.

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Platform variants

The workflow above assumes Claude Code. On **Claude.ai** (no subagents, often no browser) and in **Cowork** (subagents but no display), some mechanics change — running tests, reviewing results, benchmarking, and packaging. When you're on either platform, read `references/platform-variants.md` and follow the adaptations there.

