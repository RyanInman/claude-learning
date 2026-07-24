# Conventions for Generated Scripts

Every script written into a target skill follows these rules. smoke_test.py
checks them mechanically; `skills/skill-reviewer/scripts/audit.py` is the
in-repo exemplar of the shape.

## The five hard rules

1. **argv-only, never interactive.** Agents run non-interactive shells; a
   prompt hangs forever. All input via arguments and flags. Never call
   `input()`, never read stdin unless a documented `-` argument asks for it.
2. **Meaningful exit codes.** House style: `0` success/clean, `1`
   findings/failure, `2` usage error or unreadable input. Document them in the
   docstring. Different failure kinds beyond that get distinct codes only when
   a caller needs to branch on them.
3. **JSON to stdout, diagnostics to stderr.** stdout is the data contract.
   Support `--out FILE` whenever output can exceed a screenful, and print a
   compact summary to stdout in that mode.
4. **`--help` must work.** Use argparse (it is free). The help text is how the
   next agent learns the interface; keep it short since it enters context.
5. **Self-documenting header docstring** with USAGE and EXIT CODES sections —
   copy the shape of audit.py's header.

## Also

- Python 3 stdlib only, unless the target skill already carries dependencies.
- Handle expected errors (missing file, bad JSON) with a clear stderr message
  and exit 2 — never a bare traceback for a predictable failure.
- No voodoo constants: `TIMEOUT = 30  # slowest observed fixture is 12s`, not
  a bare number.
- Destructive operations need `--force` and offer `--dry-run`; prefer
  idempotent "create if not exists" since agents retry.
- Forward slashes in every path, even on Windows.
