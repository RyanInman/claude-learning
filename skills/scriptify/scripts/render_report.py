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
     "class": "SCRIPT",            // SCRIPT | VALIDATOR | HYBRID | HOOK | CLAUDE | DEAD | ALREADY_DELEGATED
     "why": "same regex check every run",
     "proposed_script": {          // REQUIRED for SCRIPT/VALIDATOR/HYBRID, optional for HOOK, null otherwise
       "name": "check_headings.py",
       "interface": "python3 scripts/check_headings.py changelogs/ --json",
       "stdout": "findings JSON",
       "exit": "0 clean / 1 findings / 2 usage",
       "touches": "reads changelogs/*.md, writes nothing"},   // required, rendered in Security
     "proposed_hook": null},       // REQUIRED for HOOK, null otherwise
    {"id": "s9", "class": "HOOK", "why": "must hold on every run, prose cannot enforce itself",
     "proposed_script": null,
     "proposed_hook": {
       "event": "PreToolUse",
       "matcher": "Bash",
       "command": "python3 scripts/block_push_main.py",
       "scope": "project settings",
       "false_positive_cost": "blocks a deliberate push to main during a hotfix"}}
  ]
}

USAGE
    python3 scripts/render_report.py <classification.json> <inventory.json> [--out FILE]

EXIT CODES
    0  Report rendered.
    1  Classification invalid; every problem named on stderr.
    2  Usage error / unreadable or unparseable input file / --out unwritable.
