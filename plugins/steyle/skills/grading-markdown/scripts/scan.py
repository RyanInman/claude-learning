#!/usr/bin/env python3
"""
scan.py - Flags literal hits for the writing guides' closed-vocabulary rules.

Checks one markdown file, or a whole skill folder, for the three universal
rules a fixed pattern can catch: C1 ("and then" compound steps), D2 (the
vague-delegation word list), and D3 (ALL-CAPS MUST/NEVER/ALWAYS). It skips
fenced code blocks and leading YAML frontmatter in every target. In a skill
target it also skips any Example section, because the skill guide exempts
Zone 2. A plain document keeps its examples in scope, because the universal
guide grants no such exemption.

Each hit is a candidate, not a confirmed violation. Read the flagged line
before you report it, because a quoted bad example inside prose still needs a
human read to place correctly. Rules A1 (synonym drift), B1 (passive voice),
and B4 (stacked clauses) need judgment this script cannot supply, so they stay
out of scope here.

USAGE
    python scan.py <target> [--json]

    <target>  One markdown file, or a folder that contains SKILL.md. A file
              path scans that one file, a SKILL.md included. A folder path
              scans SKILL.md plus every markdown file under references/.
    --json    Print hits as JSON to stdout. Diagnostics still go to stderr.

EXIT CODES
    0  No hits.
    1  One or more hits found.
    2  Usage error: the target is missing, is not markdown, or is a folder
       with no SKILL.md.

All input comes from argv. The script never prompts.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# D2's word list, taken from the universal checklist plus "deal with" from the
# rule's own text. "some" is left out on purpose: it is too common in ordinary
# prose, and matching it would flood the report with false positives. Treat
# D2's "some" case as a manual read, not a scan.
D2_PATTERNS = {
    "handle/process": re.compile(r"\b(?:handles?|handling|handled|process(?:es|ing|ed)?)\b", re.IGNORECASE),
    "deal with": re.compile(r"\bdeal(?:s|t)?\s+with\b", re.IGNORECASE),
    "appropriately": re.compile(r"\bappropriately\b", re.IGNORECASE),
    "as needed": re.compile(r"\bas needed\b", re.IGNORECASE),
    "various": re.compile(r"\bvarious\b", re.IGNORECASE),
    "etc.": re.compile(r"\betc\."),
}

# Case-sensitive on purpose: D3 bans the ALL-CAPS form. Lowercase "must" is
# normal, approved obligation phrasing and must not fire here.
D3_PATTERN = re.compile(r"\b(MUST|NEVER|ALWAYS)\b")

C1_PATTERN = re.compile(r"\band then\b", re.IGNORECASE)


class TargetError(Exception):
    """Raised when the target is not a markdown file or a skill folder."""


def frontmatter_line_count(text):
    """Return the line count of a leading YAML frontmatter block (both ---
    fences plus everything between), or 0 if the text has none."""
    if not text.startswith("---"):
        return 0
    m = re.match(r"^---\n.*?\n---\n?", text, re.DOTALL)
    return m.group(0).count("\n") if m else 0


def strip_exempt_zones(text, skip_lines=0, skip_examples=True):
    """Return [(line_no, line_text), ...] with the first `skip_lines` lines
    (frontmatter) and fenced code blocks removed. With `skip_examples`, any
    Example section goes too. Line numbers stay 1-indexed against the original
    file, matching what an editor or the Read tool shows."""
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
            if skip_examples and re.match(r"Examples?\b", heading.group(2), re.IGNORECASE):
                example_depth = level
                continue
        if example_depth is not None:
            continue
        kept.append((lineno, line))
    return kept


def scan_lines(lines):
    """Return a list of hit dicts (rule, detail, line, text, count) for one
    file's already-filtered (line_no, line_text) pairs. Repeats of one pattern
    on one line collapse into a single hit with a count, so the report never
    prints the same line twice."""
    hits = []
    for lineno, line in lines:
        def add(rule, detail, count):
            hits.append({"rule": rule, "detail": detail, "line": lineno,
                         "text": line.strip(), "count": count})
        for detail, count in Counter(C1_PATTERN.findall(line)).items():
            add("C1", detail, count)
        for label, pattern in D2_PATTERNS.items():
            count = len(pattern.findall(line))
            if count:
                add("D2", label, count)
        for detail, count in Counter(D3_PATTERN.findall(line)).items():
            add("D3", detail, count)
    return hits


def is_skill_file(path):
    """Return True when the file belongs to a skill folder. The skill guide's
    Zone 2 exemption covers a SKILL.md, any file beside it, and a reference
    file one level below it."""
    if path.name == "SKILL.md":
        return True
    if (path.parent / "SKILL.md").is_file():
        return True
    return path.parent.name == "references" and (path.parent.parent / "SKILL.md").is_file()


def resolve_target(target):
    """Return [(display_path, Path, skill_mode), ...] in scan order. A file
    path yields that one file. A folder path yields SKILL.md plus every
    markdown file under references/."""
    if target.is_file():
        if target.suffix.lower() != ".md":
            raise TargetError(f"not a markdown file: {target}")
        return [(target.name, target, is_skill_file(target))]
    if target.is_dir():
        skill_md = target / "SKILL.md"
        if not skill_md.is_file():
            raise TargetError(f"no SKILL.md in {target}")
        files = [("SKILL.md", skill_md, True)]
        refs_dir = target / "references"
        if refs_dir.is_dir():
            for ref in sorted(refs_dir.rglob("*.md")):
                files.append((str(ref.relative_to(target)), ref, True))
        return files
    raise TargetError(f"no such file or folder: {target}")


def render_report(hits):
    if not hits:
        return ("No C1/D2/D3 hits. Rules A1, B1, and B4 still need a manual "
                "read; a scan cannot judge them.")
    total = sum(h["count"] for h in hits)
    lines = [f"SCAN  ::  {total} hit(s)", ""]
    for h in sorted(hits, key=lambda h: (h["file"], h["line"])):
        times = f" x{h['count']}" if h["count"] > 1 else ""
        lines.append(f"  [{h['rule']}] {h['file']}:{h['line']}  ({h['detail']}{times})")
        lines.append(f"      {h['text']}")
    lines.append("")
    lines.append("Each hit above is a candidate. Confirm it sits inside real")
    lines.append("instructional prose before you count it against the grade.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flag literal C1/D2/D3 hits in markdown prose.")
    parser.add_argument("target",
                        help="A markdown file, or a folder that contains SKILL.md")
    parser.add_argument("--json", action="store_true", help="Print hits as JSON")
    args = parser.parse_args(argv)

    try:
        files = resolve_target(Path(args.target))
    except TargetError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    all_hits = []
    for label, path, skill_mode in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"warning: could not read {label}: {e}", file=sys.stderr)
            continue
        lines = strip_exempt_zones(text,
                                   skip_lines=frontmatter_line_count(text),
                                   skip_examples=skill_mode)
        for hit in scan_lines(lines):
            hit["file"] = label
            all_hits.append(hit)

    if args.json:
        print(json.dumps(all_hits, indent=2))
    else:
        print(render_report(all_hits))

    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main())
