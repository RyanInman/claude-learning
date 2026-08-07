# Conventions for Generated Scripts

Every script written into a target skill follows these rules. smoke_test.py
checks them mechanically. Copy the shape of this skill's own
`scripts/inventory.py`, because it ships in the same folder and stays readable.

## The five hard rules

1. **argv-only, never interactive.** Agents run non-interactive shells, so a
   prompt hangs forever. Take all input through arguments and flags. Never
   call `input()`. Never read stdin unless a documented `-` argument asks for
   it.
2. **Meaningful exit codes.** House style: `0` for success, `1` for findings
   or failure, `2` for a usage error or unreadable input. Document them in the
   docstring. Give a further failure kind its own code only when a caller
   needs to branch on it.
3. **JSON to stdout, diagnostics to stderr.** stdout is the data contract.
   Support `--out FILE` whenever output can exceed about 50 lines. Print a
   compact summary to stdout in that mode.
4. **`--help` must work.** Use argparse, because it costs nothing. The help
   text teaches Claude the interface, so keep it short. It enters context on
   every run.
5. **Self-documenting header docstring** with USAGE and EXIT CODES sections.
   Copy the shape of `scripts/inventory.py`'s header.

## Further rules

- Use the Python 3 standard library only, unless the target skill already
  carries dependencies.
- Catch expected errors such as a missing file or bad JSON. Print a clear
  stderr message. Exit 2. Never leave a bare traceback for a predictable
  failure.
- Write no magic numbers: `TIMEOUT = 30  # slowest observed fixture is 12s`,
  never a bare number.
- Guard every destructive operation behind `--force`. Offer `--dry-run`.
  Prefer idempotent "create if not exists", because agents retry.
- Use forward slashes in every path, even on Windows.
