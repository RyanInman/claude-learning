#!/usr/bin/env python3
"""Validate a skill folder against create-2's structural rules.

Usage: python3 validate_skill.py <skill-folder> [--json] [--evals]

Checks frontmatter constraints, line budgets, vague instruction verbs,
ALL-CAPS directives, @ imports, backslash paths, and reference nesting.
Pass --evals to also require evals/evals.json; it is not checked by default.
Exit codes: 0 = pass (warnings allowed), 1 = failures found, 2 = bad input.
"""

import json
import re
import sys
from pathlib import Path

VAGUE_WORDS = re.compile(r"\b(handle|appropriately|as needed|various|etc\.?)\b", re.I)
QUOTED_SPAN = re.compile(r"`[^`]*`|\"[^\"]*\"")
CAPS_DIRECTIVE = re.compile(r"\b(MUST|NEVER|ALWAYS)\b")
AND_THEN = re.compile(r"\band then\b", re.I)
IMPERATIVE_HINT = re.compile(r"^\s*(?:\d+\.|[-*])\s+[A-Z]")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, text[end + 4:]


def check(skill_dir, check_evals=False):
    findings = []  # (level, file, message)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [("FAIL", "SKILL.md", "file missing - a skill folder requires SKILL.md")]

    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if fm is None:
        findings.append(("FAIL", "SKILL.md", "no YAML frontmatter block found"))
    else:
        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not name:
            findings.append(("FAIL", "SKILL.md", "frontmatter missing 'name'"))
        else:
            if len(name) > 64:
                findings.append(("FAIL", "SKILL.md", f"name is {len(name)} chars; limit is 64"))
            if not re.fullmatch(r"[a-z0-9-]+", name):
                findings.append(("FAIL", "SKILL.md", "name must use only lowercase letters, numbers, hyphens"))
            if "anthropic" in name or "claude" in name:
                findings.append(("FAIL", "SKILL.md", "name must not contain 'anthropic' or 'claude'"))
        if not desc:
            findings.append(("FAIL", "SKILL.md", "frontmatter missing 'description' - the skill can never trigger without it"))
        else:
            if len(desc) > 1024:
                findings.append(("FAIL", "SKILL.md", f"description is {len(desc)} chars; spec limit is 1024"))
            if len(desc) < 60:
                findings.append(("WARN", "SKILL.md", "description under 60 chars - likely too thin to route reliably"))
            if not re.search(r"\b(use|when|whenever)\b", desc, re.I):
                findings.append(("WARN", "SKILL.md", "description has no 'when to use' language - triggering may be weak"))

    body_lines = body.splitlines()
    n = len(body_lines)
    if n > 500:
        findings.append(("FAIL", "SKILL.md", f"body is {n} lines; 500 is the ceiling - split to references/"))
    elif n > 200:
        findings.append(("WARN", "SKILL.md", f"body is {n} lines; target is under 200 - consider splitting to references/"))

    md_files = [skill_md] + sorted(skill_dir.glob("references/*.md"))
    for f in md_files:
        rel = str(f.relative_to(skill_dir))
        lines = f.read_text(encoding="utf-8").splitlines()
        in_code = False
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            # Quoted and backticked spans are mentions, not instructions.
            line = QUOTED_SPAN.sub("", line)
            if re.match(r"^@[\w./-]+", line.strip()):
                findings.append(("FAIL", rel, f"line {i}: @ import - not supported in skills; write a Read pointer instead"))
            if "\\" in line and re.search(r"\w\\\w", line):
                findings.append(("WARN", rel, f"line {i}: backslash path - use forward slashes"))
            for m in CAPS_DIRECTIVE.finditer(line):
                findings.append(("WARN", rel, f"line {i}: ALL-CAPS '{m.group()}' - reframe as rule + reason"))
            if IMPERATIVE_HINT.match(line) or line.strip().startswith(("Run", "Read", "Write")):
                for m in VAGUE_WORDS.finditer(line):
                    findings.append(("WARN", rel, f"line {i}: vague word '{m.group()}' in an instruction - name the specific action"))
            if AND_THEN.search(line):
                findings.append(("WARN", rel, f"line {i}: 'and then' chain - split into separate sentences"))
        if f != skill_md and len(lines) > 100:
            head = "\n".join(lines[:15]).lower()
            if "contents" not in head and "## contents" not in head:
                findings.append(("WARN", rel, f"{len(lines)} lines with no table of contents in the first 15 lines"))
        if f != skill_md:
            joined = QUOTED_SPAN.sub("", "\n".join(lines))
            if re.search(r"references/[\w-]+\.md", joined):
                findings.append(("WARN", rel, "reference points at another reference - keep references one level deep"))

    if check_evals:
        evals = skill_dir / "evals" / "evals.json"
        if not evals.exists():
            findings.append(("WARN", "evals/evals.json", "missing - write eval prompts and baseline before shipping"))
        else:
            try:
                data = json.loads(evals.read_text(encoding="utf-8"))
                if len(data.get("evals", [])) < 3:
                    findings.append(("WARN", "evals/evals.json", "fewer than 3 eval prompts"))
            except json.JSONDecodeError as e:
                findings.append(("FAIL", "evals/evals.json", f"invalid JSON: {e}"))

    return findings


def main():
    args = [a for a in sys.argv[1:] if a not in ("--json", "--evals")]
    as_json = "--json" in sys.argv
    check_evals = "--evals" in sys.argv
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0 if args and args[0] in ("-h", "--help") else 2)
    skill_dir = Path(args[0])
    if not skill_dir.is_dir():
        print(f"Not a directory: {skill_dir}", file=sys.stderr)
        sys.exit(2)

    findings = check(skill_dir, check_evals)
    fails = [f for f in findings if f[0] == "FAIL"]
    if as_json:
        print(json.dumps([{"level": l, "file": f, "message": m} for l, f, m in findings], indent=2))
    else:
        for level, f, m in findings:
            print(f"{level}  {f}: {m}")
        print(f"\n{len(fails)} failure(s), {len(findings) - len(fails)} warning(s)")
        if not findings:
            print("Validation passed: no findings")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
