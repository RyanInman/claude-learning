# Workarounds and judgment calls worth flagging

- **Fixture layout.** `new_manifest.py` points each invocation at `<fixtures>/<stem>/good` itself,
  so the changelog `.md` files must sit directly in that folder. I first built them one level deeper
  in a `changelogs/` subfolder and had to flatten them. Nothing in the skill says which layout the
  scaffold expects; `new_manifest.py --help` says `<fixtures-root>/<script-stem>/good/` but not that
  the invocation argument is that exact path.
- **`--out` in a smoke invocation.** The scaffold copied `--out scan.json` from the proposed
  interface into the manifest argv. Left alone, every smoke run would write `scan.json` into the
  target skill folder. I dropped the flag from the manifest invocation and kept it in the SKILL.md
  step, so the smoke test exercises the stdout mode and leaves no file behind.
- **`__pycache__`.** The three consumer scripts import the shared parser from `scan_changelogs.py`,
  so running them creates `scripts/__pycache__/` inside the target. I deleted it after the final
  run. A user running the skill will regenerate it; a `.gitignore` entry in the target would be the
  durable fix, but adding one was outside what the prompt asked for.
- **One command error.** `cat -A` is a GNU flag; BSD `cat` on macOS rejects it. Re-ran with plain
  `cat`. No effect on the result.
- **Review directory placement.** The working directory sits above the target, so
  `.delegation-review/` could have gone beside it. I put it in `scratch/` instead, per the run's
  boundary rule, and passed `--review-dir scratch/.delegation-review` to `keep_residue.py`.
