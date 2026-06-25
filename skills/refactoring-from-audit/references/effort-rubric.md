# Effort rubric

`estimate_effort.py` scores each finding so the skill spends the cheapest model
that can plausibly do the job. The tiers map to models because cost scales with
capability, and most audit fixes are mechanical:

| Effort | Model | Why |
|--------|-------|-----|
| low | haiku | Local, single-spot edit with a worked fix_example. Pattern-apply, no judgment. |
| medium | sonnet | Needs to read the surrounding code and adapt the fix, but stays in one file. |
| high | opus | Touches a public surface or ripples across files — judgment + blast-radius reasoning. Opus costs more, so the skill asks the user before spending it. |

## Signals (all deterministic)

| Signal | How it's computed | Pushes effort |
|--------|-------------------|---------------|
| `has_fix_example` | finding has a `fix_example` | down |
| `snippet_lines` | non-blank lines in `code_snippet` | up when long |
| `blast_radius` | `git grep -w --count` of the touched symbol, excluding test/spec files | up when high |
| `exported` | snippet contains `export`/`public` | up |
| `cross_file` | issue/fix wording implies a shared or extracted change ("shared", "every handler", "introduce a", "extract", ...) | up, to high |
| `has_nearby_test` | a `*test*`/`*spec*` file references the target file's basename | down (safer to verify) |

## Decision

```
high   if cross_file OR blast_radius >= 10 OR (exported AND not has_fix_example)
low    if has_fix_example AND snippet_lines <= 3 AND blast_radius <= 2
       AND not cross_file AND not exported
medium otherwise
```

## Tuning

Thresholds (10 for blast radius, 3 snippet lines) are deliberate round numbers,
not tuned constants — they exist so the boundary is auditable, not magic. If a
project's findings cluster wrong (e.g. everything lands high because symbols are
short and common, inflating blast radius), adjust the constants at the top of
`estimate_effort.py` rather than overriding tiers by hand. The point is a
defensible, repeatable estimate, not a perfect one — the per-finding test gate
catches a mis-sized job regardless of which model attempted it.
