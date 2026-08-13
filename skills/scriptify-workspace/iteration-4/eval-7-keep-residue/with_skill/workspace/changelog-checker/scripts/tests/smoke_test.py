#!/usr/bin/env python3
"""
smoke_test.py - Verify generated scripts are agent-callable, driven by a
manifest of declared invocations.

The manifest is written by the agent during the contract-first step, BEFORE
the scripts exist, from the target step's semantics -- so the expectations are
not derived from the script's own output (no self-grading).

ALL relative paths in argv and cwd resolve against target_skill (scripts run
with cwd=target_skill by default -- see "cwd" below). `.delegation-review/`
lives in the working directory the agent is running in, which is usually a
DIFFERENT directory from target_skill -- so fixture paths under
`.delegation-review/` must be given as ABSOLUTE paths in the manifest, not
relative ones.

`{skill}` in any argv token or cwd expands to target_skill. Use it for fixture
paths once the fixtures live inside the skill (the keep-residue layout).

A manifest at <skill>/scripts/tests/manifest.json takes its target_skill from
its own location, overriding whatever the file records and printing a note when
the two differ. So a kept residue relocates with ZERO edits: copy or install
the skill anywhere and the manifest still tests the copy you are holding. That
removes the false green at the source rather than detecting it afterwards --
the original copy usually still exists, which is what made a stale absolute
path go green while testing the wrong tree.

MANIFEST SCHEMA (.delegation-review/manifest.json)
{
  "target_skill": "/abs/path/to/target-skill",
  "scripts": [
    {
      "path": "scripts/check_headings.py",   // relative to target_skill
      "kind": "check",                       // "check" | "transform".
                                             // "check" (validates/flags data)
                                             // REQUIRES bad_data_invocation.
      "invocations": [                       // happy-path runs
        {"argv": ["python3", "scripts/check_headings.py",
                  "/abs/path/to/workdir/.delegation-review/fixtures/check_headings/changelogs-good",
                  "--json"],
         // "cwd": (optional, default target_skill; if set, argv and data paths
         //         resolve against it, not target_skill -- only use when the
         //         script itself must run from a specific directory)
         "expect_exit": 0,
         "expect_stdout_json": true,         // optional
         "expect_stdout_contains": "[]"}     // optional
      ],
      "bad_data_invocation": {               // run against the FAILING fixture;
                                             // proves the logic discriminates,
                                             // not just that the interface works
        "argv": ["python3", "scripts/check_headings.py",
                 "/abs/path/to/workdir/.delegation-review/fixtures/check_headings/changelogs-bad",
                 "--json"],
        "expect_exit_nonzero": true,
        "expect_stdout_contains": "missing_version_header"},
      "bad_invocation": {                    // bad ARGS: must exit nonzero AND
                                             // write something to stderr
        "argv": ["python3", "scripts/check_headings.py"],
        "expect_exit_nonzero": true}
    }
  ]
}

CHECKS PER SCRIPT (each a named PASS/FAIL line)
    exists          file present under target_skill
    help            `python3 <script> --help` exits 0 with non-empty usage
    fixture-run[i]  each declared invocation matches its expectations
    bad-data        the failing fixture produces the declared finding
    bad-args        the bad invocation exits nonzero AND writes to stderr
    codes-distinct  a data finding and a usage error return DIFFERENT codes
                    (only when the script declares both)

Interactive scripts surface as FAIL: stdin is closed (input() raises
EOFError -> unexpected exit code) and every run has a timeout (a /dev/tty
reader hangs -> reason "interactive-or-hung").

USAGE
    python3 scripts/smoke_test.py <manifest.json> [--timeout SECS] [--only NAME] [--json]

EXIT CODES
    0  All checks pass.
    1  One or more checks failed.
    2  Manifest missing/unreadable/schema-invalid (message names the field).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _rehome_residue(m, manifest_path):
    """Point a kept manifest at the skill folder holding it.

    A kept manifest lives at <skill>/scripts/tests/manifest.json. Its recorded
    target_skill is absolute and does not follow when the skill is copied or
    installed elsewhere, and the original usually still exists — so a stale
    path silently tests the copy you are not holding. Deriving the target from
    the manifest's own location makes relocation need zero edits and removes
    the false green outright, which beats detecting the mismatch after the
    fact. Returns (target, note_or_None).
    """
    mp = Path(manifest_path).resolve()
    declared = m.get("target_skill")
    if mp.parent.name != "tests" or mp.parent.parent.name != "scripts":
        return declared, None
    holding = str(mp.parent.parent.parent)
    if declared and Path(declared).resolve() != Path(holding):
        return holding, (f"residue manifest sits in {holding}; using that as "
                         f"target_skill instead of the recorded "
                         f"{Path(declared).resolve()} (the skill was moved).")
    return holding, None


def _todo_errors(m):
    """Refuse a scaffold whose expectations were never filled in.

    new_manifest.py writes every value the run must supply as a "TODO: ..."
    string. Running such a manifest would assert nothing while reporting PASS,
    which is worse than having no manifest at all.
    """
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and node.startswith("TODO:"):
            found.append(f"{path.lstrip('.')} is still {node!r}")

    walk(m, "")
    return found


def _schema_errors(m):
    errs = []
    if not isinstance(m, dict):
        return ["manifest root must be a JSON object"]
    errs.extend(_todo_errors(m))
    tgt = m.get("target_skill")
    if not tgt:
        errs.append("missing field: target_skill")
    elif not Path(tgt).is_dir():
        errs.append(f"target_skill is not a directory: {tgt}")
    scripts = m.get("scripts")
    if not isinstance(scripts, list) or not scripts:
        errs.append("missing or empty field: scripts")
        return errs
    for i, s in enumerate(scripts):
        w = f"scripts[{i}]"
        if not s.get("path"):
            errs.append(f"{w}: missing field: path")
        kind = s.get("kind")
        if kind not in ("check", "transform"):
            errs.append(f"{w}: kind must be 'check' or 'transform', got {kind!r}")
        if not s.get("invocations"):
            errs.append(f"{w}: missing or empty field: invocations")
        if kind == "check" and not s.get("bad_data_invocation"):
            errs.append(f"{w}: kind 'check' requires bad_data_invocation "
                        "(a run against the failing fixture)")
        if not s.get("bad_invocation"):
            errs.append(f"{w}: missing field: bad_invocation")
        bd = s.get("bad_data_invocation")
        if bd and not bd.get("argv"):
            errs.append(f"{w}.bad_data_invocation: missing field: argv")
        bi = s.get("bad_invocation")
        if bi and not bi.get("argv"):
            errs.append(f"{w}.bad_invocation: missing field: argv")
        for j, inv in enumerate(s.get("invocations") or []):
            if not inv.get("argv"):
                errs.append(f"{w}.invocations[{j}]: missing field: argv")
    return errs


def _run(argv, cwd, timeout):
    """Return (exit_code, stdout, stderr, hard_failure_reason_or_None)."""
    try:
        r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr, None
    except subprocess.TimeoutExpired:
        return None, "", "", "interactive-or-hung"
    except (FileNotFoundError, PermissionError, NotADirectoryError) as e:
        return None, "", "", f"exec-failed: {e}"


def _expand(argv, base):
    """Expand {skill} to target_skill in every argv token.

    Fixture paths must survive the skill folder moving. Writing them with
    {skill} makes relocation a one-field edit (target_skill) instead of one
    edit per path, and a missed path then fails loudly rather than silently
    reading the original copy's fixtures.
    """
    return [t.replace("{skill}", str(base)) if isinstance(t, str) else t
            for t in argv]


def _resolve_cwd(spec, base):
    cwd = (spec.get("cwd") or ".").replace("{skill}", str(base))
    p = Path(cwd)
    return str(p if p.is_absolute() else (base / p))


def _expectations(spec, code, out, want_nonzero):
    if want_nonzero or spec.get("expect_exit_nonzero"):
        if code == 0:
            return "expected nonzero exit, got 0"
    elif "expect_exit" in spec and code != spec["expect_exit"]:
        return f"expected exit {spec['expect_exit']}, got {code}"
    if spec.get("expect_stdout_json"):
        try:
            json.loads(out)
        except ValueError:
            return "stdout is not valid JSON"
    sub = spec.get("expect_stdout_contains")
    if sub and sub not in out:
        return f"stdout missing expected substring: {sub!r}"
    return ""


def run_checks(m, timeout, only=None):
    base = Path(m["target_skill"])
    results = []

    def add(script, check, ok, reason="", cmd="", code=None, stderr=""):
        results.append({"script": script, "check": check,
                        "status": "PASS" if ok else "FAIL", "reason": reason,
                        "cmd": cmd, "exit": code,
                        "stderr_head": "\n".join((stderr or "").splitlines()[:10])})

    for s in m["scripts"]:
        name = s["path"]
        if only and only not in name:
            continue
        path = base / name
        ok = path.is_file()
        add(name, "exists", ok, "" if ok else f"not found: {path}")
        if not ok:
            continue

        argv = [sys.executable, str(path), "--help"]
        code, out, err, hard = _run(argv, str(base), timeout)
        ok = hard is None and code == 0 and bool(out.strip())
        add(name, "help", ok,
            hard or ("" if ok else f"--help exit={code}, usage-empty={not out.strip()}"),
            " ".join(argv), code, err)

        for j, inv in enumerate(s["invocations"]):
            code, out, err, hard = _run(_expand(inv["argv"], base),
                                        _resolve_cwd(inv, base), timeout)
            reason = hard or _expectations(inv, code, out, want_nonzero=False)
            add(name, f"fixture-run[{j}]", not reason, reason,
                " ".join(inv["argv"]), code, err)

        bd = s.get("bad_data_invocation")
        data_code = None
        if bd:
            code, out, err, hard = _run(_expand(bd["argv"], base),
                                    _resolve_cwd(bd, base), timeout)
            reason = hard or _expectations(bd, code, out, want_nonzero=True)
            data_code = code
            add(name, "bad-data", not reason, reason, " ".join(bd["argv"]), code, err)

        bi = s["bad_invocation"]
        code, out, err, hard = _run(_expand(bi["argv"], base),
                                _resolve_cwd(bi, base), timeout)
        ok = hard is None and code not in (0, None) and bool(err.strip())
        add(name, "bad-args", ok,
            hard or ("" if ok else
                     f"exit={code} (must be nonzero), stderr-empty={not (err or '').strip()}"),
            " ".join(bi["argv"]), code, err)
        usage_code = code

        # Both of the checks above only require "nonzero", so a script that
        # returns the same code for a data finding and a usage error passes
        # them both -- and the caller can then no longer tell "the data has a
        # problem" from "the script has a problem", which is exactly what
        # script-conventions.md forbids and what Step 8's exit-code branching
        # depends on. Compare them.
        if data_code is not None and usage_code is not None:
            distinct = data_code != usage_code
            add(name, "codes-distinct", distinct,
                "" if distinct else
                f"a data finding and a usage error both exit {data_code}; "
                f"split them (house style: 1 findings, 2 usage)",
                f"bad-data exit={data_code} vs bad-args exit={usage_code}")
    return results


def render(results):
    lines = []
    for r in results:
        lines.append(f"{r['status']}  {r['script']}  {r['check']}")
        if r["status"] == "FAIL":
            lines.append(f"      reason : {r['reason']}")
            if r["cmd"]:
                lines.append(f"      cmd    : {r['cmd']}  (exit {r['exit']})")
            if r["stderr_head"]:
                for l in r["stderr_head"].splitlines():
                    lines.append(f"      stderr | {l}")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    lines.append(f"\n{len(results) - n_fail}/{len(results)} checks passed")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Smoke-test generated scripts against a declared manifest.")
    parser.add_argument("manifest", help="Path to manifest.json")
    parser.add_argument("--timeout", type=float, default=20.0,
                        help="Per-run timeout in seconds (default 20)")
    parser.add_argument("--only", help="Only test scripts whose path contains NAME")
    parser.add_argument("--json", action="store_true",
                        help="Emit structured results instead of the table")
    args = parser.parse_args(argv)

    try:
        m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error: manifest is not valid JSON: {e}", file=sys.stderr)
        return 2

    target, note = _rehome_residue(m, args.manifest)
    if target:
        m["target_skill"] = target
    if note:
        print(f"note: {note}", file=sys.stderr)

    errs = _schema_errors(m)
    if errs:
        for e in errs:
            print(f"manifest invalid: {e}", file=sys.stderr)
        return 2

    results = run_checks(m, args.timeout, args.only)
    if not results and args.only:
        print(f"error: --only {args.only!r} matched no scripts in manifest", file=sys.stderr)
        return 2
    print(json.dumps(results, indent=2) if args.json else render(results))
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
