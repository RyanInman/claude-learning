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

    if not isinstance(inv.get("steps"), list):
        print("error: inventory has no 'steps' list", file=sys.stderr)
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
