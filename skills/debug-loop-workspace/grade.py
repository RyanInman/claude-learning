#!/usr/bin/env python3
"""Mechanical half of eval grading for running-debug-loops.

Checks the artifacts each run left behind: the patched source, the test files,
the git history in the copied fixture, and the response.md text. Prints one
JSON blob per run so a judgment pass only has to cover what code cannot see.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FIXTURES = Path(
    "/Users/admin/claude-learning/skills/debug-loop/evals/fixtures"
)


def sh(cmd, cwd):
    try:
        return subprocess.run(
            cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=120
        )
    except Exception as exc:  # noqa: BLE001
        return subprocess.CompletedProcess(cmd, 1, "", str(exc))


def read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def brief_checks(resp):
    low = resp.lower()
    has_brief = "debug brief" in low
    fields = sum(k in low for k in ("symptom", "repro", "check"))
    hyps = len(re.findall(r"^\s*\d[\.\)]\s", resp, re.M))
    evidence = bool(re.search(r"(passed|failed|=====|\$ )", resp))
    return {
        "brief_heading": has_brief,
        "brief_fields_present": fields,
        "numbered_items": hyps,
        "shows_command_output": evidence,
    }


def git_facts(project):
    log = sh("git log --oneline --reverse", project).stdout.strip().splitlines()
    commits = []
    for line in log:
        sha = line.split()[0]
        files = sh(f"git show --name-only --format= {sha}", project).stdout.split()
        commits.append({"subject": line, "files": files})
    return commits


def test_first(commits):
    """True when some commit after the baseline touches only test files."""
    for c in commits[1:]:
        if c["files"] and all("test" in f for f in c["files"]):
            return True
    return False


def suite(project):
    r = sh("python3 -m pytest tests -q", project)
    return {"exit": r.returncode, "tail": (r.stdout or r.stderr).strip()[-300:]}


def assertions(path):
    return sorted(
        line.strip() for line in read(path).splitlines() if line.strip().startswith("assert")
    )


def grade(eval_dir, cfg):
    out = eval_dir / cfg / "outputs"
    project = out / "project"
    name = eval_dir.name
    res = {"eval": name, "config": cfg}
    if not project.is_dir():
        res["error"] = "no project directory"
        return res

    res.update(brief_checks(read(out / "response.md")))
    commits = git_facts(project)
    res["commit_count"] = len(commits)
    res["committed_test_before_fix"] = test_first(commits)
    res["suite"] = suite(project)

    if "vague-login" in name:
        src = read(project / "sessions.py")
        res["selects_by_version"] = bool(
            re.search(r"(max|sorted)\([^\n]*version", src)
            or re.search(r"key=lambda[^\n]*\[.version.\]", src)
        )
        res["still_selects_by_created_at"] = bool(
            re.search(r"(max|sorted)\([^\n]*created_at", src)
        )
        res["new_test_files"] = [
            p.name for p in (project / "tests").glob("*.py") if p.name != "test_sessions.py"
        ]
        res["test_lines_added"] = len(read(project / "tests/test_sessions.py").splitlines()) - len(
            read(FIXTURES / "expired-sessions/tests/test_sessions.py").splitlines()
        )
    elif "traceback" in name:
        src = read(project / "report.py")
        res["bom_aware_read"] = "utf-8-sig" in src or "\\ufeff" in src or "ufeff" in src
        res["masks_with_get_default"] = bool(re.search(r"row\.get\(\s*['\"]region", src))
        tests = "\n".join(read(p) for p in (project / "tests").rglob("*.py"))
        res["bom_regression_test"] = "utf-8-sig" in tests or "bom" in tests.lower()
    elif "trivial-typo" in name:
        src = read(project / "slug.py")
        fixture_src = read(FIXTURES / "slug-typo/slug.py")
        res["typo_fixed"] = ".strip()" in src and ".stip()" not in src
        res["source_otherwise_unchanged"] = src.replace(".strip()", ".stip()") == fixture_src
        res["tests_unmodified"] = read(project / "tests/test_slug.py") == read(
            FIXTURES / "slug-typo/tests/test_slug.py"
        )
        res["extra_test_files"] = [
            p.name for p in (project / "tests").glob("*.py") if p.name != "test_slug.py"
        ]
        res["response_lines"] = len(read(out / "response.md").splitlines())
    elif "red-tests" in name:
        before = assertions(FIXTURES / "pricing-regression/tests/test_pricing.py")
        after = assertions(project / "tests/test_pricing.py")
        res["assertions_unchanged"] = before == after
        res["assertions_removed_or_edited"] = [a for a in before if a not in after]
        src = read(project / "pricing.py")
        res["uses_decimal_or_cents"] = bool(
            re.search(r"Decimal|ROUND_HALF_UP|cents", src)
        )
        res["still_plain_round_float"] = bool(
            re.search(r"return round\([^\n]*\*", src)
        )
    return res


def main():
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "iteration-1"
    rows = []
    for eval_dir in sorted(base.glob("eval-*")):
        for cfg in ("with_skill", "without_skill", "old_skill"):
            if (eval_dir / cfg).is_dir():
                rows.append(grade(eval_dir, cfg))
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
