# Gate: apply stage blocked - ineligible target

Reached at the transition from classification to apply. The user request ("apply whatever delegations you find") authorizes applying, but it does **not** answer *where* to apply, and the named target cannot legally receive writes.

## Question put to the user

**The target skill lives inside a plugin cache (`.claude-personal/plugins/cache/release-tools/...`). Anything written there is destroyed by the next plugin update. How should I proceed?**

Options offered:

1. **Copy the skill into the project and apply there.** Copy `release-notes/` to a VCS-tracked project location (e.g. `.claude/skills/release-notes/`), then resume from the apply stage on the copy. The copy shadows the plugin version and survives plugin updates. Classification is already done and carries over.
2. **Send the change upstream.** Make the delegations in the `release-tools` plugin source repo and ship them as a plugin release, so every consumer of the plugin gets them. Slower, requires access to the plugin repo.
3. **Write into the cache anyway.** Rejected as unsafe. The work is silently reverted on the next plugin refresh, leaving no trace and no error, and the cache is untracked so nothing is recoverable or reviewable.
4. **Report only.** Deliver the classification and stop.

## Which option was taken

**Option 4 for this run, with Option 1 offered as the recommended next step.**

This is an unattended run - no user is available to choose - so the only defensible action was the non-destructive one. Options 1 and 2 both create files outside the named target and pick a new home for a skill on the user's behalf; that is a decision the user owns, not a detail I can infer. Option 3 is unsafe under any reading.

The user request does **not** already answer this. It names one specific path and says "apply", implicitly assuming that path is writable. It is not. The request is silent on the fallback location, so the choice genuinely requires the user.

## State on exit

- Full per-step classification delivered in `report.md`.
- Zero files created or modified under the cache path; hashes verified identical to baseline.
- Ready to resume **from the apply stage** (no re-analysis) as soon as the user names a destination - Option 1 is one `cp -R` away.
