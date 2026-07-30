#!/usr/bin/env python3
"""Heuristic complexity/nesting signal for a file or line range.

Regex-based approximation, not a real parser. Use as a directional signal
only -- never as a gate on whether a refactor pass is good.
"""
import argparse
import re
import sys

DECISION_KEYWORDS = re.compile(
    r"\b(if|elif|for|foreach|while|case|when|catch|except|switch)\b"
)
BOOL_OPERATORS = re.compile(r"(&&|\|\||\bor\b|\band\b)")
# Ternary '?', excluding optional chaining '?.' and nullish coalescing '??'.
TERNARY = re.compile(r"(?<!\?)\?(?!\.|\?)")

INDENT_EXTENSIONS = (".py", ".yml", ".yaml")


def read_lines(path, start, end):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    start_idx = (start - 1) if start else 0
    end_idx = end if end else len(lines)
    return lines[start_idx:end_idx]


def complexity_estimate(lines):
    text = "".join(lines)
    score = 1
    score += len(DECISION_KEYWORDS.findall(text))
    score += len(BOOL_OPERATORS.findall(text))
    score += len(TERNARY.findall(text))
    return score


def nesting_depth_braces(lines):
    depth = 0
    max_depth = 0
    in_string = None
    for line in lines:
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                if ch == "\\":
                    i += 2
                    continue
                if ch == in_string:
                    in_string = None
            elif ch in ("'", '"', "`"):
                in_string = ch
            elif ch == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == "}":
                depth = max(0, depth - 1)
            i += 1
    return max_depth


def nesting_depth_indent(lines):
    indents = [
        len(s) - len(s.lstrip(" "))
        for s in (line.rstrip("\n") for line in lines)
        if s.strip()
    ]
    if not indents:
        return 0
    positive = [i for i in indents if i > 0]
    unit = min(positive) if positive else 4
    base = min(indents)
    return max((i - base) // unit for i in indents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    parser.add_argument("--start", type=int, default=None)
    parser.add_argument("--end", type=int, default=None)
    args = parser.parse_args()

    lines = read_lines(args.file, args.start, args.end)
    if not lines:
        print("No lines read -- check --start/--end against the file.", file=sys.stderr)
        sys.exit(1)

    complexity = complexity_estimate(lines)
    if args.file.endswith(INDENT_EXTENSIONS):
        nesting = nesting_depth_indent(lines)
    else:
        nesting = nesting_depth_braces(lines)

    print(f"complexity_estimate: {complexity}")
    print(f"max_nesting_depth: {nesting}")
    print(f"line_count: {len(lines)}")
    print("(heuristic signal only -- not a real parser; directional indicator, never a gate)")


if __name__ == "__main__":
    main()
