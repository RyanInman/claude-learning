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
