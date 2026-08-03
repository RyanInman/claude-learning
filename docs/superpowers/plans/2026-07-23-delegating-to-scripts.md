# delegating-to-scripts Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `delegating-to-scripts` skill: reviews a target skill folder, classifies each workflow step SCRIPT/CLAUDE/HYBRID/DEAD, reports, gates on user selection, then writes scripts into the target and rewrites its SKILL.md — contract-first, smoke-tested.

**Architecture:** Three bundled Python scripts do the deterministic work (inventory.py = anchors + cost profile + existing-script audit; render_report.py = report renderer + classification validator; smoke_test.py = manifest-driven verification of generated scripts). Claude does only judgment: classification, script authoring, prose rewriting. Spec: `docs/superpowers/specs/2026-07-23-delegating-to-scripts-design.md`.

**Tech Stack:** Python 3 stdlib (argparse, re, json, subprocess, pathlib) + optional PyYAML. pytest for tests. Markdown for SKILL.md/references/fixtures.

## Global Constraints

- All scripts: stdlib-only plus optional PyYAML fallback (`_naive_yaml`), never a hard PyYAML dependency.
- Exit-code house style (from `skills/skill-reviewer/scripts/audit.py`): `0` success/clean, `1` findings/failures, `2` usage error/unreadable input. Exception: inventory.py has no exit 1 (no findings layer).
- All scripts: argv-only, never interactive, `stdin` never read; `--help` via argparse; JSON to stdout, diagnostics to stderr.
- Forward slashes in all paths. Skill folder: `skills/delegating-to-scripts/`.
- Frontmatter description: third person, under 1024 chars, no angle brackets, contains "use whenever" trigger clause and "Do NOT use" negative triggers.
- Test command everywhere: `python3 -m pytest skills/delegating-to-scripts/tests/ -v` (run from repo root `/Users/admin/claude-learning`).
- Commit after every task. Branch: current (`feature/mining-architecture-patterns`).

---

### Task 1: Fixture A — `changelog-checker` planted skill

**Files:**
- Create: `skills/delegating-to-scripts/evals/fixtures/changelog-checker/SKILL.md`
- Create: `skills/delegating-to-scripts/evals/fixtures/changelog-checker/changelogs/v1.0.0.md`
- Create: `skills/delegating-to-scripts/evals/fixtures/changelog-checker/changelogs/v1.1.0.md`
- Create: `skills/delegating-to-scripts/evals/fixtures/changelog-checker/changelogs/v1.2.0.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the dev test bed every later task runs against. Step semantics: steps 1/2/3/5 SCRIPT, step 6 HYBRID, steps 4/7 CLAUDE (7 is the trap: contains the word "Verify" but is judgment). v1.2.0.md is the planted defect (missing `## vX.Y.Z — date` header) used as bad-data fixture.

- [ ] **Step 1: Write the fixture SKILL.md**

```markdown
---
name: changelog-checker
description: Checks a project's changelogs folder for structural problems and writes a release summary. Use when the user asks to check, validate, or summarize changelog files.
---

# Changelog Checker

Review the changelog files in `changelogs/` and produce a release summary.

## Workflow

1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
7. Verify the entries are clearly written and flag any that a reader would find confusing.
```

- [ ] **Step 2: Write the three changelog files**

`changelogs/v1.0.0.md`:

```markdown
## v1.0.0 — 2026-01-15

### Added
- Initial release
- User accounts

### Fixed
- Login redirect loop
```

`changelogs/v1.1.0.md`:

```markdown
## v1.1.0 — 2026-03-02

### Added
- CSV export

### Changed
- Faster search indexing

### Misc
- Corrected typo in settings page label
```

`changelogs/v1.2.0.md` (planted defect: no version header line):

```markdown
### Added
- Dark mode

### Fixed
- Crash on empty profile
```

- [ ] **Step 3: Verify the fixture parses as a skill**

Run: `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts/evals/fixtures/changelog-checker --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['name'])"`
Expected: prints `changelog-checker` (findings about short description are fine; frontmatter must parse).

- [ ] **Step 4: Commit**

```bash
git add skills/delegating-to-scripts/evals/fixtures/changelog-checker
git commit -m "feat(delegating-to-scripts): add changelog-checker eval fixture"
```

---

### Task 2: `scripts/inventory.py`

**Files:**
- Create: `skills/delegating-to-scripts/scripts/inventory.py`
- Test: `skills/delegating-to-scripts/tests/test_inventory.py`

**Interfaces:**
- Consumes: fixture A from Task 1; `_split_frontmatter`/`_naive_yaml` pattern copied from `skills/skill-reviewer/scripts/audit.py`.
- Produces: CLI `python3 scripts/inventory.py <target-skill-dir> [--out FILE] [--no-probe]`, exit 0/2. Output JSON keys used by Task 3: `target`, `frontmatter{name, description_chars, unexpected_keys}`, `body{lines, approx_tokens}`, `steps[{id, origin, heading_path, line_start, line_end, approx_tokens, snippet, code_blocks[{lang, looks_like_command}], mechanical_verb_hints, agent_tool_mentions, mentions_existing_script}]`, `orphan_code_blocks`, `scripts[{path, lines, mentioned_in_body, has_argparse, has_docstring, help_ok}]`, `references`, `assets`, `stats{n_steps, n_steps_with_hints, n_existing_scripts}`. Step ids are `s1..sN` in document order; line numbers are 1-based positions in the SKILL.md file (frontmatter included in the count).

- [ ] **Step 1: Write the failing test**

`skills/delegating-to-scripts/tests/test_inventory.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "inventory.py"
FIXTURE_A = SKILL_DIR / "evals" / "fixtures" / "changelog-checker"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=60)


def test_fixture_a_step_anchors():
    r = run(str(FIXTURE_A))
    assert r.returncode == 0, r.stderr
    inv = json.loads(r.stdout)
    assert inv["frontmatter"]["name"] == "changelog-checker"
    assert inv["stats"]["n_steps"] == 7
    ids = [s["id"] for s in inv["steps"]]
    assert ids == [f"s{i}" for i in range(1, 8)]
    assert all(s["origin"] == "numbered-list" for s in inv["steps"])
    assert all(s["approx_tokens"] >= 1 for s in inv["steps"])
    assert all(s["line_start"] >= 1 for s in inv["steps"])


def test_fixture_a_hints():
    inv = json.loads(run(str(FIXTURE_A)).stdout)
    steps = {s["id"]: s for s in inv["steps"]}
    assert "list" in steps["s1"]["mechanical_verb_hints"]
    assert "check" in steps["s2"]["mechanical_verb_hints"]
    assert "count" in steps["s3"]["mechanical_verb_hints"]
    assert "render" in steps["s5"]["mechanical_verb_hints"]
    # trap step: 'verify' hint present even though the step is CLAUDE work
    assert "verify" in steps["s7"]["mechanical_verb_hints"]
    assert steps["s4"]["agent_tool_mentions"] == []
    assert inv["stats"]["n_existing_scripts"] == 0


def test_accepts_skill_md_path():
    r = run(str(FIXTURE_A / "SKILL.md"))
    assert r.returncode == 0
    assert json.loads(r.stdout)["stats"]["n_steps"] == 7


def test_non_skill_dir_exits_2(tmp_path):
    r = run(str(tmp_path))
    assert r.returncode == 2
    assert "SKILL.md" in r.stderr


def test_out_flag_summary_has_no_step_text(tmp_path):
    out = tmp_path / "inv.json"
    r = run(str(FIXTURE_A), "--out", str(out))
    assert r.returncode == 0
    inv = json.loads(out.read_text())
    assert inv["stats"]["n_steps"] == 7
    # stdout is counts + hints only, never step text
    assert "release narrative" not in r.stdout
    assert "verbs=" in r.stdout


def test_help():
    r = run("--help")
    assert r.returncode == 0
    assert "target-skill-dir" in r.stdout or "target_skill_dir" in r.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_inventory.py -v`
Expected: FAIL/ERROR — `inventory.py` does not exist (subprocess exits 2 with python "No such file" error).

- [ ] **Step 3: Write inventory.py**

`skills/delegating-to-scripts/scripts/inventory.py`:

