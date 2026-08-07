# Gate question (unattended run — default chosen)

**Question:** the request says to keep "the manifest" inside the skill, but no manifest
format or location was specified, and the skill had none before this run.

**Options considered**

1. `tests/manifest.json` + `tests/run_smoke_tests.py` — declarative check definitions
   (script, args, expected exit code, expected JSON fields, expected output text) plus a
   runner that executes them against the bundled fixtures.
2. A plain shell script of smoke commands, with no separate manifest file.
3. A prose checklist in SKILL.md describing the checks to run by hand.

**Chosen default: option 1.** The stated reason for keeping the residue is "so I can
re-run the checks myself later," which needs the expectations recorded somewhere
machine-runnable, not just the commands. Option 2 folds the expectations into control
flow and is harder to extend; option 3 is not re-runnable without a human in the loop.

**Also assumed:** "test fixtures" means the sample changelog folders under
`tests/fixtures/`. These stay in the skill permanently, as requested — they are not
scratch files and were not cleaned up. The real `changelogs/` folder was left untouched.