"""

import argparse
import json
import sys
from pathlib import Path

CLASSES = {"SCRIPT", "VALIDATOR", "HYBRID", "HOOK", "CLAUDE", "DEAD", "ALREADY_DELEGATED"}
NEEDS_SCRIPT = {"SCRIPT", "VALIDATOR", "HYBRID"}
# A SCRIPT or VALIDATOR step becomes one command line; a HYBRID keeps its judgment prose.
PURE = {"SCRIPT", "VALIDATOR"}
NO_TOOL_EVENTS = {"Stop", "SessionStart", "UserPromptSubmit"}
HOOK_FIELDS = ("event", "matcher", "command", "scope", "false_positive_cost")


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
        # A HOOK carries a proposed_script only when its command is a new
        # script; when it does, the script needs the same full interface.
        if klass in NEEDS_SCRIPT or (klass == "HOOK" and ps):
            missing = [k for k in ("name", "interface", "stdout", "exit", "touches")
                       if not (ps or {}).get(k)]
            if missing:
                errors.append(f"{where}: class {klass} requires proposed_script "
                              f"with fields {missing}")
        elif ps and klass != "HOOK":
            errors.append(f"{where}: class {klass} must not carry a proposed_script")
        ph = st.get("proposed_hook")
        if klass == "HOOK":
            # Stop, SessionStart, and UserPromptSubmit match no tool, so an
            # empty matcher is the honest value there.
            no_tool = (ph or {}).get("event") in NO_TOOL_EVENTS
            missing = [k for k in HOOK_FIELDS
                       if not str((ph or {}).get(k) or "").strip()
                       and not (k == "matcher" and no_tool)]
            if missing:
                errors.append(f"{where}: class HOOK requires proposed_hook "
                              f"with fields {missing}")
        elif ph:
            errors.append(f"{where}: class {klass} must not carry a proposed_hook")
    unclassified = sorted(inv_ids - seen)
    if unclassified:
        errors.append(f"unclassified inventory steps: {unclassified}")
    errors.extend(_shared_name_errors(cls))
    return errors


def _shared_name_errors(cls):
    """One script name, one exit-code contract.

    Two steps that share a proposed_script name are one script, so disagreeing
    'exit' strings ship an ambiguous branch into the rewritten SKILL.md: Step 8
    keys branching off exit codes, and a caller cannot tell 'no sources found'
    from 'thin sources present' when both are exit 1.
    """
    by_name = {}
    for st in cls.get("steps", []):
        ps = st.get("proposed_script") or {}
        name, exit_spec = ps.get("name"), ps.get("exit")
        if name and exit_spec:
            by_name.setdefault(name, {}).setdefault(exit_spec, []).append(st.get("id"))
    errors = []
    for name, contracts in sorted(by_name.items()):
        if len(contracts) > 1:
            detail = "; ".join(f"{sorted(ids)} say {spec!r}"
                               for spec, ids in sorted(contracts.items()))
            errors.append(f"script {name!r}: steps disagree on the exit "
                          f"contract: {detail}")
    return errors


def render(cls, inv):
    by_id = {s["id"]: s for s in cls["steps"]}
    mech = [s for s in inv["steps"] if by_id[s["id"]]["class"] in NEEDS_SCRIPT]
    # Count only SCRIPT and VALIDATOR. Step 8 replaces those with one command line, but a
    # HYBRID step keeps its judgment prose and only gains an invocation, so counting HYBRID
    # here advertises a saving the rewrite never delivers.
    full = [s for s in inv["steps"] if by_id[s["id"]]["class"] in PURE]
    hyb = len(mech) - len(full)
    hooks = [s for s in inv["steps"] if by_id[s["id"]]["class"] == "HOOK"]
    tok = sum(s["approx_tokens"] for s in full)
    name = inv.get("frontmatter", {}).get("name") or inv.get("target", "?")
    hyb_note = f", plus {hyb} HYBRID step(s) that keep their judgment prose" if hyb else ""
    out = [
        f"## Delegation review: {name}",
        "",
        f"**Verdict:** {len(full)} of {len(inv['steps'])} steps become pure script "
        f"invocations{hyb_note}. Replacing the {len(full)} SCRIPT step(s) removes ~{tok} tokens "
        f"of per-run reasoning."
        + (f" {len(hooks)} step(s) become hooks." if hooks else ""),
        "",
        "| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |",
        "|---|-------------|--------------|--------|-------|-----|---------------------------|",
    ]
    for s in inv["steps"]:
        c = by_id[s["id"]]
        ps = c.get("proposed_script")
        ph = c.get("proposed_hook")
        if ps:
            iface = f"`{ps['interface']}` -> {ps['stdout']}, exit {ps['exit']}"
        elif ph:
            iface = (f"{ph['event']} on `{ph['matcher']}`: `{ph['command']}`"
                     if ph.get('matcher') else f"{ph['event']}: `{ph['command']}`")
        else:
            iface = "-"
        out.append(f"| {s['id']} | \"{s['snippet']}\" (L{s['line_start']}-{s['line_end']}) "
                   f"| {s['origin']} | {s['approx_tokens']} | {c['class']} "
                   f"| {c['why']} | {iface} |")
    if hooks:
        out += ["", "### Hooks", "",
                "| Step | Event | Matcher | Command | Scope | False-positive cost |",
                "|------|-------|---------|---------|-------|---------------------|"]
        for s in hooks:
            h = by_id[s["id"]]["proposed_hook"]
            out.append(f"| {s['id']} | {h['event']} | `{h['matcher']}` | `{h['command']}` "
                       f"| {h['scope']} | {h['false_positive_cost']} |")
    unref = [sc["path"] for sc in inv.get("scripts", []) if not sc.get("mentioned_in_body")]
    if unref:
        out += ["", "### Existing scripts neither the body nor a reference invokes (wire or delete)", ""]
        out += [f"- `{path}`" for path in unref]
    names = {}
    for c in cls["steps"]:
        ps = c.get("proposed_script")
        if ps and ps.get("name") not in names:
            names[ps["name"]] = ps.get("touches") or "not stated"
    if names:
        out += ["", "### Security", "",
                "Every new script runs with the user's permissions. Files each one touches:", ""]
        out += [f"- `{n}`: {t}" for n, t in names.items()]
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
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(report, encoding="utf-8")
        except OSError as e:
            print(f"error: cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"report written to {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
