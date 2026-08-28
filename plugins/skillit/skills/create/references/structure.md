# Structure: anatomy, splitting, scripts

## Contents

- [Folder anatomy](#folder-anatomy)
- [The three-tier loading model](#the-three-tier-loading-model)
- [When to split](#when-to-split)
- [Degrees of freedom](#degrees-of-freedom)
- [Scripts](#scripts)
- [Frontmatter fields (Claude Code)](#frontmatter-fields-claude-code)

## Folder anatomy

```
my-skill/
├── SKILL.md            # Required: frontmatter + body
├── references/         # Docs Claude READS into context on demand
├── scripts/            # Code Claude RUNS; source never enters context
├── assets/             # Files used inside the OUTPUT (templates, boilerplate)
└── evals/              # Optional: only when the user asks for evals
    └── evals.json      # Eval prompts + assertions
```

Name files descriptively (`form_validation_rules.md`, not `doc2.md`) and organize references by domain, because Claude navigates the folder like a filesystem and should read only the one file the task needs.

## The three-tier loading model

1. Startup: name + description only (~100 tokens per skill).
2. On trigger: the full body loads and stays in context for the session.
3. On demand: references load when read; scripts cost only their output.

Consequence: bundled content is effectively unbounded as long as it stays addressable rather than resident. The body's job is to be a table of contents with a workflow, not an encyclopedia.

## When to split

- Keep in the body: overview, core workflow, the example, gotchas, pointers.
- Split to `references/` from ~150 body lines; treat 500 as a hard ceiling.
- Keep references one level deep - a reference must not point to another reference, because deep files get partially read and return incomplete information.
- Add a table of contents to any reference over ~100 lines, so a partial read still shows the full scope.
- Point with "Read `references/x.md` when Y" lines. Never use `@` imports: they do not work in SKILL.md, and where they do work they inline the file at full token cost.
- Use forward slashes in every path, even on Windows.

## Degrees of freedom

Match instruction specificity to task fragility:

- Many valid approaches, context-dependent → text guidance (high freedom).
- One preferred pattern → pseudocode or a parameterized script (medium).
- Fragile operation where consistency is critical → one exact command, "do not modify" (low). Example: "Run exactly `python scripts/migrate.py --verify --backup`."

If outputs vary run-to-run in testing, tighten one notch: text → template → exact script.

## Scripts

Move a step into `scripts/` when it is deterministic or when every test run rewrote the same helper, because pre-written code is faster, cheaper, and consistent where regenerated code is none of those.

Interface rules - scripts run in non-interactive agent shells:

- No interactive prompts, ever. A blocking prompt hangs the agent. Take input via flags or stdin.
- Structured output (JSON/CSV) to stdout, diagnostics to stderr, meaningful exit codes per failure type.
- Verbose, self-correcting errors: "Field 'signature_date' not found. Available fields: customer_name, order_total" lets the agent fix its own call. An opaque "Error: invalid input" wastes a turn.
- Bounded output size, because harnesses truncate long tool output. Default to a summary; offer `--verbose`.
- Safe defaults: `--dry-run` for anything destructive, idempotent behavior ("create if not exists"), `--force` to confirm.
- `--help` that documents usage in a few lines - it is how the agent learns the interface, and it enters context.
- Self-contained dependencies: stdlib only, or PEP 723 inline metadata run with `uv run`.
- State in the body whether to RUN a script ("Run `scripts/x.py` to validate") or READ it ("See `scripts/x.py` for the algorithm"). Default to run.

## Frontmatter fields (Claude Code)

Required: `name`, `description`. Useful optional fields:

- `disable-model-invocation: true` - only the user can invoke. Use for side-effecting actions (deploy, commit) Claude must not trigger on its own.
- `user-invocable: false` - only Claude can invoke; hidden from the `/` menu. Use for passive background knowledge.
- `allowed-tools` - pre-approve tools while the skill runs.
- `context: fork` - run the skill in an isolated subagent, keeping the main context clean.