```python
#!/usr/bin/env python3
"""
inventory.py - Anchor generator + cost profiler for a skill under delegation review.

Emits the deterministic facts the classifying agent needs: step anchors
(id, origin, heading path, line range, token estimate), per-step hints
(mechanical verbs, agent-tool mentions, attached code blocks, existing-script
mentions), an interface audit of the target's existing scripts/ (argparse,
docstring, live --help probe), and references/assets inventories.

It does NOT classify and does NOT extract full step text: the agent reads the
target SKILL.md itself. This inventory is the map, not the territory. The
verb/tool hints are hints for the classifying agent, not verdicts.

USAGE
    python3 scripts/inventory.py <target-skill-dir> [--out FILE] [--no-probe]

    <target-skill-dir>  Folder containing SKILL.md. Passing the SKILL.md file
                        itself also works (its parent is used).
    --out FILE          Write full JSON to FILE and print a compact summary
                        (counts and hints only, no step text) to stdout.
                        Without --out, full JSON goes to stdout.
    --no-probe          Skip the live `--help` probe of existing .py scripts
                        (the probe runs each with a 10s timeout, stdin closed).

EXIT CODES
    0  Inventory produced (even with zero steps; the summary says so).
    2  Usage error / no SKILL.md / unreadable file.

There is no exit 1: extraction has no findings layer -- deciding what matters
is the agent's job. All input from argv; the script never prompts.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
STEP_HEADING_RE = re.compile(r"\b(step|phase)\s*\d+", re.IGNORECASE)
NUM_ITEM_RE = re.compile(r"^\s{0,3}\d{1,3}[.)]\s+(.*)$")
CHECKLIST_RE = re.compile(r"^\s*-\s\[[ xX]\]\s+(.*)$")
FENCE_RE = re.compile(r"^(```+|~~~+)\s*(\S*)\s*$")
CMD_RE = re.compile(r"^(python3?|bash|sh|node|npx|uvx?|git|grep|find|mkdir|rm|jq|sed|awk)\b")

MECH_VERBS = ("parse", "validate", "count", "check", "extract", "sort", "format",
              "render", "diff", "aggregate", "collect", "list", "scan", "verify",
              "lint", "convert")
AGENT_TOOL_RE = re.compile(
    r"mcp__[\w-]+|\bWebFetch\b|\bWebSearch\b|\bAskUserQuestion\b|"
    r"\bsubagents?\b|\bAgent tool\b|\bTask tool\b", re.IGNORECASE)


def _split_frontmatter(text):
    """Return (frontmatter_dict_or_None, body_str, error_or_None)."""
    if not text.startswith("---"):
        return None, text, "no YAML frontmatter (file does not start with '---')"
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, text, "frontmatter present but not closed with a '---' line"
    fm_text, body = m.group(1), m.group(2)
    try:
        import yaml
        fm = yaml.safe_load(fm_text)
    except ImportError:
        fm = _naive_yaml(fm_text)
    except Exception as e:  # noqa: BLE001
        return None, body, f"frontmatter is not valid YAML: {e}"
    if not isinstance(fm, dict):
        return None, body, "frontmatter is not a YAML mapping"
    return fm, body, None


def _naive_yaml(fm_text):
    """Tiny fallback parser for `key: value` frontmatter when PyYAML is absent."""
    out = {}
    key = None
    for line in fm_text.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if re.fullmatch(r"[>|][+-]?", val):
                val = ""
            out[key] = val
        elif key and line.strip():
            out[key] = (str(out.get(key, "")) + " " + line.strip()).strip()
    return out


def _fences(lines):
    """Return list of (start, end, lang), 0-based inclusive line indexes."""
    out, open_at, lang = [], None, ""
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if not m:
            continue
        if open_at is None:
            open_at, lang = i, m.group(2).lower()
        else:
            out.append((open_at, i, lang))
            open_at = None
    if open_at is not None:
        out.append((open_at, len(lines) - 1, lang))
    return out


def _looks_like_command(lines, start, end, lang):
    if lang in ("bash", "sh", "shell", "console", "zsh"):
        return True
    for i in range(start + 1, end):
        stripped = lines[i].strip()
        if stripped:
            return bool(CMD_RE.match(stripped))
    return False


