#!/usr/bin/env python3
"""Validate a skill brief produced by skillit:interview.

Checks that all 12 required sections are present under their canonical headings
and filled with something other than the template's placeholder text. Sections
6 and 7 are checked label by label, and sections 4 and 7 against their closed
sets of allowed values, because a section with its first slot filled and the
rest empty is the failure this gate exists to catch.

Section order is not checked; heading text is.

Usage:
    python3 scripts/check_brief.py path/to/skill-brief-name.md
    python3 scripts/check_brief.py path/to/brief.md --json
    python3 scripts/check_brief.py --self-test

Exit codes:
    0  brief is complete (advisories may still print)
    1  brief has missing or unfilled sections
    2  bad usage or unreadable file (details on stderr)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Section number -> canonical heading text. The authoring skill reads the brief
# by these headings, so a renamed heading silently drops that input.
REQUIRED = {
    1: "One job",
    2: "Container check",
    3: "Baseline failure",
    4: "Skill type",
    5: "Draft description",
    6: "Trigger phrases",
    7: "Output shape",
    8: "Degrees of freedom",
    9: "Script candidates",
    10: "Gotchas",
    11: "Eval prompts",
    12: "Open questions",
}

# Sections whose template carries several labeled slots. Each label must be
# present with non-placeholder text after it. Labels rather than paragraph
# counting, because prose blocks are not slots: three answers on three
# consecutive lines are one block, and one answer split in two is two.
MULTI_SLOT = {
    6: ["Should fire", "Should not fire"],
    7: ["Form", "Template or example output", "What run 50 must share with run 1"],
}

# Closed enumerations. Section 4 decides which sections the authoring skill
# treats as required, so an unrecognized value silently leaves the author with
# no criteria at all.
CLOSED_SETS = {
    4: (None, {"technique", "discipline", "pattern", "reference"}),
    7: ("Form", {"fixed template", "template with judgment slots", "free-form"}),
}

# Sections that need a numbered list of a given length.
NUMBERED_MIN = {
    11: (3, "one plain case, one edge case, one near-miss"),
}

# A line counts as placeholder when nothing survives stripping the template's
# "..." markers and optional list numbering.
PLACEHOLDER_LINE = re.compile(r"^\s*(?:\d+\.\s*)?(?:\.\.\.)?\s*$")
HINT_LINE = re.compile(r"^\s*>")
NUMBERED_ITEM = re.compile(r"^\s*\d+\.\s+(?!\.\.\.\s*$)\S")

# Slots the bank forbids leaving empty. Q3.1 tells the interviewer to supply
# candidate phrasings when the user cannot, so there is no legitimate brief with
# no trigger phrases - section 5's description would have nothing to tune on.
NON_DEFERRABLE = {(6, "Should fire")}

# An author who has nothing to record, or who moved the question to section 12,
# needs a way to clear the gate. Without one the instruction in the failure
# message deadlocks them into inventing an answer - the failure this gate exists
# to prevent.
DEFERRED = re.compile(
    r"^\s*(?:(?:none|n/?a|unanswered|deferred|open)"
    r"(?:\s*[-\u2013\u2014:]?\s*see section 12)?|see section 12)\s*$",
    re.I,
)

# Markdown allows either syntax, and a pasted example whose own content uses
# backticks has to be tilde-fenced. Missing that reads the paste as structure.
FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")

HEADING = re.compile(r"^##\s+(\d+)\.\s*(.+?)\s*$")
DESC_LIMIT = 1024


def fence_unterminated(text):
    """True when a fence opens and never closes, which swallows later sections."""
    open_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            open_fence = not open_fence
    return open_fence


def parse_sections(text):
    """Return {number: (heading_text, body_lines)} for every '## N. Title'.

    Fenced blocks are content, never structure. Q4.2 asks the user to paste an
    example output, and a pasted report template full of '## 1. Summary' lines
    would otherwise be read as brief sections - blaming section 1 for a mistake
    the author made nowhere.
    """
    sections = {}
    current = None
    fenced = False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            if current is not None:
                sections[current][1].append(line)
            continue
        if fenced:
            if current is not None:
                sections[current][1].append(line)
            continue
        match = HEADING.match(line)
        if match:
            current = int(match.group(1))
            sections[current] = (match.group(2), [])
        elif current is not None:
            sections[current][1].append(line)
    return sections


def unfenced(lines):
    """Body lines outside fenced blocks, for counts that must not see pasted text."""
    out = []
    fenced = False
    for line in lines:
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return out


def content_blocks(lines):
    """Split a section body into blank-line-separated blocks of real content.

    Hint lines and placeholder lines are dropped first, so a block survives only
    when the author wrote something into that slot.
    """
    blocks = []
    current = []
    for line in lines:
        if HINT_LINE.match(line):
            continue
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        if PLACEHOLDER_LINE.match(line):
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def slot_value(lines, label, siblings=()):
    """Text belonging to 'label:' in a section body, or None when absent.

    A slot's answer may sit on the label's own line or on the lines after it -
    the bank asks the user to paste a template and to list 6 to 10 phrasings,
    and both land on following lines. Reading only the label's line false-fails
    the two highest-value slots in the brief.
    """
    pattern = re.compile(rf"^\s*{re.escape(label)}[^:]*:\s*(.*)$", re.I)
    others = [
        re.compile(rf"^\s*{re.escape(other)}[^:]*:", re.I)
        for other in siblings
        if other != label
    ]
    for index, line in enumerate(lines):
        if HINT_LINE.match(line):
            continue
        match = pattern.match(line)
        if not match:
            continue
        if match.group(1).strip():
            return match.group(1).strip()
        tail = []
        for following in lines[index + 1:]:
            if HINT_LINE.match(following) or PLACEHOLDER_LINE.match(following):
                continue
            if any(other.match(following) for other in others):
                break
            if following.strip():
                tail.append(following.strip())
        return " ".join(tail)
    return None


def plain_text(lines):
    """Section body as one string, hints and placeholders removed."""
    return " ".join(
        line.strip()
        for line in lines
        if line.strip() and not HINT_LINE.match(line) and not PLACEHOLDER_LINE.match(line)
    )


def forced_choice_message(number, expected, label=None):
    """Message for an empty forced-choice slot, or None when it is deferrable.

    The generic message offers "none" and "see section 12", and both are wrong
    for a closed set - following them costs the author another failing run.
    """
    if (number, label) in NON_DEFERRABLE:
        return (
            f"section {number} ({expected}) slot '{label}:' is unfilled, and it cannot "
            f"be deferred. The interviewer supplies candidate phrasings when the user "
            f"cannot - mark them as yours, because the draft description has nothing "
            f"to tune on otherwise."
        )
    entry = CLOSED_SETS.get(number)
    if not entry or entry[0] != label:
        return None
    options = ", ".join(sorted(entry[1]))
    slot = f" slot '{label}:'" if label else ""
    return (
        f"section {number} ({expected}){slot} is unfilled. This is a forced choice, "
        f"not a deferrable slot - pick one of: {options}."
    )


def check(text):
    """Return (problems, advisories). An empty problems list means the brief passes."""
    problems = []
    advisories = []

    if fence_unterminated(text):
        return (
            [
                "a code fence opens and never closes, so every section after it was "
                "read as fenced content. Close the fence and rerun - the sections "
                "reported missing are almost certainly fine."
            ],
            advisories,
        )

    sections = parse_sections(text)

    for number, expected in REQUIRED.items():
        if number not in sections:
            problems.append(
                f"section {number} missing: expected a heading '## {number}. {expected}'"
            )
            continue

        found, body = sections[number]
        if found.lower() != expected.lower():
            problems.append(
                f"section {number} renamed: found '{found}', expected '{expected}' "
                f"- the authoring skill matches this heading literally"
            )

        blocks = content_blocks(body)
        deferrable = number not in CLOSED_SETS and not any(
            n == number for n, _ in NON_DEFERRABLE
        )
        if blocks and DEFERRED.search(plain_text(body)) and deferrable:
            continue
        if not blocks:
            closed_label = (CLOSED_SETS.get(number) or (None,))[0]
            problems.append(forced_choice_message(number, expected, closed_label) or (
                f"section {number} ({expected}) is unfilled: still placeholder text. "
                f"Answer it, write \"none\" when there is nothing to record, or write "
                f"\"see section 12\" after moving the question there."
            ))
            continue

        if number in MULTI_SLOT:
            labels = MULTI_SLOT[number]
            for label in labels:
                value = slot_value(body, label, labels)
                if value is None:
                    problems.append(
                        f"section {number} ({expected}) is missing the '{label}:' label. "
                        f"Keep every label from the template - the author reads this "
                        f"section slot by slot, and an absent label reads as no answer."
                    )
                elif DEFERRED.search(value):
                    if (number, label) not in NON_DEFERRABLE:
                        continue
                    problems.append(
                        f"section {number} ({expected}) defers '{label}:', which cannot "
                        f"be deferred. The interviewer supplies candidate phrasings when "
                        f"the user cannot - mark them as yours rather than leaving this "
                        f"empty, because the draft description has nothing to tune on."
                    )
                elif not value or PLACEHOLDER_LINE.match(value):
                    problems.append(
                        forced_choice_message(number, expected, label) or (
                            f"section {number} ({expected}) has '{label}:' with nothing "
                            f"after it. Answer it, write \"none\", or write \"see section "
                            f"12\" after moving the question there."
                        )
                    )

        if number in NUMBERED_MIN:
            needed, what = NUMBERED_MIN[number]
            items = sum(1 for line in unfenced(body) if NUMBERED_ITEM.match(line))
            if items < needed:
                problems.append(
                    f"section {number} ({expected}) has {items} of {needed} numbered "
                    f"items: needs {what}. The near-miss is the one that catches an "
                    f"over-broad description, so it is not optional."
                )

    for number, (label, allowed) in CLOSED_SETS.items():
        if number not in sections:
            continue
        body = sections[number][1]
        value = slot_value(body, label, MULTI_SLOT.get(number, ())) if label else plain_text(body)
        if not value or PLACEHOLDER_LINE.match(value):
            continue
        low = value.lower()
        if not any(option in low for option in allowed):
            options = ", ".join(sorted(allowed))
            problems.append(
                f"section {number} ({REQUIRED[number]})"
                + (f" slot '{label}'" if label else "")
                + f" reads '{value[:60]}', which is not one of: {options}. "
                f"This is a forced choice, not a deferrable slot - pick the closest "
                f"value, because it decides what the authoring skill treats as required."
            )

    if 5 in sections:
        desc = plain_text(sections[5][1])
        if len(desc) > DESC_LIMIT:
            problems.append(
                f"section 5 (Draft description) is {len(desc)} chars, over the "
                f"{DESC_LIMIT}-char frontmatter limit - trim it before handoff"
            )
        if "<" in desc or ">" in desc:
            problems.append(
                "section 5 (Draft description) contains an angle bracket, which is "
                "not allowed in a skill description"
            )

    if 1 in sections:
        job = plain_text(sections[1][1])
        if re.search(r"\band\b|&", job, re.I):
            advisories.append(
                "section 1 (One job) contains 'and'. Read the sentence back: if the "
                "'and' joins two verbs, this is two skills and both will trigger "
                "badly. If it joins two objects of one verb, it is fine. Judgment "
                "call - this check cannot make it for you."
            )

    return problems, advisories


SECTIONS = [
    (1, "One job", "Turn the last 24h of Sentry issues into the standup blurb."),
    (2, "Container check", "Skill. Closest alternative was a CLAUDE.md line."),
    (3, "Baseline failure", "Format varies every run. Evidence: reproducible."),
    (4, "Skill type", "technique - needs a worked example and Gotchas."),
    (5, "Draft description", "Writes the standup blurb. Use when the user says X."),
    (6, "Trigger phrases", "Should fire: \"standup blurb\"\nShould not fire: postmortem"),
    (7, "Output shape", "Form: fixed template\nTemplate or example output: five lines\nWhat run 50 must share with run 1: same order"),
    (8, "Degrees of freedom", "Low for the fetch, high for the summaries."),
    (9, "Script candidates", "Fetch issues -> scripts/fetch.py"),
    (10, "Gotchas", "Issues tagged internal never appear."),
    (11, "Eval prompts", "1. plain\n2. edge\n3. near-miss"),
    (12, "Open questions", "1. Whether Datadog counts. Ask on-call."),
]


def build_brief(overrides=None):
    overrides = overrides or {}
    parts = ["# Skill brief: test"]
    for number, heading, body in SECTIONS:
        parts.append(f"\n## {number}. {heading}\n\n{overrides.get(number, body)}")
    return "\n".join(parts) + "\n"


def self_test():
    """Regression cases this gate has already failed once. Returns exit code."""
    cases = [
        ("complete brief passes", {}, True),
        # section 7 answers on consecutive lines, no blank separators
        ("section 7 unspaced labels pass", {7: "Form: fixed template\nTemplate or example output: five lines\nWhat run 50 must share with run 1: same order"}, True),
        # the two false passes the paragraph-counting version let through
        ("section 6 missing anti-triggers fails", {6: 'Should fire: "standup blurb"\n\nAlso "what broke"'}, False),
        ("section 7 missing run-50 label fails", {7: "Form: fixed template\n\nTemplate or example output: five lines"}, False),
        # a numbered placeholder is not an answer
        ("section 11 placeholder items fail", {11: "1. plain case\n2. ...\n3. ..."}, False),
        # answers that land on the lines after their label
        ("section 6 bulleted list passes", {6: 'Should fire:\n- "standup blurb"\n- "what broke overnight"\nShould not fire: postmortem'}, True),
        ("section 7 pasted template passes", {7: "Form: fixed template\nTemplate or example output:\n  paged\n  degraded-not-paged\nWhat run 50 must share with run 1: same order"}, True),
        # a wholesale deferral clears a section; a partial one must not
        ("section 11 wholesale deferral passes", {11: "none - see section 12"}, True),
        ("section 11 partial list plus deferral fails", {11: "1. plain\n2. edge\nnear-miss: see section 12"}, False),
        ("section 6 one label plus deferral fails", {6: 'Should fire: "x" or see section 12'}, False),
        ("deferred gotchas pass", {10: "none - see section 12"}, True),
        ("deferred skill type fails", {4: "unanswered - see section 12"}, False),
        # a deferral that leads the section must not bypass the slot checks either
        ("section 11 leading deferral plus partial list fails", {11: "none yet\n1. plain\n2. edge"}, False),
        ("section 6 leading deferral plus one label fails", {6: 'see section 12\nShould fire: "x"'}, False),
        # message text, because two fixes changed only the message
        ("section 4 empty names the forced choice", {4: "..."}, False, "forced choice, not a deferrable slot"),
        ("section 7 empty Form names the forced choice", {7: "Form:\nTemplate or example output: five lines\nWhat run 50 must share with run 1: same order"}, False, "slot 'Form:' is unfilled"),
        ("section 7 all placeholder names the forced choice", {7: "..."}, False, "forced choice"),
        ("section 7 run-50 label quoted in full", {7: "Form: fixed template\nTemplate or example output: five lines"}, False, "'What run 50 must share with run 1:'"),
        # a pasted template with numbered headings is content, not structure
        ("section 7 fenced numbered headings pass", {7: "Form: fixed template\nTemplate or example output:\n```markdown\n## 1. Summary\n\n## 2. Findings\n```\nWhat run 50 must share with run 1: same headings"}, True),
        ("section 11 fenced numbers do not count as prompts", {11: "1. plain\n```\n2. fenced\n3. fenced\n```"}, False),
        # the should-fire slot cannot be deferred
        ("section 6 deferred should-fire fails", {6: "Should fire: none\nShould not fire: none"}, False, "cannot be deferred"),
        ("section 6 wholesale deferral fails", {6: "none"}, False),
        # tilde fences must behave exactly like backtick fences
        ("section 7 tilde-fenced headings pass", {7: "Form: fixed template\nTemplate or example output:\n~~~\n## 1. Summary\n\n## 2. Findings\n~~~\nWhat run 50 must share with run 1: same headings"}, True),
        ("section 11 tilde-fenced numbers do not count", {11: "1. plain\n~~~\n2. fenced\n3. fenced\n~~~"}, False),
        # an unterminated fence is reported as itself
        ("unterminated fence names the fence", {7: "Form: fixed template\n```markdown\n## 1. Summary"}, False, "never closes"),
        # an empty non-deferrable slot is told what clears it
        ("section 6 empty should-fire names the rule", {6: "Should fire:\nShould not fire: postmortem"}, False, "cannot be deferred"),
        # closed sets
        ("unknown skill type fails", {4: "helper"}, False),
        ("unknown output form fails", {7: "Form: whatever\nTemplate or example output: x\nWhat run 50 must share with run 1: y"}, False),
    ]
    failures = 0
    for case in cases:
        name, overrides, should_pass = case[:3]
        expect_text = case[3] if len(case) > 3 else None
        problems, _ = check(build_brief(overrides))
        passed = not problems
        ok = passed == should_pass
        if ok and expect_text:
            ok = any(expect_text in problem for problem in problems)
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failures += 1
            if expect_text:
                print(f"          expected message to contain: {expect_text}")
            for problem in problems:
                print(f"          {problem}")
    print(f"\n{len(cases) - failures}/{len(cases)} self-tests passed")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate a skillit:interview skill brief."
    )
    parser.add_argument(
        "brief", nargs="?", help="path to the skill brief markdown file"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the validator's own regression cases and exit",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit results as JSON on stdout"
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not args.brief:
        parser.error("a brief path is required unless --self-test is given")

    path = Path(args.brief)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    problems, advisories = check(text)

    if args.json:
        print(
            json.dumps(
                {
                    "brief": str(path),
                    "ok": not problems,
                    "problems": problems,
                    "advisories": advisories,
                },
                indent=2,
            )
        )
        return 1 if problems else 0

    if problems:
        print(f"{path}: {len(problems)} problem(s)\n")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print(f"{path}: all 12 sections present and filled.")

    if advisories:
        print(f"\nadvisories ({len(advisories)}, exit code unaffected):\n")
        for advisory in advisories:
            print(f"  ? {advisory}")

    if problems:
        print("\nFix the problems, then rerun. Do not hand off a brief that exits 1.")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
