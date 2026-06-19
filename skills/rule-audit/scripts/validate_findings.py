#!/usr/bin/env python3
"""Validate one review-subagent findings JSON against the Finding schema.

Each review subagent runs this on its own `batch-<N>.json` before returning to
the orchestrator: a malformed file is then caught while the subagent still has
the files and rule text in context to fix and rewrite it, instead of failing the
whole render later (where the orchestrator would have to re-dispatch the batch).
render_report.py imports `validate_finding` from here so subagent-side and
render-side checks never drift.

Usage: python3 validate_findings.py <batch-N.json>
Exit: 0 valid · 2 schema/parse error · 1 usage/IO.
"""

import json
import sys

LEVELS = {"HIGH", "MEDIUM", "LOW"}
REQUIRED = ("title", "rule_file", "rule_text", "issue", "impact", "risk",
            "code_snippet", "suggested_fix")


def validate_finding(src, file, i, fnd):
    where = f"{src}: finding #{i + 1} for {file}"
    if not isinstance(fnd, dict):
        return [f"{where}: not a JSON object"]
    errs = [f"{where}: missing '{k}'" for k in REQUIRED if not fnd.get(k)]
    for axis in ("impact", "risk"):
        v = fnd.get(axis)
        if v is not None and v not in LEVELS:
            errs.append(f"{where}: {axis}={v!r} not one of HIGH|MEDIUM|LOW")
    conf = fnd.get("confidence")
    if conf is None:
        errs.append(f"{where}: missing 'confidence' (integer 0-100)")
    elif isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 100:
        errs.append(f"{where}: confidence={conf!r} must be a number 0-100")
    return errs


def validate_file(path):
    """Return a list of error strings ([] == valid). Shared by render_report.py."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: cannot parse JSON ({e})"]
    if not isinstance(data, dict):
        return [f"{path}: top level must be a JSON object"]
    ffs = data.get("file_findings")
    if not isinstance(ffs, list):
        return [f"{path}: missing or non-list 'file_findings'"]
    errs = []
    for entry in ffs:
        if not isinstance(entry, dict) or "file" not in entry:
            errs.append(f"{path}: each file_findings entry needs a 'file' key")
            continue
        fnds = entry.get("findings", [])
        if not isinstance(fnds, list):
            errs.append(f"{path}: 'findings' for {entry.get('file')} must be a list")
            continue
        for i, fnd in enumerate(fnds):
            errs.extend(validate_finding(path, entry["file"], i, fnd))
    return errs


def main():
    if len(sys.argv) != 2:
        print("usage: validate_findings.py <batch-N.json>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    errs = validate_file(path)
    if errs:
        print("INVALID — fix and rewrite before returning:\n  - " + "\n  - ".join(errs),
              file=sys.stderr)
        sys.exit(2)
    print(f"OK: {path} valid")


if __name__ == "__main__":
    main()
