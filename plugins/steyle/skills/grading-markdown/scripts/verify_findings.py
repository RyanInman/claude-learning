#!/usr/bin/env python3
"""
verify_findings.py - Check every finding in a findings.json against the target files.

READS   findings.json and each target file it names
WRITES  nothing

USAGE
    python3 scripts/verify_findings.py <findings.json>

findings.json shape (Claude writes it after the read in Step 3):
    {"target": "<file or folder path>", "scope": "file"|"folder",
     "target_class": "skill"|"memory"|"other",
     "findings": [{"file": "SKILL.md", "line": 21, "rule": "B1",
                   "quote": "<verbatim text>", "fix": "<rewrite>"}, ...]}
    "file" is relative to the target folder (folder scope) or to the target
    file's directory (file scope). Absolute paths also work. A file-wide
    finding sets "line": null and puts the finding text in "quote".

Checks, one code per condition:
    missing_field          file, rule, or fix absent; quote absent on a line finding
    file_not_found         the named file does not exist
    line_out_of_range      line is below 1 or past the last line
    quote_not_at_line      quote exists in the file but not within lines n..n+2
    quote_not_in_file      quote appears nowhere in the file (fabrication signal)
    line_in_frontmatter    line sits inside the leading --- block (covers the description)
    line_in_code_block     line sits inside a fenced code block
    line_in_blockquote     line starts with ">", quoted text
    line_in_example        skill target only: line sits under an "Example(s)" heading

Not checked: the memory guide's two-emphasized-rules allowance. Count those by hand.
Quote matching folds whitespace runs and curly quotes to straight quotes, and treats
"..." or an ellipsis as elision.

EXIT CODES
    0  Every finding verified (JSON summary on stdout).
    1  Failures (JSON with per-finding codes on stdout).
    2  Usage error, unreadable or malformed findings.json.
    3  Unexpected failure.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SAME_MARK = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
                           "‘": "'", "’": "'", "‚": "'"})
ELLIPSIS = re.compile(r"…|\.\.\.")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
EXAMPLE_HEADING = re.compile(r"Examples?\b", re.IGNORECASE)
QUOTE_WINDOW = 3  # a quoted sentence can wrap onto the two lines after its anchor
REQUIRED = ("file", "rule", "fix")


def normalize(text):
    return re.sub(r"\s+", " ", text.translate(SAME_MARK)).strip()


def fragments(quote):
    return [normalize(f) for f in ELLIPSIS.split(quote) if normalize(f)]


def zones(lines, skill_mode):
    """Return a per-line zone label: None, frontmatter, code_block, blockquote, example."""
    zone = [None] * len(lines)
    in_fm = False
    if lines and lines[0].strip() == "---":
        in_fm = True
        zone[0] = "frontmatter"
        for i in range(1, len(lines)):
            zone[i] = "frontmatter"
            if lines[i].strip() == "---":
                in_fm = False
                break
    in_code = False
    example_level = None
    for i, ln in enumerate(lines):
        if zone[i] == "frontmatter":
            continue
        if ln.strip().startswith("```"):
            in_code = not in_code
            zone[i] = "code_block"
            continue
        if in_code:
            zone[i] = "code_block"
            continue
        h = HEADING.match(ln)
        if h:
            level = len(h.group(1))
            if example_level is not None and level <= example_level:
                example_level = None
            if skill_mode and EXAMPLE_HEADING.match(h.group(2)):
                example_level = level
        if example_level is not None:
            zone[i] = "example"
        elif ln.lstrip().startswith(">"):
            zone[i] = "blockquote"
    return zone


def resolve_file(target, scope, name):
    p = Path(name).expanduser()
    if p.is_absolute():
        return p
    base = target if scope == "folder" else target.parent
    return (base / p).resolve()


def check(finding, target, scope, skill_mode, cache):
    codes = [f"missing_field:{k}" for k in REQUIRED if not finding.get(k)]
    line = finding.get("line")
    if line is not None and not finding.get("quote"):
        codes.append("missing_field:quote")
    if codes:
        return codes
    path = resolve_file(target, scope, finding["file"])
    if path not in cache:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ["file_not_found"]
        lines = text.splitlines()
        cache[path] = (lines, zones(lines, skill_mode), normalize(text))
    lines, zone, norm_text = cache[path]
    if line is None:
        return []
    if not isinstance(line, int) or line < 1 or line > len(lines):
        return ["line_out_of_range"]
    z = zone[line - 1]
    if z:
        codes.append(f"line_in_{z}")
    frags = fragments(finding["quote"])
    window = normalize(" ".join(lines[line - 1:line - 1 + QUOTE_WINDOW]))
    if not all(f in window for f in frags):
        if all(f in norm_text for f in frags):
            codes.append("quote_not_at_line")
        else:
            codes.append("quote_not_in_file")
    return codes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("findings", help="findings.json written after the Step 3 read")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.findings).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"error: cannot load {args.findings}: {e}", file=sys.stderr)
        return 2
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list) or "target" not in data:
        print("error: findings.json needs 'target' and a 'findings' list", file=sys.stderr)
        return 2
    target = Path(data["target"]).expanduser().resolve()
    scope = data.get("scope") or ("folder" if target.is_dir() else "file")
    skill_mode = data.get("target_class") == "skill"

    cache, failures = {}, []
    for i, f in enumerate(data["findings"]):
        codes = check(f if isinstance(f, dict) else {}, target, scope, skill_mode, cache)
        if codes:
            failures.append({"index": i, "file": f.get("file") if isinstance(f, dict) else None,
                             "line": f.get("line") if isinstance(f, dict) else None, "codes": codes})
    result = {"checked": len(data["findings"]), "verified": len(data["findings"]) - len(failures),
              "failures": failures}
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # predictable errors already returned 2 above
        print(f"unexpected failure: {e}", file=sys.stderr)
        sys.exit(3)