def _extract_steps(lines, fences, line_offset):
    fenced = set()
    for a, b, _ in fences:
        fenced.update(range(a, b + 1))

    anchors = []        # (line_idx, origin, label)
    heading_lines = []  # line indexes of headings
    stack = []          # [(level, text)]
    path_at = []        # heading-path snapshot per line
    for i, line in enumerate(lines):
        if i not in fenced:
            hm = HEADING_RE.match(line)
            if hm:
                level, text = len(hm.group(1)), hm.group(2)
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, text))
                heading_lines.append(i)
                if STEP_HEADING_RE.search(text):
                    anchors.append((i, "step-heading", text))
            else:
                nm = NUM_ITEM_RE.match(line)
                cm = CHECKLIST_RE.match(line)
                if nm:
                    anchors.append((i, "numbered-list", nm.group(1)))
                elif cm:
                    anchors.append((i, "checklist", cm.group(1)))
        path_at.append([t for _, t in stack])

    steps, chunks = [], []
    anchor_lines = [a for a, _, _ in anchors]
    for n, (start, origin, label) in enumerate(anchors):
        nexts = [a for a in anchor_lines if a > start] + \
                [h for h in heading_lines if h > start] + [len(lines)]
        end = min(nexts) - 1
        chunk = "\n".join(lines[start:end + 1])
        low = chunk.lower()
        blocks = [{"lang": lg, "looks_like_command": _looks_like_command(lines, a, b, lg)}
                  for a, b, lg in fences if start <= a and b <= end]
        heading_path = path_at[start]
        if origin == "step-heading" and heading_path:
            heading_path = heading_path[:-1]
        steps.append({
            "id": f"s{n + 1}",
            "origin": origin,
            "heading_path": heading_path,
            "line_start": start + 1 + line_offset,
            "line_end": end + 1 + line_offset,
            "approx_tokens": max(1, len(chunk) // 4),
            "snippet": re.sub(r"\s+", " ", str(label)).strip()[:80],
            "code_blocks": blocks,
            "mechanical_verb_hints": [v for v in MECH_VERBS
                                      if re.search(rf"\b{v}\w*\b", low)],
            "agent_tool_mentions": sorted(set(AGENT_TOOL_RE.findall(chunk))),
        })
        chunks.append(chunk)

    step_line_set = set()
    for s in steps:
        step_line_set.update(range(s["line_start"] - 1 - line_offset,
                                   s["line_end"] - line_offset))
    orphans = [{"lang": lg, "line_start": a + 1 + line_offset,
                "looks_like_command": _looks_like_command(lines, a, b, lg)}
               for a, b, lg in fences if a not in step_line_set]
    return steps, chunks, orphans


def _mentioned(name_path, stem, name, body):
    return name in body or name_path in body or stem in body


def _audit_scripts(skill_dir, body, probe):
    out = []
    sdir = skill_dir / "scripts"
    if not sdir.is_dir():
        return out
    for scr in sorted(sdir.iterdir()):
        if scr.suffix not in (".py", ".sh") or scr.name.startswith("_"):
            continue
        try:
            text = scr.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = f"scripts/{scr.name}"
        after_shebang = re.sub(r"^#![^\n]*\n", "", text).lstrip()
        rec = {
            "path": rel,
            "lines": len(text.splitlines()),
            "mentioned_in_body": _mentioned(rel, scr.stem, scr.name, body),
            "has_argparse": ("argparse" in text) if scr.suffix == ".py" else None,
            "has_docstring": (after_shebang.startswith('"""') or
                              after_shebang.startswith("'''")) if scr.suffix == ".py" else None,
            "help_ok": None,
        }
        if probe and scr.suffix == ".py":
            try:
                r = subprocess.run([sys.executable, str(scr), "--help"],
                                   stdin=subprocess.DEVNULL, capture_output=True,
                                   text=True, timeout=10)
                rec["help_ok"] = r.returncode == 0 and bool(r.stdout.strip())
            except Exception:  # noqa: BLE001 - probe failure is just help_ok=False
                rec["help_ok"] = False
        out.append(rec)
    return out


def _inventory_files(skill_dir, sub, body):
    out = []
    d = skill_dir / sub
    if not d.is_dir():
        return out
    for f in sorted(d.rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(skill_dir))
        try:
            n_lines = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            n_lines = None
        out.append({"path": rel, "lines": n_lines,
                    "mentioned_in_body": _mentioned(rel, f.stem, f.name, body)})
    return out


def _summary(inv):
    s = inv["stats"]
    lines = [f"inventory: {inv['target']}",
             f"steps: {s['n_steps']}  existing scripts: {s['n_existing_scripts']}  "
             f"references: {len(inv['references'])}  body: ~{inv['body']['approx_tokens']} tokens"]
    if s["n_steps"] == 0:
        lines.append("0 steps extracted -- the workflow may be prose-only; "
                     "read SKILL.md directly")
    for st in inv["steps"]:
        verbs = ",".join(st["mechanical_verb_hints"]) or "-"
        tools = ",".join(st["agent_tool_mentions"]) or "-"
        lines.append(f"  {st['id']} {st['origin']} L{st['line_start']}-{st['line_end']} "
                     f"~{st['approx_tokens']}tok verbs={verbs} tools={tools}")
    for sc in inv["scripts"]:
        lines.append(f"  script {sc['path']} lines={sc['lines']} "
                     f"mentioned={sc['mentioned_in_body']} argparse={sc['has_argparse']} "
                     f"help_ok={sc['help_ok']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Anchor generator + cost profiler for a target-skill-dir "
                    "under delegation review.")
    parser.add_argument("target_skill_dir", metavar="target-skill-dir",
                        help="Folder containing SKILL.md (or the SKILL.md file itself)")
    parser.add_argument("--out", help="Write full JSON here; print summary to stdout")
    parser.add_argument("--no-probe", action="store_true",
                        help="Skip the live --help probe of existing scripts")
    args = parser.parse_args(argv)

    skill_dir = Path(args.target_skill_dir)
    if skill_dir.is_file() and skill_dir.name == "SKILL.md":
        skill_dir = skill_dir.parent
    if not skill_dir.is_dir():
        print(f"error: not a directory: {skill_dir}", file=sys.stderr)
        return 2
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"error: no SKILL.md in {skill_dir}", file=sys.stderr)
        return 2

    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: cannot read {skill_md}: {e}", file=sys.stderr)
        return 2

    fm, body, fm_err = _split_frontmatter(text)
    fm = fm or {}
    if fm_err:
        print(f"warning: {fm_err}", file=sys.stderr)
    line_offset = text[: len(text) - len(body)].count("\n")

    lines = body.splitlines()
    fences = _fences(lines)
    steps, chunks, orphans = _extract_steps(lines, fences, line_offset)

    scripts = _audit_scripts(skill_dir, body, probe=not args.no_probe)
    script_names = [(s["path"], Path(s["path"]).name, Path(s["path"]).stem)
                    for s in scripts]
    for step, chunk in zip(steps, chunks):
        step["mentions_existing_script"] = [rel for rel, name, stem in script_names
                                            if name in chunk or stem in chunk]

    inv = {
        "target": str(skill_dir.resolve()),
        "frontmatter": {
            "name": str(fm.get("name") or "").strip(),
            "description_chars": len(str(fm.get("description") or "").strip()),
            "unexpected_keys": sorted(set(fm.keys()) -
                                      {"name", "description", "license",
                                       "allowed-tools", "metadata", "compatibility"}),
        },
        "body": {"lines": len(lines), "approx_tokens": max(1, len(body) // 4)},
        "steps": steps,
        "orphan_code_blocks": orphans,
        "scripts": scripts,
        "references": _inventory_files(skill_dir, "references", body),
        "assets": _inventory_files(skill_dir, "assets", body),
        "stats": {
            "n_steps": len(steps),
            "n_steps_with_hints": sum(1 for s in steps if s["mechanical_verb_hints"]),
            "n_existing_scripts": len(scripts),
        },
    }

    payload = json.dumps(inv, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(_summary(inv))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_inventory.py -v`
Expected: 6 passed.

- [ ] **Step 5: Sanity-run against a real skill**

Run: `python3 skills/delegating-to-scripts/scripts/inventory.py skills/rule-audit --out /tmp/ra.json && python3 -c "import json; d=json.load(open('/tmp/ra.json')); print(d['stats']); print([s['path']+':'+str(s['help_ok']) for s in d['scripts']])"`
Expected: nonzero `n_steps`, `n_existing_scripts` == 3, every rule-audit script `help_ok: True`.

- [ ] **Step 6: Commit**

```bash
git add skills/delegating-to-scripts/scripts/inventory.py skills/delegating-to-scripts/tests/test_inventory.py
git commit -m "feat(delegating-to-scripts): inventory.py anchor generator + cost profiler"
```

---

### Task 3: `scripts/render_report.py`

**Files:**
- Create: `skills/delegating-to-scripts/scripts/render_report.py`
- Test: `skills/delegating-to-scripts/tests/test_render_report.py`

**Interfaces:**
- Consumes: inventory JSON from Task 2 (`steps[{id, snippet, origin, line_start, line_end, approx_tokens}]`, `frontmatter.name`, `target`).
- Produces: CLI `python3 scripts/render_report.py <classification.json> <inventory.json> [--out FILE]`, exit 0/1/2. Validates + renders the report table. Classification schema (the contract Claude writes in workflow step 2):

```json
{
  "target": "/abs/path/to/target-skill",
  "steps": [
    {"id": "s2",
     "class": "SCRIPT",
     "why": "same regex check every run",
     "proposed_script": {
       "name": "check_headings.py",
       "interface": "python3 scripts/check_headings.py changelogs/ --json",
       "stdout": "findings JSON",
       "exit": "0 clean / 1 findings / 2 usage"}}
  ]
}
```

`class` is one of `SCRIPT | CLAUDE | HYBRID | DEAD | ALREADY_DELEGATED`. SCRIPT/HYBRID require `proposed_script` with all four keys; the other classes must omit it or set null. Every inventory step must be classified.

- [ ] **Step 1: Write the failing test**

`skills/delegating-to-scripts/tests/test_render_report.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "render_report.py"

INVENTORY = {
    "target": "/tmp/fake-skill",
    "frontmatter": {"name": "fake-skill", "description_chars": 200, "unexpected_keys": []},
    "body": {"lines": 40, "approx_tokens": 400},
    "steps": [
        {"id": "s1", "origin": "numbered-list", "heading_path": ["Workflow"],
         "line_start": 10, "line_end": 12, "approx_tokens": 55,
         "snippet": "List every .md file", "code_blocks": [],
         "mechanical_verb_hints": ["list"], "agent_tool_mentions": [],
         "mentions_existing_script": []},
        {"id": "s2", "origin": "numbered-list", "heading_path": ["Workflow"],
         "line_start": 13, "line_end": 15, "approx_tokens": 80,
         "snippet": "Write a narrative", "code_blocks": [],
         "mechanical_verb_hints": [], "agent_tool_mentions": [],
         "mentions_existing_script": []},
    ],
    "orphan_code_blocks": [], "scripts": [], "references": [], "assets": [],
    "stats": {"n_steps": 2, "n_steps_with_hints": 1, "n_existing_scripts": 0},
}

GOOD_CLASSIFICATION = {
    "target": "/tmp/fake-skill",
    "steps": [
        {"id": "s1", "class": "SCRIPT", "why": "pure file discovery",
         "proposed_script": {"name": "list_files.py",
                             "interface": "python3 scripts/list_files.py docs/ --json",
                             "stdout": "file list JSON",
                             "exit": "0 ok / 2 usage"}},
        {"id": "s2", "class": "CLAUDE", "why": "prose synthesis",
         "proposed_script": None},
    ],
}


def run(tmp_path, classification, inventory=INVENTORY, extra=()):
    c = tmp_path / "classification.json"
    i = tmp_path / "inventory.json"
    c.write_text(json.dumps(classification))
    i.write_text(json.dumps(inventory))
    return subprocess.run([sys.executable, str(SCRIPT), str(c), str(i), *extra],
                          capture_output=True, text=True, timeout=30)


def test_renders_table(tmp_path):
    r = run(tmp_path, GOOD_CLASSIFICATION)
    assert r.returncode == 0, r.stderr
    assert "## Delegation review: fake-skill" in r.stdout
    assert "1 of 2 steps" in r.stdout
    assert "| s1 |" in r.stdout and "| SCRIPT |" in r.stdout
    assert "| s2 |" in r.stdout and "| CLAUDE |" in r.stdout
    assert "list_files.py" in r.stdout
    # CLAUDE rows carry no interface
    s2_row = [l for l in r.stdout.splitlines() if l.startswith("| s2 |")][0]
    assert "list_files.py" not in s2_row


def test_unknown_id_exits_1(tmp_path):
    bad = {"target": "/tmp/fake-skill",
           "steps": GOOD_CLASSIFICATION["steps"] +
                    [{"id": "s9", "class": "CLAUDE", "why": "x", "proposed_script": None}]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "s9" in r.stderr


def test_script_class_requires_interface(tmp_path):
    bad = {"target": "/tmp/fake-skill",
           "steps": [{"id": "s1", "class": "SCRIPT", "why": "x", "proposed_script": None},
                     {"id": "s2", "class": "CLAUDE", "why": "y", "proposed_script": None}]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "proposed_script" in r.stderr


def test_unclassified_step_exits_1(tmp_path):
    bad = {"target": "/tmp/fake-skill", "steps": [GOOD_CLASSIFICATION["steps"][0]]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "s2" in r.stderr


def test_missing_file_exits_2(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "/nope.json", "/nope2.json"],
                       capture_output=True, text=True)
    assert r.returncode == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_render_report.py -v`
Expected: FAIL — script missing.

- [ ] **Step 3: Write render_report.py**

`skills/delegating-to-scripts/scripts/render_report.py`:

```python
#!/usr/bin/env python3
"""
render_report.py - Render the delegation-review report from classification.json
plus inventory.json, validating the classification in the process.

The classification is the agent's judgment; this script is its consumer AND its
validator: it joins classification entries to inventory step anchors by id,
rejects unknown ids / unclassified steps / bad classes / interface omissions,
and renders the fixed report template so the table is never hand-typed.

CLASSIFICATION SCHEMA (.delegation-review/classification.json)
{
  "target": "/abs/path/to/target-skill",
  "steps": [
    {"id": "s2",
     "class": "SCRIPT",            // SCRIPT | CLAUDE | HYBRID | DEAD | ALREADY_DELEGATED
     "why": "same regex check every run",
     "proposed_script": {          // REQUIRED for SCRIPT/HYBRID, null otherwise
       "name": "check_headings.py",
       "interface": "python3 scripts/check_headings.py changelogs/ --json",
       "stdout": "findings JSON",
       "exit": "0 clean / 1 findings / 2 usage"}}
  ]
}

USAGE
    python3 scripts/render_report.py <classification.json> <inventory.json> [--out FILE]

EXIT CODES
    0  Report rendered.
    1  Classification invalid; every problem named on stderr.
    2  Usage error / unreadable or unparseable input file.
"""

import argparse
import json
import sys
from pathlib import Path

CLASSES = {"SCRIPT", "CLAUDE", "HYBRID", "DEAD", "ALREADY_DELEGATED"}
NEEDS_SCRIPT = {"SCRIPT", "HYBRID"}


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except OSError as e:
        return None, f"cannot read {path}: {e}"
    except ValueError as e:
        return None, f"{path} is not valid JSON: {e}"


def validate(cls, inv):
    errors = []
    inv_ids = {s["id"] for s in inv.get("steps", [])}
    seen = set()
    for i, st in enumerate(cls.get("steps", [])):
        sid = st.get("id")
        where = f"steps[{i}] (id={sid})"
        if sid not in inv_ids:
            errors.append(f"{where}: unknown step id (not in inventory)")
            continue
        if sid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(sid)
        klass = st.get("class")
        if klass not in CLASSES:
            errors.append(f"{where}: class must be one of "
                          f"{sorted(CLASSES)}, got {klass!r}")
            continue
        if not str(st.get("why") or "").strip():
            errors.append(f"{where}: missing 'why'")
        ps = st.get("proposed_script")
        if klass in NEEDS_SCRIPT:
            missing = [k for k in ("name", "interface", "stdout", "exit")
                       if not (ps or {}).get(k)]
            if missing:
                errors.append(f"{where}: class {klass} requires proposed_script "
                              f"with fields {missing}")
        elif ps:
            errors.append(f"{where}: class {klass} must not carry a proposed_script")
    unclassified = sorted(inv_ids - seen)
    if unclassified:
        errors.append(f"unclassified inventory steps: {unclassified}")
    return errors


def render(cls, inv):
    by_id = {s["id"]: s for s in cls["steps"]}
    mech = [s for s in inv["steps"] if by_id[s["id"]]["class"] in NEEDS_SCRIPT]
    tok = sum(s["approx_tokens"] for s in mech)
    name = inv.get("frontmatter", {}).get("name") or inv.get("target", "?")
    out = [
        f"## Delegation review: {name}",
        "",
        f"**Verdict:** {len(mech)} of {len(inv['steps'])} steps are mechanical "
        f"(SCRIPT/HYBRID); delegating them removes ~{tok} tokens of per-run reasoning.",
        "",
        "| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |",
        "|---|-------------|--------------|--------|-------|-----|---------------------------|",
    ]
    for s in inv["steps"]:
        c = by_id[s["id"]]
        ps = c.get("proposed_script")
        iface = (f"`{ps['interface']}` -> {ps['stdout']}, exit {ps['exit']}"
                 if ps else "-")
        out.append(f"| {s['id']} | \"{s['snippet']}\" (L{s['line_start']}-{s['line_end']}) "
                   f"| {s['origin']} | {s['approx_tokens']} | {c['class']} "
                   f"| {c['why']} | {iface} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a delegation classification and render the report table.")
    parser.add_argument("classification", help="Path to classification.json")
    parser.add_argument("inventory", help="Path to inventory.json")
    parser.add_argument("--out", help="Write the report here instead of stdout")
    args = parser.parse_args(argv)

    cls, err = _load(args.classification)
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    inv, err = _load(args.inventory)
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    errors = validate(cls, inv)
    if errors:
        for e in errors:
            print(f"invalid classification: {e}", file=sys.stderr)
        return 1

    report = render(cls, inv)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"report written to {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_render_report.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/delegating-to-scripts/scripts/render_report.py skills/delegating-to-scripts/tests/test_render_report.py
git commit -m "feat(delegating-to-scripts): render_report.py classification validator + renderer"
```

---

### Task 4: `scripts/smoke_test.py`

**Files:**
- Create: `skills/delegating-to-scripts/scripts/smoke_test.py`
- Test: `skills/delegating-to-scripts/tests/test_smoke_test.py`

**Interfaces:**
- Consumes: a manifest JSON written by the agent during the contract-first step (before the generated scripts exist).
- Produces: CLI `python3 scripts/smoke_test.py <manifest.json> [--timeout SECS] [--only NAME] [--json]`, exit 0/1/2. Manifest schema (also documented in the script docstring — the docstring is the authoritative copy the agent reads):

```json
{
  "target_skill": "/abs/path/to/target-skill",
  "scripts": [
    {
      "path": "scripts/check_headings.py",
      "kind": "check",
      "invocations": [
        {"argv": ["python3", "scripts/check_headings.py", "changelogs-good", "--json"],
         "cwd": ".delegation-review/fixtures/check_headings",
         "expect_exit": 0,
         "expect_stdout_json": true,
         "expect_stdout_contains": "[]"}
      ],
      "bad_data_invocation": {
        "argv": ["python3", "scripts/check_headings.py", "changelogs-bad", "--json"],
        "cwd": ".delegation-review/fixtures/check_headings",
        "expect_exit_nonzero": true,
        "expect_stdout_contains": "missing_version_header"},
      "bad_invocation": {
        "argv": ["python3", "scripts/check_headings.py"],
        "expect_exit_nonzero": true}
    }
  ]
}
```

Rules: `kind` is `"check"` (validates/flags data — REQUIRES `bad_data_invocation` against the failing fixture) or `"transform"`. Relative `argv`/`cwd` paths resolve against `target_skill`. Checks per script: `exists`, `help`, `fixture-run[i]`, `bad-data`, `bad-args`.

- [ ] **Step 1: Write the failing test**

`skills/delegating-to-scripts/tests/test_smoke_test.py`:

```python
import json
import subprocess
import sys
import textwrap
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "smoke_test.py"

GOOD_SCRIPT = textwrap.dedent('''\
    #!/usr/bin/env python3
    """toy checker. Exits 0 if the file contains 'ok', else 1 with a finding."""
    import argparse, sys
    p = argparse.ArgumentParser(description="toy checker")
    p.add_argument("file")
    a = p.parse_args()
    text = open(a.file).read()
    if "ok" in text:
        print("[]")
        sys.exit(0)
    print("finding: missing_ok")
    sys.exit(1)
''')

INTERACTIVE_SCRIPT = textwrap.dedent('''\
    #!/usr/bin/env python3
    import argparse
    p = argparse.ArgumentParser()
    p.parse_args()
    answer = input("continue? ")
    print(answer)
''')


def make_target(tmp_path):
    target = tmp_path / "target"
    (target / "scripts").mkdir(parents=True)
    (target / "scripts" / "toy_check.py").write_text(GOOD_SCRIPT)
    (target / "good.txt").write_text("all ok here")
    (target / "bad.txt").write_text("nothing here")
    return target


def manifest_for(target, expect_exit_good=0):
    return {
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/toy_check.py",
            "kind": "check",
            "invocations": [
                {"argv": [sys.executable, "scripts/toy_check.py", "good.txt"],
                 "expect_exit": expect_exit_good,
                 "expect_stdout_json": True}],
            "bad_data_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py", "bad.txt"],
                "expect_exit_nonzero": True,
                "expect_stdout_contains": "missing_ok"},
            "bad_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py"],
                "expect_exit_nonzero": True},
        }],
    }


