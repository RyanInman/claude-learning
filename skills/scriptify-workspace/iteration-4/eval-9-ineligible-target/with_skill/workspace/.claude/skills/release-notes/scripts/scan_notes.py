#!/usr/bin/env python3
"""
scan_notes.py - Inventory the merged-PR note files for one milestone.

Lists every `.md` file in the notes directory sorted by filename, checks that
each one opens with `PR #<number>:`, reads its `type:` field, and tallies the
entries per type. The JSON it emits is the single input render_notes.py
consumes, so the parsing happens once per run instead of once per step.

FINDING CODES
    first_line_not_pr_header  the first line does not match `PR #<number>:`
    missing_type_field        the file carries no `type:` line
    unknown_type              the `type:` value is outside feat/fix/chore

USAGE
    python3 scripts/scan_notes.py <notes-dir> [--out FILE]

    Without --out the full JSON goes to stdout. With --out the JSON goes to the
    file and stdout carries a compact summary that still names every finding
    code, so a caller can branch without opening the file.

EXIT CODES
    0  Every file is well formed.
    1  At least one finding.
    2  Usage error, missing directory, or an unreadable file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PR_HEADER = re.compile(r"^PR #(\d+):\s*(.*)$")
TYPE_FIELD = re.compile(r"^type:\s*(\S+)\s*$")
KNOWN_TYPES = ("feat", "fix", "chore")


def scan(notes_dir):
    """Return (payload, findings). Raises OSError on an unreadable file."""
    entries = []
    findings = []
    types = {t: 0 for t in KNOWN_TYPES}

    for path in sorted(notes_dir.glob("*.md"), key=lambda p: p.name):
        lines = path.read_text(encoding="utf-8").splitlines()
        first = lines[0] if lines else ""
        header = PR_HEADER.match(first)
        if header:
            pr, title = int(header.group(1)), header.group(2).strip()
        else:
            pr, title = None, ""
            findings.append({"code": "first_line_not_pr_header",
                             "file": path.name,
                             "detail": f"first line is {first!r}"})

        kind = None
        for line in lines:
            field = TYPE_FIELD.match(line)
            if field:
                kind = field.group(1)
                break
        if kind is None:
            findings.append({"code": "missing_type_field", "file": path.name,
                             "detail": "no `type:` line in the file"})
        elif kind not in KNOWN_TYPES:
            findings.append({"code": "unknown_type", "file": path.name,
                             "detail": f"type {kind!r} is not one of "
                                       + "/".join(KNOWN_TYPES)})
        else:
            types[kind] += 1

        entries.append({"file": path.name, "pr": pr, "title": title,
                        "type": kind})

    payload = {"notes_dir": notes_dir.as_posix(), "file_count": len(entries),
               "entries": entries, "types": types, "findings": findings}
    return payload, findings


def summarize(payload, out_path):
    types = payload["types"]
    lines = [f"scanned {payload['file_count']} file(s) in {payload['notes_dir']}",
             "types: " + " ".join(f"{t}={types[t]}" for t in KNOWN_TYPES)]
    findings = payload["findings"]
    if findings:
        lines.append(f"findings: {len(findings)}")
        lines += [f"  {f['code']}  {f['file']}  {f['detail']}" for f in findings]
    else:
        lines.append("findings: none")
    lines.append(f"wrote {out_path}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory milestone PR notes.")
    ap.add_argument("notes_dir", help="Directory holding the pr-*.md notes")
    ap.add_argument("--out", help="Write the JSON here; summarize on stdout")
    args = ap.parse_args(argv)

    notes_dir = Path(args.notes_dir)
    if not notes_dir.is_dir():
        print(f"scan_notes: not a directory: {notes_dir}", file=sys.stderr)
        return 2

    try:
        payload, findings = scan(notes_dir)
    except OSError as e:
        print(f"scan_notes: cannot read a note file: {e}", file=sys.stderr)
        return 2

    if args.out:
        out_path = Path(args.out)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2) + "\n",
                                encoding="utf-8")
        except OSError as e:
            print(f"scan_notes: cannot write {out_path}: {e}", file=sys.stderr)
            return 2
        print(summarize(payload, out_path.as_posix()))
    else:
        print(json.dumps(payload, indent=2))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
