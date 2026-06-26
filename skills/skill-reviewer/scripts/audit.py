#!/usr/bin/env python3
"""
audit.py - Deterministic checks for a SKILL.md skill folder.

Runs every check that can be measured mechanically (frontmatter validity,
body size, anti-pattern detection, reference-file structure) so the reviewing
agent can spend its attention on judgment instead of counting lines.

USAGE
    python scripts/audit.py <path-to-skill-folder> [--json]

    <path-to-skill-folder>  Folder containing SKILL.md (not the SKILL.md file
                            itself). If you pass the SKILL.md file, its parent
                            is used.
    --json                  Emit findings as JSON to stdout instead of the
                            human-readable report. Diagnostics still go to
                            stderr.

EXIT CODES
    0  No findings (clean) OR only informational notes.
    1  One or more high/medium/low findings were reported.
    2  Usage error or the skill could not be read (no SKILL.md, bad YAML).

All input is taken from argv; the script never prompts. Findings are a flat
list so they are easy to fold into a written review. Severity is the script's
best mechanical guess -- the agent re-triages by real-world impact afterward.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Mirror of the packager/validator's allowed frontmatter keys. Anything else
# fails on upload, so it is a hard (high) finding here too.
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}

# Caps-lock directive words we count to detect "the shouting file" anti-pattern.
CAPS_DIRECTIVES = ["MUST", "ALWAYS", "NEVER", "DO NOT", "DON'T", "SHOULD NOT", "REQUIRED", "MANDATORY"]


def _add(findings, severity, category, message, suggestion, location="SKILL.md"):
    findings.append({
        "severity": severity,       # high | medium | low | info
        "category": category,
        "message": message,
        "suggestion": suggestion,
        "location": location,
    })


def _split_frontmatter(text):
    """Return (frontmatter_dict_or_None, body_str, error_or_None)."""
    if not text.startswith("---"):
        return None, text, "no YAML frontmatter (file does not start with '---')"
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, text, "frontmatter present but not closed with a '---' line"
    fm_text, body = m.group(1), m.group(2)
    try:
        import yaml  # stdlib-free path below if PyYAML is absent
        fm = yaml.safe_load(fm_text)
    except ImportError:
        fm = _naive_yaml(fm_text)
    except Exception as e:  # noqa: BLE001 - report any YAML parse problem
        return None, body, f"frontmatter is not valid YAML: {e}"
    if not isinstance(fm, dict):
        return None, body, "frontmatter is not a YAML mapping"
    return fm, body, None


def _naive_yaml(fm_text):
    """Tiny fallback parser for `key: value` frontmatter when PyYAML is absent.
    Handles the flat string fields this audit cares about (name, description)."""
    out = {}
    key = None
    for line in fm_text.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # A bare block-scalar indicator (>, |, >-, |-, >+, |+) is not the
            # value -- the value is the indented lines that follow. Without this
            # the indicator leaks into the field (e.g. a '>-' folded description
            # falsely trips the angle-bracket check).
            if re.fullmatch(r"[>|][+-]?", val):
                val = ""
            out[key] = val
        elif key and line.strip():  # continuation of a folded value
            out[key] = (str(out.get(key, "")) + " " + line.strip()).strip()
    return out


def check_frontmatter(fm, findings):
    keys = set(fm.keys())
    unexpected = keys - ALLOWED_KEYS
    if unexpected:
        _add(findings, "high", "frontmatter",
             f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}. "
             f"These cause the skill to be rejected on upload.",
             f"Remove them. Allowed keys: {', '.join(sorted(ALLOWED_KEYS))}.")

    # name
    name = fm.get("name")
    if not name or not str(name).strip():
        _add(findings, "high", "frontmatter", "Missing 'name'.",
             "Add a kebab-case name. Gerund form is recommended (e.g. reviewing-skills).")
    else:
        name = str(name).strip()
        if not re.match(r"^[a-z0-9-]+$", name):
            _add(findings, "high", "frontmatter",
                 f"name '{name}' is not kebab-case.",
                 "Use lowercase letters, digits, and hyphens only.")
        if name.startswith("-") or name.endswith("-") or "--" in name:
            _add(findings, "high", "frontmatter",
                 f"name '{name}' starts/ends with a hyphen or has '--'.",
                 "Fix the hyphen placement.")
        if len(name) > 64:
            _add(findings, "high", "frontmatter",
                 f"name is {len(name)} chars (max 64).", "Shorten it.")
        if "anthropic" in name.lower() or "claude" in name.lower():
            _add(findings, "medium", "frontmatter",
                 f"name '{name}' contains a reserved word (anthropic/claude).",
                 "Rename without 'anthropic' or 'claude'.")

    # description -- the highest-leverage field
    desc = fm.get("description")
    if not desc or not str(desc).strip():
        _add(findings, "high", "description", "Missing 'description'.",
             "Add a third-person description stating WHAT the skill does and "
             "WHEN to use it, with concrete trigger phrases.")
        return name, ""
    desc = str(desc).strip()
    if "<" in desc or ">" in desc:
        _add(findings, "high", "description",
             "Description contains angle brackets (rejected on upload).",
             "Remove '<' and '>'.")
    if len(desc) > 1024:
        _add(findings, "high", "description",
             f"Description is {len(desc)} chars (max 1024).", "Trim it.")
    elif len(desc) < 120:
        _add(findings, "medium", "description",
             f"Description is short ({len(desc)} chars). Short descriptions are a "
             "leading cause of under-triggering -- the skill never fires.",
             "Expand with concrete trigger phrases: 'Use this whenever the user "
             "mentions X, Y, or Z, even if they don't say <keyword>.'")
    # Does it say WHEN, not just WHAT?
    when_signals = ("use this", "use when", "use whenever", "trigger", "whenever the user",
                    "when the user", "when a", "when you")
    if not any(s in desc.lower() for s in when_signals):
        _add(findings, "high", "description",
             "Description does not clearly state WHEN to trigger (no 'use when/"
             "whenever...' phrasing). Claude tends to under-trigger without it.",
             "Add an explicit, slightly 'pushy' trigger clause listing the user "
             "phrases/contexts that should fire the skill.")
    # Negative triggers reduce false positives in overlapping domains.
    neg_signals = ("do not use", "don't use", "not for", "instead use", "use the", "rather than")
    if not any(s in desc.lower() for s in neg_signals):
        _add(findings, "low", "description",
             "No negative trigger ('do NOT use this for...'). Optional, but it "
             "sharply reduces false-positive firing when skills overlap.",
             "If a sibling skill could be confused with this one, add a one-line "
             "exclusion pointing to it.")
    # Second person is a style smell for descriptions.
    if re.search(r"\byou(r)?\b", desc.lower()):
        _add(findings, "low", "description",
             "Description uses second person ('you/your'). Convention is third "
             "person ('Use this when the user...').",
             "Rewrite in third person.")
    return name, desc


def check_body(body, findings):
    lines = body.splitlines()
    n_lines = len(lines)
    approx_tokens = max(1, len(body) // 4)

    if n_lines > 500:
        _add(findings, "high", "size",
             f"SKILL.md body is {n_lines} lines (> 500). Once a skill triggers, the "
             f"whole body stays in context for the session (~{approx_tokens} tokens), "
             "competing with the live task.",
             "Move detail into references/ (read on demand) and keep the body as a "
             "lean index: overview, workflow, pointers.")
    elif n_lines > 300:
        _add(findings, "medium", "size",
             f"SKILL.md body is {n_lines} lines (soft limit ~300). Approaching the "
             "point where splitting pays off.",
             "Consider moving domain-specific or rarely-used detail into references/.")

    # @imports do not work in SKILL.md (only in CLAUDE.md).
    for i, line in enumerate(lines, 1):
        if re.match(r"^\s*@[\w./-]+\s*$", line):
            _add(findings, "high", "imports",
                 f"'@import' syntax on line {i} ('{line.strip()}'). @-imports work "
                 "in CLAUDE.md, NOT in SKILL.md -- this line will not load anything.",
                 "Replace with an instruction: 'Read references/<file>.md for ...'.",
                 location=f"SKILL.md:{i}")

    # Backslash paths.
    if re.search(r"[\w-]+\\[\w-]+", body):
        _add(findings, "low", "paths",
             "Backslash path separators found. Use forward slashes even on Windows.",
             "Switch '\\' to '/' in bundled paths.")

    # The shouting file: many caps directives suggest rules without reasons.
    caps_count = 0
    for word in CAPS_DIRECTIVES:
        caps_count += len(re.findall(rf"\b{re.escape(word)}\b", body))
    if caps_count >= 6:
        _add(findings, "medium", "anti-pattern",
             f"{caps_count} ALL-CAPS directives (MUST/ALWAYS/NEVER/...). Heavy "
             "shouting buries the rules that matter and skips the reasoning Claude "
             "needs to generalize.",
             "Keep one or two genuine 'IMPORTANT' markers. For the rest, state the "
             "rule AND the why ('use X because Y') so the model can handle edge cases.")
    elif caps_count >= 3:
        _add(findings, "low", "anti-pattern",
             f"{caps_count} ALL-CAPS directives. Watch for shouting without reasons.",
             "Prefer 'rule + why' over bare imperatives.")

    return n_lines, approx_tokens


def _has_toc(text):
    head = "\n".join(text.splitlines()[:40]).lower()
    if "table of contents" in head or "## contents" in head:
        return True
    # A cluster of links/list items near the top also counts as a TOC.
    return head.count("\n- ") + head.count("\n* ") + head.count("](#") >= 4


def check_structure(skill_dir, body, findings):
    has_scripts = (skill_dir / "scripts").is_dir()
    has_refs = (skill_dir / "references").is_dir()

    # Reference files: TOC for long ones, and flag deep nesting.
    if has_refs:
        for ref in (skill_dir / "references").rglob("*.md"):
            rel = ref.relative_to(skill_dir)
            depth = len(rel.parts) - 1  # parts beyond 'references/<file>'
            try:
                rtext = ref.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rlines = len(rtext.splitlines())
            if rlines > 100 and not _has_toc(rtext):
                _add(findings, "medium", "references",
                     f"{rel} is {rlines} lines but has no table of contents. Claude "
                     "may preview long files with a partial read and miss sections.",
                     "Add a short TOC at the top so the full scope is visible.",
                     location=str(rel))
            if depth > 1:
                _add(findings, "low", "references",
                     f"{rel} is nested deeper than one level. Deeply nested refs get "
                     "partially read and produce incomplete information.",
                     "Keep references one level deep and link each directly from SKILL.md.",
                     location=str(rel))
            # Is the reference actually pointed to from the body?
            if ref.name not in body and str(rel) not in body and rel.stem not in body:
                _add(findings, "low", "references",
                     f"{rel} does not appear to be referenced from SKILL.md.",
                     "Add a pointer ('Read {rel} when ...') or remove the file -- an "
                     "unreferenced file is one Claude will never open.".format(rel=rel),
                     location=str(rel))

    # Top-level scripts never mentioned in the body = won't be run. Only check
    # direct children of scripts/ -- nested files (scripts/pkg/helper.py) and
    # private modules (_x.py, __init__.py) are implementation details a caller
    # need not name. Match the stem too, so module-style refs like
    # `python -m scripts.foo` count as mentioning foo.py.
    if has_scripts:
        for scr in sorted((skill_dir / "scripts").glob("*.py")):
            if scr.name == "__init__.py" or scr.name.startswith("_"):
                continue
            rel = scr.relative_to(skill_dir)
            if scr.name not in body and str(rel) not in body and scr.stem not in body:
                _add(findings, "low", "scripts",
                     f"{rel} exists but is not mentioned in SKILL.md, so Claude "
                     "won't know to run it.",
                     f"State explicitly whether Claude should run it "
                     f"('Run {rel} to ...') or remove it.",
                     location=str(rel))

    return has_scripts, has_refs


SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
SEV_LABEL = {"high": "HIGH", "medium": "MED ", "low": "LOW ", "info": "INFO"}


def render_report(name, desc, n_lines, approx_tokens, has_scripts, has_refs, findings):
    out = []
    out.append("=" * 64)
    out.append(f"SKILL AUDIT  ::  {name or '(unnamed)'}")
    out.append("=" * 64)
    out.append(f"  description : {len(desc)} chars" + ("" if desc else "  (MISSING)"))
    out.append(f"  body        : {n_lines} lines  (~{approx_tokens} tokens once loaded)")
    out.append(f"  scripts/    : {'yes' if has_scripts else 'no'}")
    out.append(f"  references/ : {'yes' if has_refs else 'no'}")
    out.append("")

    findings_sorted = sorted(findings, key=lambda f: SEV_ORDER.get(f["severity"], 9))
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    summary = ", ".join(f"{counts[s]} {s}" for s in ("high", "medium", "low", "info") if s in counts)
    out.append(f"FINDINGS ({summary or 'none'}):")
    out.append("")

    if not findings_sorted:
        out.append("  No mechanical issues detected. Proceed to judgment-based review.")
    for i, f in enumerate(findings_sorted, 1):
        out.append(f"  [{SEV_LABEL[f['severity']]}] {f['category']} @ {f['location']}")
        out.append(f"        {f['message']}")
        out.append(f"     -> {f['suggestion']}")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Deterministic checks for a SKILL.md skill folder.")
    parser.add_argument("skill_path", help="Folder containing SKILL.md")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a report")
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_path)
    if skill_dir.is_file() and skill_dir.name == "SKILL.md":
        skill_dir = skill_dir.parent
    if not skill_dir.is_dir():
        print(f"error: not a directory: {skill_dir}", file=sys.stderr)
        return 2
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"error: no SKILL.md in {skill_dir}", file=sys.stderr)
        return 2

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body, fm_err = _split_frontmatter(text)
    findings = []

    if fm_err:
        _add(findings, "high", "frontmatter", f"Frontmatter problem: {fm_err}.",
             "Fix the YAML frontmatter; name and description are required.")
        name, desc = "", ""
    else:
        name, desc = check_frontmatter(fm, findings)

    n_lines, approx_tokens = check_body(body, findings)
    has_scripts, has_refs = check_structure(skill_dir, body, findings)

    if args.json:
        print(json.dumps({
            "name": name, "description_chars": len(desc),
            "body_lines": n_lines, "approx_body_tokens": approx_tokens,
            "has_scripts": has_scripts, "has_references": has_refs,
            "findings": findings,
        }, indent=2))
    else:
        print(render_report(name, desc, n_lines, approx_tokens, has_scripts, has_refs, findings))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