def run(manifest_path, *extra):
    return subprocess.run([sys.executable, str(SCRIPT), str(manifest_path), *extra],
                          capture_output=True, text=True, timeout=120)


def test_all_pass(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target)))
    r = run(mf)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout


def test_wrong_expect_exit_fails(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target, expect_exit_good=3)))
    r = run(mf)
    assert r.returncode == 1
    assert "FAIL" in r.stdout


def test_interactive_script_flagged(tmp_path):
    target = make_target(tmp_path)
    (target / "scripts" / "toy_check.py").write_text(INTERACTIVE_SCRIPT)
    mf = tmp_path / "manifest.json"
    m = manifest_for(target)
    m["scripts"][0]["invocations"][0]["argv"] = [sys.executable, "scripts/toy_check.py"]
    m["scripts"][0]["invocations"][0].pop("expect_stdout_json")
    mf.write_text(json.dumps(m))
    r = run(mf, "--timeout", "10")
    assert r.returncode == 1
    # input() with stdin=DEVNULL raises EOFError -> nonzero exit -> exit mismatch FAIL;
    # a /dev/tty reader would hit the timeout -> 'interactive-or-hung'
    assert "FAIL" in r.stdout


def test_check_without_bad_data_rejected(tmp_path):
    target = make_target(tmp_path)
    m = manifest_for(target)
    del m["scripts"][0]["bad_data_invocation"]
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(m))
    r = run(mf)
    assert r.returncode == 2
    assert "bad_data_invocation" in r.stderr


