#!/usr/bin/env python3
"""
analyze_session.py — Extract review metrics from a Claude Code session transcript.

Claude Code stores each session as a JSONL file (one JSON object per line) under
~/.claude/projects/<encoded-cwd>/<session-id>.jsonl. This script parses that file
and emits a structured metrics summary that a reviewer can map to known session
anti-patterns (context rot, cache misses, tool sprawl, output bloat, etc.).
Subagent transcripts in the sibling <session-id>/subagents/ directory are aggregated
automatically.

The script does only the deterministic, mechanical work: counting, summing,
hashing, and flagging threshold crossings. It does NOT decide what to recommend —
that interpretation lives in references/review-checklist.md so the model can
reason about it. Thresholds here are documented with their rationale so they are
not "voodoo constants."

Usage:
  python analyze_session.py SESSION.jsonl                 # one file
  python analyze_session.py /path/to/dir                  # newest .jsonl in dir
  python analyze_session.py --latest                      # newest session anywhere
  python analyze_session.py SESSION.jsonl --format text   # human-readable summary
  python analyze_session.py SESSION.jsonl --full          # include per-turn trajectory

Output: JSON to stdout (default) or a text summary with --format text.
Diagnostics and warnings go to stderr.

Exit codes:
  0  success
  2  bad arguments / nothing to analyze
  3  file not found
  4  no valid JSONL records parsed (wrong file type?)
"""

import argparse
import json
import os
import sys
import hashlib
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

# --- Documented thresholds (each cites why it matters; see review-checklist.md) ---
# A typical Claude context window. Used only to express peak context as a % of window.
DEFAULT_WINDOW = 200_000
# Context-rot research shows quality degrading well before the window is full;
# ~50k tokens is a commonly observed inflection even on 200k-window models.
CONTEXT_DEGRADE_TOKENS = 50_000
# Practitioner guidance treats >~80% window utilization as the danger zone.
CONTEXT_DANGER_FRAC = 0.80
# Claude Code truncates tool responses at ~25k tokens by default; outputs near or
# past this lose information. We measure characters (~4 chars/token heuristic).
TOOL_OUTPUT_WARN_CHARS = 25_000 * 4
# Agent reliability degrades past roughly 10-15 distinct tools.
TOOL_SPRAWL_COUNT = 15
# Below this cache-hit fraction (on a session with meaningful repeated context),
# the prompt-cache prefix is probably being invalidated.
LOW_CACHE_HIT_FRAC = 0.50
# Prompt-cache default TTL is 5 minutes (refreshed free on each use). A gap
# between assistant turns longer than this guarantees an EXPECTED cache miss
# (idle expiry) as opposed to a warm miss, which indicates prefix instability.
CACHE_TTL_SECONDS = 300


def err(msg):
    print(msg, file=sys.stderr)


