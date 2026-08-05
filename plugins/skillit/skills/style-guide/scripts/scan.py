#!/usr/bin/env python3
"""
scan.py - Flags literal hits for the style guide's closed-vocabulary rules.

Checks SKILL.md and each reference file for three rules a fixed pattern can
catch: Rule 3 ("and then" compound steps), Rule 6 (the vague-delegation word
list), and Rule 9 (ALL-CAPS MUST/NEVER/ALWAYS). It skips the frontmatter
description (Rule 11 exempt zone) and any Example section (Rule 12 exempt
zone) on its own, and it skips fenced code blocks too.

Each hit is a candidate, not a confirmed violation. Read the flagged line
before you report it, because a quoted bad example inside prose (not inside
an Example section) still needs a human read to place correctly. Rules 2
(passive voice), 5 (synonym drift), and 8 (stacked clauses) need judgment
this script cannot supply, so they stay out of scope here.

USAGE
    python scan.py <path-to-skill-folder> [--json]

    <path-to-skill-folder>  Folder that contains SKILL.md.
    --json                  Print hits as JSON to stdout. Diagnostics still
                            go to stderr.

EXIT CODES
    0  No hits.
    1  One or more hits found.
    2  Usage error, or the folder has no SKILL.md.

All input comes from argv. The script never prompts.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Rule 6's word list, taken from the guide's pre-ship checklist plus "deal
# with" from the rule's own text. "some" is left out on purpose: it is too
# common in ordinary prose, and matching it would flood the report with
# false positives. Treat Rule 6's "some" case as a manual read, not a scan.
RULE_6_PATTERNS = {
    "handle/process": re.compile(r"\b(?:handles?|handling|handled|process(?:es|ing|ed)?)\b", re.IGNORECASE),
    "deal with": re.compile(r"\bdeal(?:s|t)?\s+with\b", re.IGNORECASE),
    "appropriately": re.compile(r"\bappropriately\b", re.IGNORECASE),
    "as needed": re.compile(r"\bas needed\b", re.IGNORECASE),
    "various": re.compile(r"\bvarious\b", re.IGNORECASE),
    "etc.": re.compile(r"\betc\."),
}

# Case-sensitive on purpose: Rule 9 bans the ALL-CAPS form. Lowercase "must"
# is normal, approved obligation phrasing and must not fire here.
RULE_9_PATTERN = re.compile(r"\b(MUST|NEVER|ALWAYS)\b")

RULE_3_PATTERN = re.compile(r"\band then\b", re.IGNORECASE)


def frontmatter_line_count(text):
    """Return the line count of a leading YAML frontmatter block (both ---
    fences plus everything between), or 0 if the text has none."""
    if not text.startswith("---"):
        return 0
    m = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    return m.group(0).count("\n") if m else 0


def strip_exempt_zones(text, skip_lines=0):
    """Return [(line_no, line_text), ...] with the first `skip_lines` lines
    (frontmatter), fenced code blocks, and any Example section removed. Line
    numbers stay 1-indexed against the original file, matching what an editor
    or the Read tool shows."""
    kept = []
    in_code_fence = False
    example_depth = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if lineno <= skip_lines:
            continue
        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            if example_depth is not None and level <= example_depth:
                example_depth = None
            if re.match(r"Examples?\b", heading.group(2), re.IGNORECASE):
                example_depth = level
                continue
        if example_depth is not None:
            continue
        kept.append((lineno, line))
    return kept


def scan_lines(lines):
    """Return a list of hit dicts (rule, detail, line, text) for one file's
    already-filtered (line_no, line_text) pairs."""
    hits = []
    for lineno, line in lines:
        for match in RULE_3_PATTERN.finditer(line):
            hits.append({"rule": "Rule 3", "detail": match.group(0), "line": lineno, "text": line.strip()})
        for label, pattern in RULE_6_PATTERNS.items():
            for match in pattern.finditer(line):
                hits.append({"rule": "Rule 6", "detail": label, "line": lineno, "text": line.strip()})
        for match in RULE_9_PATTERN.finditer(line):
            hits.append({"rule": "Rule 9", "detail": match.group(0), "line": lineno, "text": line.strip()})
    return hits


def collect_files(skill_dir):
    """Return [(display_path, Path), ...] for SKILL.md plus every reference
    file, in scan order."""
    files = [("SKILL.md", skill_dir / "SKILL.md")]
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.rglob("*.md")):
            files.append((str(ref.relative_to(skill_dir)), ref))
    return files


def render_report(hits):
    if not hits:
        return ("No Rule 3/6/9 hits. Rules 2, 5, and 8 still need a manual "
                "read; a scan cannot judge them.")
    lines = [f"SCAN  ::  {len(hits)} hit(s)", ""]
    for h in sorted(hits, key=lambda h: (h["file"], h["line"])):
        lines.append(f"  [{h['rule']}] {h['file']}:{h['line']}  ({h['detail']})")
        lines.append(f"      {h['text']}")
    lines.append("")
    lines.append("Each hit above is a candidate. Confirm it sits inside real")
    lines.append("instructional prose before you count it against the grade.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flag literal Rule 3/6/9 hits in a skill's prose.")
    parser.add_argument("skill_path", help="Folder that contains SKILL.md")
    parser.add_argument("--json", action="store_true", help="Print hits as JSON")
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_path)
    if skill_dir.is_file() and skill_dir.name == "SKILL.md":
        skill_dir = skill_dir.parent
    if not skill_dir.is_dir():
        print(f"error: not a directory: {skill_dir}", file=sys.stderr)
        return 2
    if not (skill_dir / "SKILL.md").exists():
        print(f"error: no SKILL.md in {skill_dir}", file=sys.stderr)
        return 2

    all_hits = []
    for label, path in collect_files(skill_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"warning: could not read {label}: {e}", file=sys.stderr)
            continue
        skip = frontmatter_line_count(text) if label == "SKILL.md" else 0
        for hit in scan_lines(strip_exempt_zones(text, skip_lines=skip)):
            hit["file"] = label
            all_hits.append(hit)

    if args.json:
        print(json.dumps(all_hits, indent=2))
    else:
        print(render_report(all_hits))

    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main())