def test_garbage_manifest_exits_2(tmp_path):
    mf = tmp_path / "manifest.json"
    mf.write_text("{not json")
    r = run(mf)
    assert r.returncode == 2


def test_json_output(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target)))
    r = run(mf, "--json")
    assert r.returncode == 0
    results = json.loads(r.stdout)
    checks = {c["check"] for c in results}
    assert {"exists", "help", "fixture-run[0]", "bad-data", "bad-args"} <= checks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_smoke_test.py -v`
Expected: FAIL — script missing.

- [ ] **Step 3: Write smoke_test.py**

`skills/delegating-to-scripts/scripts/smoke_test.py`:

```python
#!/usr/bin/env python3
"""
smoke_test.py - Verify generated scripts are agent-callable, driven by a
manifest of declared invocations.

The manifest is written by the agent during the contract-first step, BEFORE
the scripts exist, from the target step's semantics -- so the expectations are
not derived from the script's own output (no self-grading).

MANIFEST SCHEMA (.delegation-review/manifest.json)
{
  "target_skill": "/abs/path/to/target-skill",
  "scripts": [
    {
      "path": "scripts/check_headings.py",   // relative to target_skill
      "kind": "check",                       // "check" | "transform".
                                             // "check" (validates/flags data)
                                             // REQUIRES bad_data_invocation.
      "invocations": [                       // happy-path runs
        {"argv": ["python3", "scripts/check_headings.py", "changelogs-good", "--json"],
         "cwd": ".delegation-review/fixtures/check_headings",  // optional,
                                             // default target_skill; relative
                                             // paths resolve against target_skill
         "expect_exit": 0,
         "expect_stdout_json": true,         // optional
         "expect_stdout_contains": "[]"}     // optional
      ],
      "bad_data_invocation": {               // run against the FAILING fixture;
                                             // proves the logic discriminates,
                                             // not just that the interface works
        "argv": ["python3", "scripts/check_headings.py", "changelogs-bad", "--json"],
        "cwd": ".delegation-review/fixtures/check_headings",
        "expect_exit_nonzero": true,
        "expect_stdout_contains": "missing_version_header"},
      "bad_invocation": {                    // bad ARGS: must exit nonzero AND
                                             // write something to stderr
        "argv": ["python3", "scripts/check_headings.py"],
        "expect_exit_nonzero": true}
    }
  ]
}

CHECKS PER SCRIPT (each a named PASS/FAIL line)
    exists          file present under target_skill
    help            `python3 <script> --help` exits 0 with non-empty usage
    fixture-run[i]  each declared invocation matches its expectations
    bad-data        the failing fixture produces the declared finding
    bad-args        the bad invocation exits nonzero AND writes to stderr

Interactive scripts surface as FAIL: stdin is closed (input() raises
EOFError -> unexpected exit code) and every run has a timeout (a /dev/tty
reader hangs -> reason "interactive-or-hung").

USAGE
    python3 scripts/smoke_test.py <manifest.json> [--timeout SECS] [--only NAME] [--json]

EXIT CODES
    0  All checks pass.
    1  One or more checks failed.
    2  Manifest missing/unreadable/schema-invalid (message names the field).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _schema_errors(m):
    errs = []
    if not isinstance(m, dict):
        return ["manifest root must be a JSON object"]
    tgt = m.get("target_skill")
    if not tgt:
        errs.append("missing field: target_skill")
    elif not Path(tgt).is_dir():
        errs.append(f"target_skill is not a directory: {tgt}")
    scripts = m.get("scripts")
    if not isinstance(scripts, list) or not scripts:
        errs.append("missing or empty field: scripts")
        return errs
    for i, s in enumerate(scripts):
        w = f"scripts[{i}]"
        if not s.get("path"):
            errs.append(f"{w}: missing field: path")
        kind = s.get("kind")
        if kind not in ("check", "transform"):
            errs.append(f"{w}: kind must be 'check' or 'transform', got {kind!r}")
        if not s.get("invocations"):
            errs.append(f"{w}: missing or empty field: invocations")
        if kind == "check" and not s.get("bad_data_invocation"):
            errs.append(f"{w}: kind 'check' requires bad_data_invocation "
                        "(a run against the failing fixture)")
        if not s.get("bad_invocation"):
            errs.append(f"{w}: missing field: bad_invocation")
        for j, inv in enumerate(s.get("invocations") or []):
            if not inv.get("argv"):
                errs.append(f"{w}.invocations[{j}]: missing field: argv")
    return errs


def _run(argv, cwd, timeout):
    """Return (exit_code, stdout, stderr, hard_failure_reason_or_None)."""
    try:
        r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr, None
    except subprocess.TimeoutExpired:
        return None, "", "", "interactive-or-hung"
    except (FileNotFoundError, PermissionError, NotADirectoryError) as e:
        return None, "", "", f"exec-failed: {e}"


def _resolve_cwd(spec, base):
    cwd = spec.get("cwd", ".")
    p = Path(cwd)
    return str(p if p.is_absolute() else (base / p))


def _expectations(spec, code, out, want_nonzero):
    if want_nonzero or spec.get("expect_exit_nonzero"):
        if code == 0:
            return "expected nonzero exit, got 0"
    elif "expect_exit" in spec and code != spec["expect_exit"]:
        return f"expected exit {spec['expect_exit']}, got {code}"
    if spec.get("expect_stdout_json"):
        try:
            json.loads(out)
        except ValueError:
            return "stdout is not valid JSON"
    sub = spec.get("expect_stdout_contains")
    if sub and sub not in out:
        return f"stdout missing expected substring: {sub!r}"
    return ""


def run_checks(m, timeout, only=None):
    base = Path(m["target_skill"])
    results = []

    def add(script, check, ok, reason="", cmd="", code=None, stderr=""):
        results.append({"script": script, "check": check,
                        "status": "PASS" if ok else "FAIL", "reason": reason,
                        "cmd": cmd, "exit": code,
                        "stderr_head": "\n".join((stderr or "").splitlines()[:10])})

    for s in m["scripts"]:
        name = s["path"]
        if only and only not in name:
            continue
        path = base / name
        ok = path.is_file()
        add(name, "exists", ok, "" if ok else f"not found: {path}")
        if not ok:
            continue

        argv = [sys.executable, str(path), "--help"]
        code, out, err, hard = _run(argv, str(base), timeout)
        ok = hard is None and code == 0 and bool(out.strip())
        add(name, "help", ok,
            hard or ("" if ok else f"--help exit={code}, usage-empty={not out.strip()}"),
            " ".join(argv), code, err)

        for j, inv in enumerate(s["invocations"]):
            code, out, err, hard = _run(inv["argv"], _resolve_cwd(inv, base), timeout)
            reason = hard or _expectations(inv, code, out, want_nonzero=False)
            add(name, f"fixture-run[{j}]", not reason, reason,
                " ".join(inv["argv"]), code, err)

        bd = s.get("bad_data_invocation")
        if bd:
            code, out, err, hard = _run(bd["argv"], _resolve_cwd(bd, base), timeout)
            reason = hard or _expectations(bd, code, out, want_nonzero=True)
            add(name, "bad-data", not reason, reason, " ".join(bd["argv"]), code, err)

        bi = s["bad_invocation"]
        code, out, err, hard = _run(bi["argv"], _resolve_cwd(bi, base), timeout)
        ok = hard is None and code not in (0, None) and bool(err.strip())
        add(name, "bad-args", ok,
            hard or ("" if ok else
                     f"exit={code} (must be nonzero), stderr-empty={not (err or '').strip()}"),
            " ".join(bi["argv"]), code, err)
    return results


def render(results):
    lines = []
    for r in results:
        lines.append(f"{r['status']}  {r['script']}  {r['check']}")
        if r["status"] == "FAIL":
            lines.append(f"      reason : {r['reason']}")
            if r["cmd"]:
                lines.append(f"      cmd    : {r['cmd']}  (exit {r['exit']})")
            if r["stderr_head"]:
                for l in r["stderr_head"].splitlines():
                    lines.append(f"      stderr | {l}")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    lines.append(f"\n{len(results) - n_fail}/{len(results)} checks passed")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Smoke-test generated scripts against a declared manifest.")
    parser.add_argument("manifest", help="Path to manifest.json")
    parser.add_argument("--timeout", type=float, default=20.0,
                        help="Per-run timeout in seconds (default 20)")
    parser.add_argument("--only", help="Only test scripts whose path contains NAME")
    parser.add_argument("--json", action="store_true",
                        help="Emit structured results instead of the table")
    args = parser.parse_args(argv)

    try:
        m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error: manifest is not valid JSON: {e}", file=sys.stderr)
        return 2

    errs = _schema_errors(m)
    if errs:
        for e in errs:
            print(f"manifest invalid: {e}", file=sys.stderr)
        return 2

    results = run_checks(m, args.timeout, args.only)
    print(json.dumps(results, indent=2) if args.json else render(results))
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/test_smoke_test.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run the full suite**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/ -v`
Expected: all pass (inventory 6 + render 5 + smoke 6 = 17).

- [ ] **Step 6: Commit**

```bash
git add skills/delegating-to-scripts/scripts/smoke_test.py skills/delegating-to-scripts/tests/test_smoke_test.py
git commit -m "feat(delegating-to-scripts): smoke_test.py manifest-driven verifier"
```

---

### Task 5: References — `delegation-rubric.md` and `script-conventions.md`

**Files:**
- Create: `skills/delegating-to-scripts/references/delegation-rubric.md`
- Create: `skills/delegating-to-scripts/references/script-conventions.md`

**Interfaces:**
- Consumes: nothing (pure docs).
- Produces: the classification criteria the SKILL.md workflow step 2 tells Claude to read, and the generated-script interface rules workflow step 6 tells Claude to follow.

- [ ] **Step 1: Write delegation-rubric.md**

```markdown
# Delegation Rubric: SCRIPT, CLAUDE, HYBRID, or DEAD

## Contents

- [The core test](#the-core-test)
- [The four classifications](#the-four-classifications)
- [Commonly delegable (SCRIPT) categories](#commonly-delegable-script-categories)
- [Commonly Claude-needed (CLAUDE) categories](#commonly-claude-needed-claude-categories)
- [Hybrid shapes](#hybrid-shapes)
- [Gotchas](#gotchas)

## The core test

**Would two different Claude runs produce meaningfully different output on this
step? If no — SCRIPT.**

A deterministic step re-derived in prose is paid for on every run: tokens to
re-think it, latency to re-generate it, and variance because generation is
stochastic. A script pays that cost once, at authoring time. That is the whole
economics of delegation (see skill-reviewer's `references/token-economics.md`
for the long version).

Secondary test for close calls: **could you write the unit test for this step's
output right now?** If yes, the step is deterministic enough to script. If you
cannot say what the correct output is without seeing the input, it needs
judgment — CLAUDE or HYBRID.

## The four classifications

**SCRIPT** — the step is a function of its inputs. Fully delegable. The
rewritten step becomes one exact command line ("Run exactly: ..."). Examples:
"check every file starts with a version header", "count entries per category".

**CLAUDE** — judgment, synthesis, or conversation-dependent. Scripting it
would fake determinism: the script would encode one arbitrary answer to a
question that genuinely varies. The step stays prose. Examples: "write the
release narrative", "decide which findings matter to this user".

**HYBRID** — a script prepares (gathers, counts, sorts, filters, structures),
Claude decides. The rewritten step becomes "run X, then apply judgment to its
output". In-repo precedent: skill-reviewer's `audit.py` produces a mechanical
severity guess that the agent re-triages — that is the HYBRID shape.

**DEAD** — the step should not exist: stale, duplicative, or superseded.
Do not force a script onto it. Flag it in the report and route it to a
`skill-reviewer` follow-up; never auto-delete another skill's steps.

Steps already backed by an adequate existing script (the inventory's interface
audit shows `mentioned_in_body`, `has_argparse`, `help_ok`) are classified
**ALREADY_DELEGATED** and skipped.

## Commonly delegable (SCRIPT) categories

- **Parsing/extraction** — frontmatter, JSON, log formats, structured text.
- **Fixed-rule validation** — schema checks, required fields, regex-style
  lint rules ("every heading matches the version pattern").
- **File discovery/inventory** — globbing, "list all X", mentioned-in-body
  cross-checks.
- **Report rendering from structured data** — sorting, tables, fixed markdown
  templates.
- **Diffing** — baseline vs after, set differences.
- **Aggregation/counting/statistics** — per-category tallies, totals, line
  counts, token estimates.
- **Format conversion** — CSV to JSON, one markdown shape to another.

## Commonly Claude-needed (CLAUDE) categories

- **Judgment and trade-offs** — anything where reasonable runs disagree.
- **Contextual classification** — severity re-triage, intent inference,
  "does this Misc entry really belong under Fixed?".
- **Prose writing** — summaries, narratives, explanations, descriptions.
- **Design decisions and naming.**
- **Conversation-reading** — a script cannot see pasted text or user answers.
- **User negotiation** — AskUserQuestion steps, approval gates.
- **Agent-runtime-tool steps** — anything invoking MCP tools, WebFetch,
  AskUserQuestion, subagent/Task dispatch, or other permission-gated tools.
  Never pure SCRIPT: a script reimplementation (e.g. curl instead of an MCP
  call) silently loses auth, the permission model, and rate handling. At most
  HYBRID around the tool call (script prepares input / digests output).

## Hybrid shapes

1. **Extract-then-judge** — script lists candidates, Claude filters or
   interprets. (inventory.py feeding classification is itself this shape.)
2. **Judge-then-render** — Claude produces structured JSON, a script validates
   and renders it. This is the plan-validate-execute pattern; render_report.py
   is the in-skill example.
3. **Script-gates-judgment** — the script's exit code decides whether Claude
   engages at all ("exit 0: nothing to review, stop here").

## Gotchas

- **Mechanical verbs lie.** "Validate the approach with the user" contains
  "validate" and is CLAUDE. The inventory's verb hints are hints, not verdicts.
- **A trivial one-liner needs no bundled script.** One `ls` or one `grep` is
  fine inline. The threshold: hard to get right on the first try, or must run
  identically on every invocation.
- **Authoring-time vs run-time.** Don't script a step that runs once when the
  skill is written rather than every time the skill runs.
- **Scripting judgment hides variance behind false authority.** A wrong script
  is worse than prose: it fails silently and looks official.
- **Watch output size.** A delegated step that dumps 40KB into context traded
  token cost for token cost. Large output goes to a file via `--out`; stdout
  carries a compact summary.
- **Failure modes flip.** Prose degrades gracefully; scripts fail hard.
  Meaningful exit codes and verbose error messages are what make hard failure
  a feature instead of a trap.
```

- [ ] **Step 2: Write script-conventions.md**

```markdown
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
```

- [ ] **Step 3: Verify the rubric against fixture A (hand-classification)**

Read `skills/delegating-to-scripts/evals/fixtures/changelog-checker/SKILL.md` and classify each of the 7 steps using ONLY the rubric text. Expected result — s1 SCRIPT (file discovery), s2 SCRIPT (fixed-rule validation), s3 SCRIPT (aggregation), s4 CLAUDE (prose writing), s5 SCRIPT (report rendering), s6 HYBRID (extract-then-judge: tag check is fixed-rule, Misc re-homing is contextual classification), s7 CLAUDE (trap: "verify ... clearly written" is judgment despite the verb). If any classification needs knowledge not in the rubric, extend the rubric before proceeding.

- [ ] **Step 4: Commit**

```bash
git add skills/delegating-to-scripts/references
git commit -m "feat(delegating-to-scripts): delegation rubric + script conventions"
```

---

### Task 6: `SKILL.md`

**Files:**
- Create: `skills/delegating-to-scripts/SKILL.md`

**Interfaces:**
- Consumes: all three scripts (Tasks 2-4) by exact invocation; both references (Task 5) by name.
- Produces: the user-facing skill. Workdir contract: everything transient lives in `.delegation-review/` in the cwd.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: delegating-to-scripts
description: >-
  Reviews a target skill folder to find workflow steps that should be delegated
  to pre-written deterministic scripts instead of being re-derived in prose on
  every run, then, after the user picks which delegations to apply, writes
  those scripts into the target skill, rewrites its SKILL.md steps to invoke
  them, and smoke-tests every generated script. Operating principle: always use
  a script unless Claude is needed specifically. Use whenever the user wants to
  scriptify a skill, make a skill more deterministic, reduce a skill's token
  cost or run-to-run variance, move mechanical work like parsing, validation,
  counting, or report rendering into scripts, or asks which parts of a skill
  should be scripts or why a skill gives different output every run. Do NOT use
  for a general skill quality or triggering review with no intent to add
  scripts (use skill-reviewer), and do NOT use to author a brand-new skill from
  scratch (use smart-skill-creator).
---

# Delegating Skill Steps to Scripts

Convert a skill's mechanical workflow steps into pre-written scripts.
Principle: **always use a script unless Claude is needed specifically** — a
deterministic step re-derived in prose costs tokens, latency, and variance on
every run; a script pays once.

Scripts live in `scripts/`. **Run them; don't reimplement them.**

This skill CHANGES the target skill. For a read-only quality review use the
sibling `skill-reviewer` — and running it on the target after this skill
finishes is a good final check.

Below, `<skill>` = this skill's folder; "target" = the skill under review.
Transient files live in `.delegation-review/` in the working directory.

## Step 0 — Locate the target and check eligibility

Find the folder containing the target SKILL.md. If the user pasted SKILL.md
content, save it to a scratch folder first. No SKILL.md at all → this skill
reviews skills, not arbitrary markdown; say so and stop.

Eligibility: the target must be writable, user-owned, and OUTSIDE plugin/cache
paths (anything under a plugins cache such as `~/.claude/plugins/` or
`.claude-personal/plugins/cache/`) — scripts written into a plugin cache are
silently clobbered on the next plugin update. Ineligible target → run
report-only (steps 1-4), then offer to copy the skill into the project.

Check `git status` for the target SKILL.md. If it has uncommitted changes,
warn the user and copy it to `.delegation-review/SKILL.md.orig` before
anything else — that copy is the restore point.

## Step 1 — Inventory (deterministic)

    mkdir -p .delegation-review
    python3 <skill>/scripts/inventory.py <target-dir> --out .delegation-review/inventory.json

Stdout is counts and hints only. The inventory extracts candidates — it does
NOT classify, and its verb/tool hints are hints, not verdicts. Now read the
target SKILL.md itself: the inventory is the map, not the territory.

## Step 2 — Classify (judgment)

Read `references/delegation-rubric.md`, then classify every inventoried step:
SCRIPT, CLAUDE, HYBRID, DEAD, or ALREADY_DELEGATED. Write the decisions to
`.delegation-review/classification.json` — terse: reference inventory step ids,
never duplicate step text. Schema (full version in render_report.py's header):

    {"target": "<abs path>", "steps": [
      {"id": "s2", "class": "SCRIPT", "why": "same regex check every run",
       "proposed_script": {"name": "check_headings.py",
         "interface": "python3 scripts/check_headings.py changelogs/ --json",
         "stdout": "findings JSON", "exit": "0 clean / 1 findings / 2 usage"}}]}

SCRIPT and HYBRID entries need a full proposed_script; the rest set it null.

## Step 3 — Render the report

    python3 <skill>/scripts/render_report.py .delegation-review/classification.json .delegation-review/inventory.json

Exit 1 means the classification is invalid — fix classification.json per the
stderr messages and re-run. Paste the rendered report to the user verbatim.

## Step 4 — Gate: the user picks

Ask with AskUserQuestion (multiSelect): one option per SCRIPT/HYBRID row. More
than 4 candidates → present the top 4 by the inventory's per-step
`approx_tokens` (highest first) and say in the question text that Other
accepts row ids or "all". Include a final option: keep verification residue
(fixtures + manifest) in the target's `scripts/tests/` afterward (default off).

No pick → stop after the report. Never write into the target without an
explicit pick.

## Step 5 — Contract first (before any script exists)

For each chosen row, derive the test expectations from the step's SEMANTICS —
what the prose says the step must catch — not from any script output:

1. Create fixtures under `.delegation-review/fixtures/<script-name>/`. Every
   validation/check script gets at least one passing AND one failing example.
2. Append the entry to `.delegation-review/manifest.json` (schema in
   smoke_test.py's header): happy-path invocation(s), a `bad_data_invocation`
   against the failing fixture asserting the finding, and a `bad_invocation`
   with broken args.

Re-read `.delegation-review/classification.json` from disk here — work from
the recorded decisions, not chat memory.

## Step 6 — Implement the scripts

Write each script into `<target>/scripts/`, built to pass the manifest you
already wrote. Follow `references/script-conventions.md` (argv-only, exit
codes 0/1/2, JSON to stdout, --help, header docstring). Name collision with an
existing file → ask the user; never silently overwrite. Do NOT touch the
target SKILL.md in this step.

## Step 7 — Smoke test

    python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json

On FAIL: fix the script, not the expectation (unless the expectation misread
the step's semantics — say so if you change one), and re-run until exit 0.
Red run → stop here; the target SKILL.md is still pristine and
`.delegation-review/` is preserved for resumption. Never claim done on red.

## Step 8 — Rewrite the target SKILL.md (atomic, last)

Only after green. Rewrite all chosen steps in ONE pass. Lossless rule: replace
only the mechanical instruction with the exact invocation ("Run exactly:
`python3 scripts/check_headings.py changelogs/ --json`"); keep rationale,
branching, and gotcha sentences verbatim. HYBRID steps become "run the script,
then apply judgment to its output" — the judgment prose stays. Show the user
the unified diff of the SKILL.md change.

## Step 9 — Wrap up

Summarize: scripts written, the diff already shown, the smoke PASS line, and
any DEAD steps flagged for a skill-reviewer follow-up. If the user chose to
keep residue, move `.delegation-review/fixtures/` and `manifest.json` to
`<target>/scripts/tests/` and note the smoke command in the target's body
(future runs can re-verify instead of regenerating). Otherwise remove
`.delegation-review/` — but only after a fully green run.

## Gotchas

- Mechanical verbs lie: "validate the approach with the user" is CLAUDE.
- Steps invoking agent-runtime tools (MCP, WebFetch, AskUserQuestion, subagent
  dispatch) are never pure SCRIPT — a script rewrite loses auth, permissions,
  and rate handling. At most HYBRID around the tool call.
- A one-liner (`ls`, single `grep`) needs no bundled script; the threshold is
  "hard to get right first try, or must run identically every invocation".
- Don't script steps that run once at skill-authoring time.
- Don't delegate steps that read conversation context — scripts can't see it.
- Scripting a judgment step doesn't remove variance; it hides it behind false
  authority.
- Big output needs `--out` — dumping 40KB to stdout trades token cost for
  token cost.
- Some steps deserve deletion, not delegation: classify DEAD, don't force a
  script onto a step that shouldn't exist.

## Bundled files

| Script (run, don't reimplement) | Does |
|---|---|
| `scripts/inventory.py <target> --out F` | step anchors, token costs, hints, existing-script audit; exit 0/2 |
| `scripts/render_report.py <cls> <inv>` | validates classification, renders report; exit 0/1/2 |
| `scripts/smoke_test.py <manifest>` | verifies generated scripts; exit 0/1/2 |

| Reference | Read at |
|---|---|
| `references/delegation-rubric.md` | Step 2, before classifying |
| `references/script-conventions.md` | Step 6, before writing scripts |
```

- [ ] **Step 2: Verify with the skill-reviewer audit**

Run: `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts`
Expected: exit 0 or only low findings; specifically NO high findings (description under 1024 chars, no angle brackets, when-signals present, all scripts and references mentioned in body). If the description exceeds 1024 chars, trim trigger phrases until it passes.

- [ ] **Step 3: Check body size**

Run: `python3 -c "print(sum(1 for _ in open('skills/delegating-to-scripts/SKILL.md')))"`
Expected: under 300 lines.

- [ ] **Step 4: Commit**

```bash
git add skills/delegating-to-scripts/SKILL.md
git commit -m "feat(delegating-to-scripts): SKILL.md workflow"
```

---

### Task 7: Fixture B + `evals/evals.json`

**Files:**
- Create: `skills/delegating-to-scripts/evals/fixtures/well-delegated/SKILL.md`
- Create: `skills/delegating-to-scripts/evals/fixtures/well-delegated/scripts/check.py`
- Create: `skills/delegating-to-scripts/evals/fixtures/well-delegated/notes/welcome.md`
- Create: `skills/delegating-to-scripts/evals/evals.json`

**Interfaces:**
- Consumes: fixture A (Task 1) referenced by eval prompts; eval schema copied from `skills/rule-audit/evals/evals.json` (`skill_name`, `evals[]` with `id`, `name`, `prompt`, `expected_output`, `files`, `assertions[{text, type}]`).
- Produces: the negative-control fixture and 4 evals consumable by smart-skill-creator's `run_eval.py` harness.

- [ ] **Step 1: Write fixture B**

`well-delegated/SKILL.md`:

```markdown
---
name: release-note-advisor
description: Reviews release notes for tone and audience fit before publishing. Use when the user asks to review or polish release notes.
---

# Release Note Advisor

## Workflow

1. Run exactly: `python3 scripts/check.py notes/ --json` to lint structure
   (title heading present). Exit 0 clean, 1 findings, 2 usage error.
2. Read the findings JSON and decide which flagged items actually matter for
   this release's audience — a missing heading on an internal note may be fine.
3. Write a short, plainly-worded explanation for each item worth fixing, in
   the project's usual voice.
```

`well-delegated/scripts/check.py`:

```python
#!/usr/bin/env python3
"""check.py - Lint release-note structure: every note needs a title heading.

