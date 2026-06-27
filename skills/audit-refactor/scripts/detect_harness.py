#!/usr/bin/env python3
"""Detect the test command for a repo so the skill can verify zero regression.

Looks for the common ecosystem markers and emits the command to run plus the
framework name (run_tests.py uses the framework to pick a result parser). It
does not run anything — detection only.

Output JSON:
  {"detected": bool, "command": "pytest", "framework": "pytest",
   "candidates": [{"command", "framework", "why"}], "root": "/abs"}

Exit: 0 detected · 1 nothing found (skill then warns + asks to proceed). The
JSON is printed either way so the caller always has structured detail.
"""

import argparse
import json
import os
import sys


def _exists(root, *names):
    return any(os.path.exists(os.path.join(root, n)) for n in names)


def _read(root, name):
    try:
        with open(os.path.join(root, name), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def detect(root):
    cands = []

    # Node: package.json with a test script. Pick runner by lockfile.
    pkg = _read(root, "package.json")
    if pkg:
        try:
            scripts = json.loads(pkg).get("scripts", {})
        except json.JSONDecodeError:
            scripts = {}
        if "test" in scripts:
            if _exists(root, "pnpm-lock.yaml"):
                runner = "pnpm test"
            elif _exists(root, "yarn.lock"):
                runner = "yarn test"
            else:
                runner = "npm test"
            fw = "jest" if "jest" in scripts.get("test", "") or "jest" in pkg else "node"
            cands.append({"command": runner, "framework": fw, "why": "package.json scripts.test"})

    # Python: pytest if configured, else stdlib unittest if test files exist.
    if _exists(root, "pytest.ini", "tox.ini", "conftest.py") or "pytest" in _read(root, "pyproject.toml"):
        cands.append({"command": "pytest -v --tb=short", "framework": "pytest",
                      "why": "pytest config"})
    import glob as _glob
    if _glob.glob(os.path.join(root, "**", "test_*.py"), recursive=True) or \
       _glob.glob(os.path.join(root, "**", "*_test.py"), recursive=True):
        cands.append({"command": "python3 -m unittest discover -v", "framework": "unittest",
                      "why": "test_*.py / *_test.py files"})

    # Rust, Go.
    if _exists(root, "Cargo.toml"):
        cands.append({"command": "cargo test", "framework": "cargo", "why": "Cargo.toml"})
    if _exists(root, "go.mod"):
        cands.append({"command": "go test ./...", "framework": "go", "why": "go.mod"})

    # Make target.
    mk = _read(root, "Makefile")
    if mk and any(line.startswith("test:") for line in mk.splitlines()):
        cands.append({"command": "make test", "framework": "generic", "why": "Makefile test target"})

    # JVM.
    if _exists(root, "gradlew"):
        cands.append({"command": "./gradlew test", "framework": "generic", "why": "gradlew"})
    elif _exists(root, "pom.xml"):
        cands.append({"command": "mvn test", "framework": "generic", "why": "pom.xml"})

    return cands


def main():
    ap = argparse.ArgumentParser(description="Detect the project's test command.")
    ap.add_argument("root", nargs="?", default=None, help="repo root (default: git toplevel or cwd)")
    args = ap.parse_args()
    root = args.root or os.popen("git rev-parse --show-toplevel 2>/dev/null").read().strip() or os.getcwd()

    cands = detect(root)
    best = cands[0] if cands else None
    out = {
        "detected": bool(best),
        "command": best["command"] if best else None,
        "framework": best["framework"] if best else None,
        "candidates": cands,
        "root": root,
    }
    print(json.dumps(out, indent=2))
    sys.exit(0 if best else 1)


if __name__ == "__main__":
    main()
