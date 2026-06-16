---
name: pattern-extractor
description: Analyze a codebase and extract its coding patterns, architectural decisions, conventions, and practices into structured markdown files. Use this skill whenever the user wants to document how an existing codebase works, extract architecture from code, generate agent_docs, create CLAUDE.md reference files, capture team patterns, or produce markdown documentation of code conventions and design patterns. Trigger even for vague requests like "document our codebase", "capture our patterns", or "help Claude understand our architecture". Do NOT use to design a new or proposed architecture from requirements or a BRD (use create-architecture), to scaffold a single CLAUDE.md from scratch (use /init), or to find refactoring opportunities and improve a codebase (use improve-codebase-architecture); this skill documents an existing codebase as-is and proposes no changes.
---

# Extract Patterns Skill

Analyzes a codebase and produces structured markdown documentation of its patterns, conventions, and architecture, suitable for use as Claude Code reference files, onboarding docs, or `agent_docs/`.

The skill makes no assumptions about layout or stack. It discovers the repo's actual structure and ecosystem first, then scans and documents adaptively against what it found.

---

## Execution Model: keep the main context lean

The dominant cost in this skill is raw file bytes accumulating in the main context, bytes that are useless once docs are written. Structure the run to keep them out:

1. Run Discovery (Step 1) in the main context. It is one script call that returns a compact profile.
2. Apply the scope checkpoint before any deep reading.
3. Dispatch deep scan and doc drafting (Steps 2-4) to subagents: one subagent per output doc, or one per in-scope sub-project. Each subagent reads files fully in its own context and returns only the finished markdown plus a short findings struct (patterns found, ambiguities, gaps). Raw code never enters the main context, and independent subagents run in parallel for lower wall-clock time.

If subagents are unavailable in the current environment, run Steps 2-4 inline, but still obey the cost rules: grep for signal, cap full reads, never echo file bodies into the chat.

---

## Step 1: Discover

Run the bundled discovery script from the project root. It performs all mechanical discovery in one pass (directory skeleton, extension histogram, manifest and workspace detection, existing-doc headings) and prints a compact profile, so raw listings never enter context:

```bash
bash scripts/discover.sh [project-root]
```

`scripts/discover.sh` is relative to this skill's directory. Omit the argument to use the current directory; pass an absolute path when a subagent runs it.

Turn the script output into a Repo Profile, the artifact that drives every later step:

- Layout style (monolith / monorepo / flat / domain-driven / polyglot), inferred from the skeleton, sub-project manifests, and workspace markers.
- Language(s) and framework(s), from the detected ecosystems plus the dominant manifest's key dependencies. Dependencies reveal architectural choices (Prisma -> ORM, tRPC -> type-safe API, FastAPI -> async Python, Rails -> convention-over-config MVC); read the dominant manifest when that detail matters.
- Where source, tests, and config actually live, derived from the skeleton, never assumed.
- Sub-projects in scope, set after the checkpoint below.

### Scope checkpoint

If the script lists more than one sub-project manifest, present them and ask the user which one(s) to document before deep-scanning. Deep-scanning everything by default wastes tokens on code the user may not care about.

---

## Step 2: Deep Scan (profile-driven)

Derive all scan targets from the Repo Profile: no hardcoded `src/services`-style paths, no fixed language command list. Dispatch this to subagents per the execution model.

- Entry points: locate per the detected ecosystem (e.g. `main.go`, `manage.py`, `index.ts`, `Program.cs`, `application.rb`), using the real directories from the profile.
- Recurring patterns: search the detected language's structural keywords and repeated idioms (class/interface declarations, decorators/annotations, route registrations, dependency wiring). Do not assume JS/Go/Py syntax.
- Representative files: pick from each major area that actually exists in this repo's layout, not an assumed one.

### Cost rules

- Grep for signal, don't read wholesale. Extract imports, signatures, decorators, and repeated idioms via grep; that yields most of the pattern signal at a fraction of the cost of full reads.
- Cap full reads. Read 1-2 genuinely representative files per area fully, inside the subagent. Do not full-read every layer.

Each subagent returns only distilled findings plus its drafted doc, never raw file bodies.

---

## Step 3: Extract and Analyze

Synthesize the deep-scan findings into the categories listed in `references/extraction-guide.md`. Read that file when you reach this step rather than carrying it through discovery. Filter to what the profile actually has and skip any category that is absent (no API layer means no API section).

---

## Step 4: Write Output Files

Create an `agent_docs/` directory at the project root, or wherever the user specifies. The exact file templates live in `references/output-templates.md`; the drafting subagent reads that file and fills each template against the detected stack, using the repo's real directory names rather than placeholder layouts. Omit any file that has no content. For multi-project scopes, carry per-project sections inside each doc.

---

## Step 5: Generate CLAUDE.md Pointer Block

Append (or create) the Reference Docs pointer block to `CLAUDE.md` so Claude Code auto-loads these docs. The block template is in `references/output-templates.md`. List only the files you actually created.

---

## Output Quality Rules

- Use the repo's real paths and stack terms, never placeholder or assumed layouts.
- Write docs straight to disk; never echo file bodies into the chat. The completion report references paths, lists ambiguities, and notes gaps only.
- Use file:line references instead of copying code snippets. Snippets go stale; references don't.
- Be specific. "Uses Repository pattern" is weak. "All DB access goes through classes in `src/repositories/` that extend `BaseRepository<T>`, see `UserRepository.ts:12`" is useful.
- Note the WHY when you can infer it. If the codebase uses parameterized queries everywhere and never string-interpolates SQL, say so; it's a security convention worth preserving.
- Flag anti-patterns you observe. If some files use globals and others use DI, note the inconsistency so contributors know what to follow.
- Keep each output file under ~150 lines. Dense reference files lose attention. Split if needed.

---

## Completion

When done, tell the user:
1. The detected Repo Profile and which scope was documented
2. What files were created
3. Any patterns that were ambiguous or inconsistent (worth discussing with the team)
4. What's NOT covered (e.g. "no test files found, testing conventions not documented")

Optionally suggest: "You may want to add this to your PR checklist: update `agent_docs/` when architectural decisions change."