USAGE
    python3 scripts/check.py <notes-dir> [--json]

EXIT CODES
    0  Clean.
    1  Findings reported.
    2  Usage error / directory missing.
"""
import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="Lint release-note structure.")
    p.add_argument("notes_dir")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    d = Path(a.notes_dir)
    if not d.is_dir():
        print(f"error: not a directory: {d}", file=sys.stderr)
        return 2
    findings = [{"file": f.name, "problem": "missing title heading"}
                for f in sorted(d.glob("*.md"))
                if not f.read_text(encoding="utf-8").startswith("# ")]
    if a.json:
        print(json.dumps(findings))
    else:
        print("\n".join(f"{x['file']}: {x['problem']}" for x in findings) or "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
```

`well-delegated/notes/welcome.md`:

```markdown
# Welcome improvements

Streamlined the first-run experience and rewrote the welcome email.
```

- [ ] **Step 2: Verify fixture B's script is genuinely well-delegated**

Run: `python3 skills/delegating-to-scripts/evals/fixtures/well-delegated/scripts/check.py skills/delegating-to-scripts/evals/fixtures/well-delegated/notes --json`
Expected: `[]`, exit 0. Also run with `--help` (exit 0) and with no args (exit 2, stderr message).

Run: `python3 skills/delegating-to-scripts/scripts/inventory.py skills/delegating-to-scripts/evals/fixtures/well-delegated --out /tmp/wd.json && python3 -c "import json; d=json.load(open('/tmp/wd.json')); s=d['scripts'][0]; assert s['mentioned_in_body'] and s['has_argparse'] and s['has_docstring'] and s['help_ok'], s; print('already-delegated signals OK')"`
Expected: `already-delegated signals OK`.

- [ ] **Step 3: Write evals.json**

```json
{
  "skill_name": "delegating-to-scripts",
  "evals": [
    {
      "id": 0,
      "name": "classify-and-report",
      "prompt": "Review the skill in evals/fixtures/changelog-checker/ and tell me which of its workflow steps should be delegated to scripts. Don't change anything yet.",
      "expected_output": "Rendered classification table: steps 1/2/3/5 SCRIPT with concrete proposed interfaces, step 6 HYBRID, steps 4 and 7 CLAUDE (7 despite containing the word 'verify'). Nothing written into the fixture; flow stops at the gate or explicitly notes changes await user selection.",
      "files": ["evals/fixtures/changelog-checker"],
      "assertions": [
        {"text": "output contains a per-step table with SCRIPT/CLAUDE/HYBRID classes and proposed script interfaces for SCRIPT/HYBRID rows", "type": "structure"},
        {"text": "no new files or directories are created inside evals/fixtures/changelog-checker/", "type": "structure"},
        {"text": "step 2 (version-header check) is classified SCRIPT with a concrete argv/exit-code interface", "type": "content"},
        {"text": "step 6 (category tags + Misc re-homing) is classified HYBRID", "type": "content"},
        {"text": "step 7 (verify entries clearly written) is classified CLAUDE despite the 'verify' verb", "type": "content"},
        {"text": "step 4 (release narrative) is classified CLAUDE", "type": "content"}
      ]
    },
    {
      "id": 1,
      "name": "apply-and-smoke-test",
      "prompt": "Review the skill in evals/fixtures/changelog-checker/ for steps to delegate to scripts, apply all the delegations you find, and verify the generated scripts work.",
      "expected_output": "Scripts written into changelog-checker/scripts/ for steps 1/2/3/5 (and the mechanical half of 6), each with --help support. Manifest includes bad_data_invocations; the header-check script flags v1.2.0.md. SKILL.md rewritten only after smoke test passes; steps 4 and 7 stay prose; step 6 keeps its judgment sentence.",
      "files": ["evals/fixtures/changelog-checker"],
      "assertions": [
        {"text": "changelog-checker/scripts/ contains at least 3 Python scripts and each supports --help", "type": "structure"},
        {"text": "the rewritten SKILL.md invokes each generated script by exact command line", "type": "structure"},
        {"text": "a smoke-test PASS result is reported before the SKILL.md rewrite is shown", "type": "structure"},
        {"text": "the header-check script, run against changelogs/, flags v1.2.0.md and exits nonzero", "type": "content"},
        {"text": "step 4 (release narrative) remains a prose instruction with no script", "type": "content"},
        {"text": "step 6's judgment about re-homing Misc entries remains prose", "type": "content"}
      ]
    },
    {
      "id": 2,
      "name": "nothing-to-delegate",
      "prompt": "Which parts of the skill in evals/fixtures/well-delegated/ should be scripts?",
      "expected_output": "Report acknowledging scripts/check.py as already delegated (mentioned in body, argparse, working --help), classifying the remaining judgment steps CLAUDE, and recommending no new scripts.",
      "files": ["evals/fixtures/well-delegated"],
      "assertions": [
        {"text": "no new files are written into evals/fixtures/well-delegated/", "type": "structure"},
        {"text": "scripts/check.py is acknowledged as already delegated", "type": "content"},
        {"text": "the judgment steps (audience-fit decision, explanations) are classified CLAUDE, not forced into scripts", "type": "content"}
      ]
    },
    {
      "id": 3,
      "name": "partial-selection",
      "prompt": "Review evals/fixtures/changelog-checker/ for delegable steps, but apply only the delegations for steps 1 and 3. Leave everything else untouched.",
      "expected_output": "Exactly two scripts generated (file listing, category counting), both smoke-tested. Step 2's prose is byte-identical to before; the SKILL.md diff touches only steps 1 and 3.",
      "files": ["evals/fixtures/changelog-checker"],
      "assertions": [
        {"text": "exactly two generated scripts exist in changelog-checker/scripts/", "type": "structure"},
        {"text": "the SKILL.md rewrite touches only steps 1 and 3; step 2's text is unchanged", "type": "structure"},
        {"text": "both generated scripts pass the smoke test before the rewrite", "type": "content"}
      ]
    }
  ]
}
```

- [ ] **Step 4: Validate evals.json shape**

Run: `python3 -c "
import json
d = json.load(open('skills/delegating-to-scripts/evals/evals.json'))
assert d['skill_name'] == 'delegating-to-scripts'
for e in d['evals']:
    for k in ('id', 'name', 'prompt', 'expected_output', 'files', 'assertions'):
        assert k in e, (e.get('id'), k)
    for a in e['assertions']:
        assert a['type'] in ('structure', 'content')
    for f in e['files']:
        import pathlib; assert (pathlib.Path('skills/delegating-to-scripts') / f).exists(), f
print('evals.json OK,', len(d['evals']), 'evals')
"`
Expected: `evals.json OK, 4 evals`.

- [ ] **Step 5: Commit**

```bash
git add skills/delegating-to-scripts/evals
git commit -m "feat(delegating-to-scripts): well-delegated fixture + 4 evals"
```

---

### Task 8: End-to-end dry run + final verification

**Files:**
- Modify: none in the skill (fixes only if the dry run exposes defects).

**Interfaces:**
- Consumes: everything above.
- Produces: verified skill; pristine fixtures.

- [ ] **Step 1: Full test suite**

Run: `python3 -m pytest skills/delegating-to-scripts/tests/ -v`
Expected: 17 passed.

- [ ] **Step 2: Dry-run the report path on a fixture copy**

```bash
cp -r skills/delegating-to-scripts/evals/fixtures/changelog-checker /tmp/cc-dryrun
cd /tmp/cc-dryrun
mkdir -p .delegation-review
python3 /Users/admin/claude-learning/skills/delegating-to-scripts/scripts/inventory.py . --out .delegation-review/inventory.json
```

Expected: summary shows 7 steps, verbs hints on s1/s2/s3/s5/s6/s7. Then hand-write `.delegation-review/classification.json` per the Task 5 Step 3 classifications (s1/s2/s3/s5 SCRIPT, s6 HYBRID, s4/s7 CLAUDE) and run:

```bash
python3 /Users/admin/claude-learning/skills/delegating-to-scripts/scripts/render_report.py .delegation-review/classification.json .delegation-review/inventory.json
```

Expected: exit 0, table with 7 rows, verdict "5 of 7 steps are mechanical".

- [ ] **Step 3: Dry-run the smoke path with one real generated-style script**

In `/tmp/cc-dryrun`, write `scripts/check_headings.py` by hand (a ~30-line argparse script that checks each `changelogs/*.md` starts with `## v` + version pattern, prints findings JSON, exits 0 clean / 1 findings / 2 usage), plus a manifest with a good invocation against a copied-clean changelogs dir, a `bad_data_invocation` against the real `changelogs/` (expected: flags v1.2.0.md, contains `v1.2.0.md`), and a `bad_invocation` with no args. Run:

```bash
python3 /Users/admin/claude-learning/skills/delegating-to-scripts/scripts/smoke_test.py .delegation-review/manifest.json
```

Expected: all checks PASS, exit 0. This validates the manifest schema docs are followable end-to-end.

- [ ] **Step 4: Confirm pristine fixtures and clean tree**

```bash
rm -rf /tmp/cc-dryrun /tmp/ra.json /tmp/wd.json
git -C /Users/admin/claude-learning status --short skills/delegating-to-scripts
```

Expected: no unstaged changes; fixture A untouched (`git status` clean for `evals/fixtures/`).

- [ ] **Step 5: Final audit + commit any dry-run fixes**

Run: `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts`
Expected: no high findings. If the dry run exposed defects that required code changes, re-run the suite and commit:

```bash
git add skills/delegating-to-scripts
git commit -m "fix(delegating-to-scripts): dry-run fixes"
```

---

## Verification (whole feature)

1. `python3 -m pytest skills/delegating-to-scripts/tests/ -v` → 17 passed.
2. `python3 skills/skill-reviewer/scripts/audit.py skills/delegating-to-scripts` → no high findings.
3. Dry run (Task 8) proves inventory → classify → render → smoke on real files.
4. Skill listed: restart session or check the available-skills list shows `delegating-to-scripts` (a skill that isn't discovered doesn't exist).
5. Optional follow-up (not this plan): run the 4 evals via smart-skill-creator's harness.