def find_latest_session(project_dir=None):
    """Return the most recently modified .jsonl under the Claude projects dir."""
    roots = []
    if project_dir:
        roots.append(Path(project_dir))
    else:
        roots.append(Path.home() / ".claude" / "projects")
    candidates = []
    for root in roots:
        if root.exists():
            candidates.extend(root.rglob("*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_path(path_arg, latest, project_dir):
    if latest:
        p = find_latest_session(project_dir)
        if p is None:
            err("No .jsonl session files found under the Claude projects directory.")
            err("Pass an explicit path, or use --project-dir to point at the folder.")
            sys.exit(3)
        err(f"Using latest session: {p}")
        return p
    if not path_arg:
        err("Provide a path to a .jsonl file or directory, or use --latest.")
        sys.exit(2)
    p = Path(path_arg)
    if not p.exists():
        err(f"Path not found: {p}")
        sys.exit(3)
    if p.is_dir():
        files = sorted(p.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            err(f"No .jsonl files in directory: {p}")
            sys.exit(3)
        err(f"Directory given; using newest .jsonl: {files[0]}")
        return files[0]
    return p


def iter_records(path):
    """Yield parsed JSON objects; count and skip malformed lines."""
    bad = 0
    total = 0
    records = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(obj, dict):
                records.append(obj)
            else:
                # Valid JSON but not a transcript record (stray array/scalar).
                bad += 1
    return records, total, bad


def content_blocks(message):
    """Return content as a list of blocks regardless of string/list shape."""
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return []


def block_text_len(block):
    if not isinstance(block, dict):
        return 0
    if "text" in block and isinstance(block["text"], str):
        return len(block["text"])
    if "thinking" in block and isinstance(block["thinking"], str):
        return len(block["thinking"])
    c = block.get("content")
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(block_text_len(b) for b in c)
    return 0


def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def analyze_subagents(session_path):
    """Aggregate token usage from subagent transcripts.

    Modern Claude Code stores each subagent's transcript in a sibling
    directory: <session-id>/subagents/agent-*.jsonl next to <session-id>.jsonl.
    Older sessions interleaved subagent turns in the main file instead
    (counted separately as counts.sidechain_entries).
    """
    result = {
        "transcript_files": 0,
        "billed_input_total": 0,
        "cache_read_total": 0,
        "cache_creation_total": 0,
        "output_total": 0,
    }
    p = Path(session_path)
    sub_dir = p.parent / p.stem / "subagents"
    if not sub_dir.is_dir():
        return result
    for f in sorted(sub_dir.glob("*.jsonl")):
        records, _total, _bad = iter_records(f)
        result["transcript_files"] += 1
        for r in records:
            if r.get("type") != "assistant":
                continue
            msg = r.get("message") or {}
            usage = msg.get("usage") or {}
            it = usage.get("input_tokens", 0) or 0
            cr = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation_input_tokens", 0) or 0
            result["billed_input_total"] += it + cr + cc
            result["cache_read_total"] += cr
            result["cache_creation_total"] += cc
            result["output_total"] += usage.get("output_tokens", 0) or 0
    return result


def analyze(records):
    m = {
        "session": {},
        "counts": {},
        "tokens": {},
        "cache": {},
        "models": {},
        "tools": {},
        "thinking": {},
        "compaction": {},
        "output": {},
        "subagents": {},
        "latency": {},
        "signals": {},
        "parse": {},
    }

    # session metadata: take first occurrence we see
    meta_keys = ("sessionId", "cwd", "gitBranch", "version")
    for r in records:
        for k in meta_keys:
            if k in r and k not in m["session"] and r[k] not in (None, ""):
                m["session"][k] = r[k]

    timestamps = []
    user_turns = 0
    assistant_turns = 0
    sidechain_entries = 0
    summary_lines = 0
    compact_summaries = 0

    # token trajectory (assistant turns carry usage)
    trajectory = []  # per assistant turn: dict
    sum_input = 0
    sum_cache_read = 0
    sum_cache_create = 0
    sum_output = 0

    models_in_order = []
    tool_calls = Counter()
    tool_call_signatures = Counter()  # name + hashed input -> detect duplicates
    tool_errors = 0
    tool_result_sizes = []
    large_tool_outputs = []  # (approx_chars,) for outputs over warn threshold
    thinking_blocks = 0
    thinking_chars = 0
    assistant_text_chars = []
    turn_durations = []
    prev_assistant_dt = None
    eph_5m = 0
    eph_1h = 0
    eph_seen = False

    for r in records:
        rtype = r.get("type")
        if r.get("isSidechain"):
            sidechain_entries += 1
        ts = r.get("timestamp")
        if ts:
            timestamps.append(ts)
        if r.get("isCompactSummary"):
            compact_summaries += 1

        if rtype == "system" and r.get("subtype") == "turn_duration":
            d = r.get("durationMs")
            if isinstance(d, (int, float)) and d >= 0:
                turn_durations.append(int(d))
            continue

        if rtype == "summary":
            summary_lines += 1
            continue

        msg = r.get("message", {})

        if rtype == "assistant":
            assistant_turns += 1
            model = msg.get("model")
            if model:
                models_in_order.append(model)
            usage = msg.get("usage", {}) if isinstance(msg, dict) else {}
            it = usage.get("input_tokens", 0) or 0
            cr = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation_input_tokens", 0) or 0
            ot = usage.get("output_tokens", 0) or 0
            sum_input += it
            sum_cache_read += cr
            sum_cache_create += cc
            sum_output += ot
            cc_detail = usage.get("cache_creation")
            if isinstance(cc_detail, dict):
                eph_seen = True
                eph_5m += cc_detail.get("ephemeral_5m_input_tokens", 0) or 0
                eph_1h += cc_detail.get("ephemeral_1h_input_tokens", 0) or 0
            cur_dt = parse_iso(ts)
            gap_s = None
            if cur_dt is not None and prev_assistant_dt is not None:
                gap_s = round((cur_dt - prev_assistant_dt).total_seconds(), 1)
            if cur_dt is not None:
                prev_assistant_dt = cur_dt
            context_size = it + cr + cc  # tokens the model saw this turn
            trajectory.append({
                "turn": assistant_turns,
                "model": model,
                "input_tokens": it,
                "cache_read_input_tokens": cr,
                "cache_creation_input_tokens": cc,
                "output_tokens": ot,
                "context_size": context_size,
                "gap_seconds_since_prev": gap_s,
            })
            text_len = 0
            for b in content_blocks(msg):
                bt = b.get("type") if isinstance(b, dict) else None
                if bt == "tool_use":
                    name = b.get("name", "unknown")
                    tool_calls[name] += 1
                    try:
                        sig = name + "|" + hashlib.sha1(
                            json.dumps(b.get("input", {}), sort_keys=True,
                                       default=str).encode()
                        ).hexdigest()
                    except Exception:
                        sig = name + "|?"
                    tool_call_signatures[sig] += 1
                elif bt == "thinking":
                    thinking_blocks += 1
                    thinking_chars += block_text_len(b)
                elif bt == "text":
                    text_len += block_text_len(b)
            if text_len:
                assistant_text_chars.append(text_len)

        elif rtype == "user":
            user_turns += 1
            for b in content_blocks(msg):
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    size = block_text_len(b)
                    tool_result_sizes.append(size)
                    if b.get("is_error"):
                        tool_errors += 1
                    if size >= TOOL_OUTPUT_WARN_CHARS:
                        large_tool_outputs.append(size)

    # --- counts ---
    m["counts"] = {
        "records": len(records),
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "tool_calls": int(sum(tool_calls.values())),
        "tool_results": len(tool_result_sizes),
        "sidechain_entries": sidechain_entries,
    }

    # --- duration ---
    duration_seconds = None
    if len(timestamps) >= 2:
        try:
            t0 = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
            duration_seconds = round((t1 - t0).total_seconds(), 1)
        except Exception:
            pass
    m["session"]["duration_seconds"] = duration_seconds
    m["session"]["first_timestamp"] = timestamps[0] if timestamps else None
    m["session"]["last_timestamp"] = timestamps[-1] if timestamps else None

    # --- tokens ---
    context_sizes = [t["context_size"] for t in trajectory if t["context_size"]]
    peak_context = max(context_sizes) if context_sizes else 0
    total_billed_input = sum_input + sum_cache_read + sum_cache_create
    m["tokens"] = {
        "billed_input_total": total_billed_input,
        "uncached_input_total": sum_input,
        "cache_read_total": sum_cache_read,
        "cache_creation_total": sum_cache_create,
        "output_total": sum_output,
        "peak_context_size": peak_context,
        "peak_context_pct_of_window": round(peak_context / DEFAULT_WINDOW * 100, 1)
        if peak_context else 0.0,
    }

    # --- cache ---
    denom = total_billed_input
    cache_hit_frac = round(sum_cache_read / denom, 3) if denom else 0.0
    cache_miss_turns = 0
    warm_miss_turns = 0
    ttl_gap_miss_turns = 0
    gaps_over_ttl = 0
    for i, t in enumerate(trajectory):
        gap = t.get("gap_seconds_since_prev")
        if gap is not None and gap > CACHE_TTL_SECONDS:
            gaps_over_ttl += 1
        if i == 0:
            continue
        if t["cache_read_input_tokens"] == 0 and t["context_size"] > 1000:
            cache_miss_turns += 1
            if gap is not None and gap > CACHE_TTL_SECONDS:
                ttl_gap_miss_turns += 1
            else:
                warm_miss_turns += 1
    m["cache"] = {
        "cache_hit_fraction": cache_hit_frac,
        "cache_miss_turns": cache_miss_turns,
        "warm_cache_miss_turns": warm_miss_turns,
        "miss_turns_after_ttl_gap": ttl_gap_miss_turns,
        "assistant_gaps_over_ttl": gaps_over_ttl,
        "note": "hit fraction = cache_read / all billed input. Misses after a "
                ">5min idle gap are expected TTL expiry; only warm misses "
                "indicate prefix instability.",
    }
    if eph_seen:
        m["cache"]["cache_creation_by_ttl"] = {
            "ephemeral_5m": eph_5m, "ephemeral_1h": eph_1h,
        }

    # --- models ---
    distinct_models = list(dict.fromkeys(models_in_order))
    switches = []
    for i in range(1, len(models_in_order)):
        if models_in_order[i] != models_in_order[i - 1]:
            switches.append({"at_assistant_turn": i + 1,
                             "from": models_in_order[i - 1],
                             "to": models_in_order[i]})
    m["models"] = {
        "distinct_models": distinct_models,
        "switch_count": len(switches),
        "switches": switches,
    }

    # --- tools ---
    duplicate_calls = {sig.split("|", 1)[0]: c for sig, c in tool_call_signatures.items() if c > 1}
    dup_total = sum(c - 1 for c in tool_call_signatures.values() if c > 1)
    m["tools"] = {
        "distinct_tools": len(tool_calls),
        "by_tool": dict(tool_calls.most_common()),
        "error_count": tool_errors,
        "duplicate_call_total": dup_total,
        "duplicated_tools": duplicate_calls,
        "largest_tool_output_chars": max(tool_result_sizes) if tool_result_sizes else 0,
        "tool_outputs_over_cap": len(large_tool_outputs),
    }

    # --- thinking ---
    m["thinking"] = {
        "thinking_blocks": thinking_blocks,
        "approx_thinking_chars": thinking_chars,
    }

    # --- compaction ---
    m["compaction"] = {
        "summary_lines": summary_lines,
        "compact_summaries": compact_summaries,
        "occurred": bool(summary_lines or compact_summaries),
    }

    # --- latency (from system turn_duration entries; absent on old sessions) ---
    m["latency"] = {
        "turns_measured": len(turn_durations),
        "mean_turn_ms": round(statistics.mean(turn_durations)) if turn_durations else 0,
        "median_turn_ms": round(statistics.median(turn_durations)) if turn_durations else 0,
        "max_turn_ms": max(turn_durations) if turn_durations else 0,
        "slowest_turns_ms": sorted(turn_durations, reverse=True)[:3],
    }

    # --- output ---
    m["output"] = {
        "assistant_text_blocks": len(assistant_text_chars),
        "mean_text_chars": round(statistics.mean(assistant_text_chars), 1)
        if assistant_text_chars else 0,
        "max_text_chars": max(assistant_text_chars) if assistant_text_chars else 0,
    }

    # --- signals (threshold flags; interpretation lives in the checklist) ---
    crossed_degrade = peak_context >= CONTEXT_DEGRADE_TOKENS
    crossed_danger = peak_context >= DEFAULT_WINDOW * CONTEXT_DANGER_FRAC
    m["signals"] = {
        "high_peak_context": crossed_degrade,
        "context_in_danger_zone": crossed_danger,
        "low_cache_hit": (denom > 5000 and cache_hit_frac < LOW_CACHE_HIT_FRAC),
        "model_switching": len(switches) > 0,
        "tool_sprawl": len(tool_calls) > TOOL_SPRAWL_COUNT,
        "duplicate_tool_calls": dup_total > 0,
        "large_tool_outputs": len(large_tool_outputs) > 0,
        "tool_errors_present": tool_errors > 0,
        "compaction_occurred": bool(summary_lines or compact_summaries),
        "heavy_thinking": thinking_chars > 40_000,
    }
    m["signals"]["_thresholds"] = {
        "context_degrade_tokens": CONTEXT_DEGRADE_TOKENS,
        "context_danger_fraction": CONTEXT_DANGER_FRAC,
        "low_cache_hit_fraction": LOW_CACHE_HIT_FRAC,
        "tool_sprawl_count": TOOL_SPRAWL_COUNT,
        "tool_output_warn_chars": TOOL_OUTPUT_WARN_CHARS,
        "window": DEFAULT_WINDOW,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
    }

    m["_trajectory"] = trajectory
    return m


def text_summary(m):
    s = m["session"]
    lines = []
    lines.append("=== SESSION REVIEW METRICS ===")
    lines.append(f"session: {s.get('sessionId', '?')}  cwd: {s.get('cwd', '?')}")
    lines.append(f"version: {s.get('version', '?')}  branch: {s.get('gitBranch', '?')}")
    if s.get("duration_seconds") is not None:
        lines.append(f"duration: {s['duration_seconds']}s")
    c = m["counts"]
    lines.append(f"\nturns: {c['user_turns']} user / {c['assistant_turns']} assistant"
                 f"  tool calls: {c['tool_calls']}  records: {c['records']}")
    t = m["tokens"]
    lines.append(f"\nTOKENS")
    lines.append(f"  peak context: {t['peak_context_size']:,} "
                 f"({t['peak_context_pct_of_window']}% of {DEFAULT_WINDOW:,})")
    lines.append(f"  output total: {t['output_total']:,}")
    ca = m["cache"]
    lines.append(f"\nCACHE  hit fraction: {ca['cache_hit_fraction']}  "
                 f"miss turns: {ca['cache_miss_turns']}")
    mo = m["models"]
    lines.append(f"\nMODELS  {', '.join(mo['distinct_models']) or 'none'}  "
                 f"(switches: {mo['switch_count']})")
    to = m["tools"]
    lines.append(f"\nTOOLS  distinct: {to['distinct_tools']}  errors: {to['error_count']}  "
                 f"duplicates: {to['duplicate_call_total']}  "
                 f"largest output: {to['largest_tool_output_chars']:,} chars")
    if to["by_tool"]:
        top = list(to["by_tool"].items())[:8]
        lines.append("  by tool: " + ", ".join(f"{k}={v}" for k, v in top))
    cp = m["compaction"]
    lines.append(f"\nCOMPACTION  occurred: {cp['occurred']} "
                 f"(summaries: {cp['summary_lines']})")
    lines.append(f"\nSIGNALS (true = worth investigating):")
    for k, v in m["signals"].items():
        if k.startswith("_"):
            continue
        if v:
            lines.append(f"  [!] {k}")
    if not any(v for k, v in m["signals"].items() if not k.startswith("_")):
        lines.append("  (no threshold flags raised)")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="Extract review metrics from a Claude Code session JSONL transcript.")
    ap.add_argument("path", nargs="?", help="Path to a .jsonl file or a directory")
    ap.add_argument("--latest", action="store_true",
                    help="Use the newest session under ~/.claude/projects")
    ap.add_argument("--project-dir",
                    help="Directory to search when using --latest")
    ap.add_argument("--format", choices=["json", "text"], default="json",
                    help="Output format (default: json)")
    ap.add_argument("--full", action="store_true",
                    help="Include the full per-turn token trajectory in JSON output")
    args = ap.parse_args()

    path = resolve_path(args.path, args.latest, args.project_dir)
    records, total, bad = iter_records(path)
    if bad:
        err(f"Skipped {bad} malformed line(s) out of {total}.")
    if not records:
        err("No valid JSONL records parsed. Is this a Claude Code session file?")
        sys.exit(4)

    m = analyze(records)
    m["subagents"] = analyze_subagents(path)
    m["parse"] = {"total_lines": total, "malformed_lines": bad, "source": str(path)}

    if not args.full:
        m.pop("_trajectory", None)

    if args.format == "text":
        print(text_summary(m))
    else:
        print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
