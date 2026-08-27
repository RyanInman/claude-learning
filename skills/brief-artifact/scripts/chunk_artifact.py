#!/usr/bin/env python3
"""Split a prose file, code file, directory, or git diff into reviewable chunks.

Writes <out>/inventory.json plus one <out>/chunk-NN.txt per chunk and prints a
one-line summary per chunk. Chunk sizes follow the review-size research: about
200 LOC for code and about 1500 words for prose, split at structural boundaries.

Usage:
    chunk_artifact.py PATH [--out DIR]
    chunk_artifact.py --diff REF [--out DIR]
"""

import argparse
import json
import os
import re
import subprocess
import sys

CODE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".rb",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".php", ".sh", ".sql",
    ".scala", ".lua", ".pl", ".r", ".m", ".mm", ".dart", ".ex", ".exs",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
# generated or vendored paths that add chunks without adding meaning
DEFAULT_EXCLUDE = re.compile(r"-workspace/|\.lock$|package-lock\.json|yarn\.lock|\.min\.(js|css)$|/outputs/|/run-\d+/")
MAX_CHUNKS = 40
HIGH_RISK_PATH = re.compile(
    r"auth|login|session|token|password|secret|cred|permission|acl|"
    r"\bdb\b|database|migration|schema|sql|"
    r"package\.json|requirements|pyproject|go\.mod|Cargo\.toml|Gemfile|\.lock$",
    re.I,
)
HIGH_RISK_TEXT = re.compile(
    r"\b(subprocess|os\.system|exec\(|eval\(|socket|requests\.|urllib|fetch\(|"
    r"http\.|open\(|writeFile|unlink|rm -rf|DROP |DELETE FROM|UPDATE |INSERT |"
    r"jwt|bcrypt|hashlib|crypto)",
)
BREAK_LINE = re.compile(r"^(def |class |function |func |fn |pub |export |impl |@|}\s*$|\s*$)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
PROMPT = """You are reading one chunk of a larger artifact. Read only the chunk text in {text_path}.
Do not look at other files, run code, or search the web.

Chunk id: {cid}
Anchor: {anchor}
Type: {ctype}   (prose | code | diff)

Write a JSON object to {json_path} with exactly these fields:
- summary: 80 words max. Say what this chunk does or argues, top-down, in plain language.
- claims: at most 6 atomic claims (prose) or behaviors (code), the ones a reviewer
  must check. Each has text (25 words max), anchor (source line number from the
  "NNN|" prefix, or file:line for diffs), and status:
    verified      the chunk shows the evidence (code visible, source cited, data shown)
    unverified    stated with no evidence in the chunk; use this when unsure
    contradicted  two places in the chunk disagree; anchor must read "A vs B"
- risks: at most 4 {{kind, anchor, note}}. note is 20 words max. kind is one of
    hallucinated-api, duplicate-logic, missing-edge-case (code)
    uncited-number, unsupported-claim (prose)
  Flag only what you see. Do not invent risks to fill the list.
- least_confident: one sentence naming the part you understood least or could not check.

Rules:
- Every claim and risk needs an anchor copied from the chunk, because the reader
  will drill in from that pointer.
- Do not summarize anything outside the chunk text.
- Output the JSON file only. No prose reply.
"""


def is_binary(path):
    with open(path, "rb") as f:
        return b"\x00" in f.read(8192)


def risk_tier(path, text):
    if HIGH_RISK_PATH.search(path or "") or HIGH_RISK_TEXT.search(text):
        return "high"
    return "low"


def split_prose(text, max_words):
    """Split at markdown headings, merging small sections up to max_words."""
    lines = text.splitlines()
    sections = []  # (heading_path, start_line, lines)
    stack = []
    cur = {"heading": "(start)", "start": 1, "lines": []}
    for i, line in enumerate(lines, 1):
        m = HEADING.match(line)
        if m:
            if cur["lines"] and any(l.strip() for l in cur["lines"]):
                sections.append(cur)
            level, title = len(m.group(1)), m.group(2).strip()
            stack = [s for s in stack if s[0] < level] + [(level, title)]
            cur = {"heading": " > ".join(t for _, t in stack[-2:]), "start": i, "lines": [line]}
        else:
            cur["lines"].append(line)
    if cur["lines"]:
        sections.append(cur)

    # split any oversized section at paragraph breaks
    expanded = []
    for s in sections:
        if len(" ".join(s["lines"]).split()) <= max_words:
            expanded.append(s)
            continue
        buf, start, part = [], s["start"], 1
        for j, line in enumerate(s["lines"]):
            buf.append(line)
            if line.strip() == "" and len(" ".join(buf).split()) >= max_words * 0.8:
                expanded.append({"heading": f'{s["heading"]} (part {part})', "start": start, "lines": buf})
                buf, start, part = [], s["start"] + j + 1, part + 1
        if buf:
            expanded.append({"heading": f'{s["heading"]} (part {part})', "start": start, "lines": buf})

    # merge small consecutive sections
    chunks = []
    acc = None
    for s in expanded:
        words = len(" ".join(s["lines"]).split())
        if acc and acc["words"] + words <= max_words:
            acc["lines"] += s["lines"]
            acc["words"] += words
            acc["end_heading"] = s["heading"]
        else:
            if acc:
                chunks.append(acc)
            acc = {"heading": s["heading"], "end_heading": s["heading"], "start": s["start"], "lines": list(s["lines"]), "words": words}
    if acc:
        chunks.append(acc)

    out = []
    for c in chunks:
        end = c["start"] + len(c["lines"]) - 1
        anchor = c["heading"] if c["heading"] == c["end_heading"] else f'{c["heading"]} .. {c["end_heading"]}'
        numbered = "\n".join(f"{c['start'] + k:5d}| {l}" for k, l in enumerate(c["lines"]))
        out.append({"anchor": f"{anchor} (L{c['start']}-L{end})", "text": numbered, "size": c["words"], "unit": "words"})
    return out


def split_code(text, path, max_lines):
    """Split into ~max_lines windows, breaking at def/class/blank lines when possible."""
    lines = text.splitlines()
    out, start = [], 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        if end < len(lines):
            # search backward up to 40 lines for a structural boundary
            for k in range(end, max(start + max_lines // 2, end - 40), -1):
                if BREAK_LINE.match(lines[k]):
                    end = k
                    break
        body = "\n".join(f"{start + k + 1:5d}| {l}" for k, l in enumerate(lines[start:end]))
        out.append({"anchor": f"{path}:{start + 1}-{end}", "text": body, "size": end - start, "unit": "lines"})
        start = end
    return out


def split_diff(text, max_lines):
    """Split a unified diff per file, then group hunks up to max_lines."""
    files = re.split(r"(?m)^(?=diff --git )", text)
    out = []
    for block in files:
        if not block.strip():
            continue
        m = re.search(r"^\+\+\+ b/(.*)$", block, re.M)
        path = m.group(1) if m else "(unknown)"
        parts = re.split(r"(?m)^(?=@@ )", block)
        header, hunks = parts[0], parts[1:]
        if not hunks:
            out.append({"anchor": f"{path} (no hunks)", "text": block, "size": block.count("\n"), "unit": "lines"})
            continue
        acc, acc_lines, first_at = [], 0, None
        for h in hunks:
            n = h.count("\n")
            at = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", h)
            if acc and acc_lines + n > max_lines:
                out.append({"anchor": f"{path}:{first_at}+ (diff)", "text": header + "".join(acc), "size": acc_lines, "unit": "lines"})
                acc, acc_lines, first_at = [], 0, None
            if first_at is None:
                first_at = at.group(1) if at else "?"
            acc.append(h)
            acc_lines += n
        if acc:
            out.append({"anchor": f"{path}:{first_at}+ (diff)", "text": header + "".join(acc), "size": acc_lines, "unit": "lines"})
    # merge small consecutive file diffs so tiny files do not each cost a chunk
    merged = []
    for c in out:
        if merged and merged[-1]["size"] + c["size"] <= max_lines:
            m = merged[-1]
            m["anchor"] = m["anchor"].replace(" (diff)", "") + ", " + c["anchor"]
            m["text"] += "\n" + c["text"]
            m["size"] += c["size"]
        else:
            merged.append(dict(c))
    return merged


def collect_files(target):
    if os.path.isfile(target):
        return [target]
    found = []
    for root, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            p = os.path.join(root, f)
            if not is_binary(p):
                found.append(p)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="file or directory")
    ap.add_argument("--diff", metavar="REF", help="git diff REF instead of a path")
    ap.add_argument("--out", default="brief-work", help="output directory (default: ./brief-work)")
    ap.add_argument("--prose-words", type=int, default=1500)
    ap.add_argument("--code-lines", type=int, default=200)
    ap.add_argument("--exclude", metavar="REGEX", help="drop paths matching this regex (added to the built-in exclude list)")
    ap.add_argument("--allow-large", action="store_true", help=f"proceed past {MAX_CHUNKS} chunks")
    a = ap.parse_args()
    excl = re.compile(a.exclude) if a.exclude else None

    def excluded(path):
        return bool(DEFAULT_EXCLUDE.search(path) or (excl and excl.search(path)))
    if bool(a.target) == bool(a.diff):
        ap.error("give exactly one of PATH or --diff REF")

    chunks = []
    if a.diff:
        text = subprocess.run(["git", "diff", a.diff], capture_output=True, text=True, check=True).stdout
        if not text.strip():
            sys.exit(f"git diff {a.diff} is empty")
        dropped = [c for c in split_diff(text, a.code_lines) if excluded(c["anchor"])]
        kept = [c for c in split_diff(text, a.code_lines) if not excluded(c["anchor"])]
        if dropped:
            print(f"excluded {len(dropped)} chunk(s) by path filter", file=sys.stderr)
        for c in kept:
            c["type"] = "diff"
            c["risk_tier"] = risk_tier(c["anchor"], c["text"])
            chunks.append(c)
        label = f"diff {a.diff}"
    else:
        if not os.path.exists(a.target):
            sys.exit(f"not found: {a.target}")
        if os.path.isfile(a.target) and is_binary(a.target):
            sys.exit(f"refusing binary file: {a.target}")
        for path in collect_files(a.target):
            if excluded(path) and os.path.isdir(a.target):
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            ext = os.path.splitext(path)[1].lower()
            if ext in CODE_EXT:
                for c in split_code(text, path, a.code_lines):
                    c["type"] = "code"
                    c["risk_tier"] = risk_tier(path, c["text"])
                    chunks.append(c)
            else:
                for c in split_prose(text, a.prose_words):
                    if os.path.isdir(a.target):
                        c["anchor"] = f"{path}: {c['anchor']}"
                    c["type"] = "prose"
                    c["risk_tier"] = "low"
                    chunks.append(c)
        label = a.target

    if len(chunks) > MAX_CHUNKS and not a.allow_large:
        sys.exit(f"{len(chunks)} chunks exceeds {MAX_CHUNKS}. Narrow the target (a subdirectory, a smaller diff range, "
                 f"or --exclude REGEX) or pass --allow-large. A brief over that size is longer than the artifact is worth.")
    os.makedirs(a.out, exist_ok=True)
    inventory = {"target": label, "chunk_count": len(chunks), "chunks": []}
    for i, c in enumerate(chunks, 1):
        cid = f"chunk-{i:02d}"
        tp = os.path.join(a.out, f"{cid}.txt")
        with open(tp, "w", encoding="utf-8") as f:
            f.write(c["text"])
        with open(os.path.join(a.out, f"{cid}.prompt.txt"), "w", encoding="utf-8") as f:
            f.write(PROMPT.format(text_path=os.path.abspath(tp), cid=cid, anchor=c["anchor"], ctype=c["type"],
                                  json_path=os.path.abspath(os.path.join(a.out, f"{cid}.json"))))
        entry = {"id": cid, "type": c["type"], "anchor": c["anchor"], "text_path": tp, "risk_tier": c["risk_tier"], "size": c["size"], "unit": c["unit"]}
        inventory["chunks"].append(entry)
        print(f"{cid}  {c['type']:5}  {c['risk_tier']:4}  {c['size']:5} {c['unit']:5}  {c['anchor']}")
    inv_path = os.path.join(a.out, "inventory.json")
    with open(inv_path, "w") as f:
        json.dump(inventory, f, indent=2)
    print(f"\n{len(chunks)} chunks -> {inv_path}")
    print("mode:", "sequential" if len(chunks) < 4 else "fan-out")


if __name__ == "__main__":
    main()
