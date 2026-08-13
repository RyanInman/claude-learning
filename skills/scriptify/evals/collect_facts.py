#!/usr/bin/env python3
"""Collect the mechanical facts a grader must not eyeball.

For every <iteration>/eval-*/<config>/ run directory, write facts.json with:
  - target_tree_diff  : added / removed / modified against fixture-baseline/
  - workspace_extra   : paths under workspace/ outside the target skill folder
  - scripts           : every .py under the target, with its --help exit status
  - skill_md_changed  : plus the unified diff
  - collision         : sha256 of docs-linter/scripts/check_headings.py (eval 6)
  - residue           : moved-manifest path resolution and smoke-test re-run (eval 7)

Usage: python3 collect_facts.py [iteration_dir]
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SMOKE_TEST = Path(__file__).resolve().parent.parent / "scripts" / "smoke_test.py"
CHECK_HEADINGS_BASELINE_SHA = (
    "d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54"
)
EVAL9_TARGET_REL = ".claude-personal/plugins/cache/release-tools/skills/release-notes"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_files(root: Path) -> dict[str, str]:
    """Map every file under root to its sha256, keyed by path relative to root."""
    out = {}
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            p = Path(dirpath) / name
            out[str(p.relative_to(root))] = sha256(p)
    return out


def tree_diff(baseline: Path, target: Path) -> dict:
    b, t = rel_files(baseline), rel_files(target)
    return {
        "added": sorted(set(t) - set(b)),
        "removed": sorted(set(b) - set(t)),
        "modified": sorted(k for k in set(b) & set(t) if b[k] != t[k]),
    }


def run(argv, cwd=None, timeout=30):
    try:
        p = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as exc:  # noqa: BLE001
        return -2, "", f"{type(exc).__name__}: {exc}"


def locate_target(run_dir: Path, eval_id: int, baseline_root: Path):
    """Return (target_dir, baseline_dir) for this run."""
    ws = run_dir / "workspace"
    if eval_id == 9:
        return ws / EVAL9_TARGET_REL, baseline_root / "plugin-cached-release-notes"
    dirs = [d for d in sorted(ws.iterdir()) if d.is_dir()] if ws.is_dir() else []
    if not dirs:
        return None, None
    return dirs[0], baseline_root / dirs[0].name


def script_facts(target: Path, baseline: Path) -> list[dict]:
    base = rel_files(baseline)
    facts = []
    for p in sorted(target.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = str(p.relative_to(target))
        code, out, err = run([sys.executable, str(p), "--help"], cwd=str(target))
        facts.append({
            "path": rel,
            "preexisting": rel in base,
            "help": {
                "exit": code,
                "stdout_len": len(out),
                "stderr_len": len(err),
                "ok": code == 0 and len(out.strip()) > 0,
            },
        })
    return facts


def residue_facts(target: Path) -> dict:
    """Eval 7: the manifest and fixtures must survive inside the target."""
    manifests = [p for p in target.rglob("manifest.json") if "__pycache__" not in p.parts]
    res = {
        "tests_dir_exists": (target / "scripts" / "tests").is_dir(),
        "manifests_found": [str(m.relative_to(target)) for m in manifests],
    }
    if not manifests:
        res["smoke_rerun_exit"] = None
        return res
    manifest = manifests[0]
    res["manifest"] = str(manifest.relative_to(target))
    try:
        data = json.loads(manifest.read_text())
    except Exception as exc:  # noqa: BLE001
        res["manifest_parse_error"] = str(exc)
        return res

    target_skill = Path(data.get("target_skill", str(target)))
    res["manifest_target_skill"] = str(target_skill)
    res["manifest_target_skill_exists"] = target_skill.is_dir()

    unresolved, stale = [], []
    for script in data.get("scripts", []):
        invs = list(script.get("invocations", []))
        for key in ("bad_data_invocation", "bad_invocation"):
            if script.get(key):
                invs.append(script[key])
        for inv in invs:
            cwd = Path(inv.get("cwd", target_skill))
            for tok in inv.get("argv", []):
                if not isinstance(tok, str) or tok.startswith("-"):
                    continue
                # Manifests templatise the skill root as {skill}. Expand it before resolving,
                # because an unexpanded token never exists on disk and reports a false unresolved.
                tok = tok.replace("{skill}", str(target_skill))
                if ".delegation-review" in tok:
                    stale.append(tok)
                if "/" not in tok and not tok.endswith((".py", ".md", ".json")):
                    continue
                cand = Path(tok) if tok.startswith("/") else cwd / tok
                if tok in ("python3", "python") or cand == cwd:
                    continue
                if not cand.exists():
                    unresolved.append(tok)
    res["unresolved_paths"] = sorted(set(unresolved))
    res["stale_delegation_review_paths"] = sorted(set(stale))

    # Run the arm's OWN runner. Firing scriptify's smoke_test.py at a manifest written for a
    # different runner reports exit 2 for a schema mismatch, which reads as a failing baseline
    # when the baseline's own residue is green.
    runner = data.get("runner")
    if runner:
        argv = runner.split()
        res["runner"] = runner
    else:
        argv = [sys.executable, str(SMOKE_TEST), str(manifest)]
        res["runner"] = "scriptify smoke_test.py (manifest declared none)"
    code, out, err = run(argv, cwd=str(target), timeout=300)
    res["smoke_rerun_exit"] = code
    res["smoke_rerun_tail"] = (out + err)[-4000:]
    return res


STEP_RE = re.compile(r"^\s{0,3}(\d{1,3})[.)]\s")


def steps_changed(baseline: Path, target: Path) -> list[str]:
    """Which numbered SKILL.md steps differ, by step number.

    Eval 3's scoped-edit guardrail asks which steps the rewrite touched; a raw
    unified diff makes a human decide that, which is what the guardrail tier
    forbids.
    """
    def by_step(path: Path) -> dict[str, str]:
        out, cur = {}, None
        for line in path.read_text().splitlines():
            m = STEP_RE.match(line)
            if m:
                cur = m.group(1)
                out.setdefault(cur, "")
            if cur:
                out[cur] += line + "\n"
        return out

    b, t = by_step(baseline), by_step(target)
    return sorted(set(b) ^ set(t) | {k for k in set(b) & set(t) if b[k] != t[k]},
                  key=int)


def collect_run(run_dir: Path, eval_id: int, eval_name: str, baseline_root: Path) -> dict:
    target, baseline = locate_target(run_dir, eval_id, baseline_root)
    facts = {
        "eval": f"eval-{eval_id}-{eval_name}",
        "config": run_dir.name,
        "target": str(target) if target else None,
        "target_exists": bool(target and target.is_dir()),
    }
    outputs = run_dir / "outputs"
    facts["outputs_present"] = (
        sorted(p.name for p in outputs.iterdir()) if outputs.is_dir() else []
    )
    if not facts["target_exists"]:
        return facts

    facts["target_tree_diff"] = tree_diff(baseline, target)

    ws = run_dir / "workspace"
    inside = {str(p) for p in [target]}
    extra = []
    for p in sorted(ws.rglob("*")):
        if "__pycache__" in p.parts:
            continue
        if str(p).startswith(str(target)) or any(str(target).startswith(str(p)) for _ in [0]):
            continue
        if p.is_file():
            extra.append(str(p.relative_to(ws)))
    facts["workspace_extra"] = extra
    del inside

    # SKILL.md diff
    b_skill, t_skill = baseline / "SKILL.md", target / "SKILL.md"
    changed = False
    diff = ""
    if b_skill.exists() and t_skill.exists():
        b_lines = b_skill.read_text().splitlines(keepends=True)
        t_lines = t_skill.read_text().splitlines(keepends=True)
        changed = b_lines != t_lines
        diff = "".join(difflib.unified_diff(b_lines, t_lines, "baseline/SKILL.md", "run/SKILL.md"))
    facts["skill_md_changed"] = changed
    facts["skill_md_steps_changed"] = (
        steps_changed(b_skill, t_skill) if b_skill.exists() and t_skill.exists() else None
    )
    facts["skill_md_diff"] = diff

    facts["scripts"] = script_facts(target, baseline)
    new = [s for s in facts["scripts"] if not s["preexisting"]]
    facts["new_script_count"] = len(new)
    facts["new_scripts_all_help_ok"] = all(s["help"]["ok"] for s in new) if new else None

    if eval_id == 6:
        ch = target / "scripts" / "check_headings.py"
        facts["collision"] = {
            "check_headings_exists": ch.exists(),
            "sha256": sha256(ch) if ch.exists() else None,
            "byte_identical_to_baseline": (
                sha256(ch) == CHECK_HEADINGS_BASELINE_SHA if ch.exists() else False
            ),
        }
    if eval_id == 7:
        facts["residue"] = residue_facts(target)
    return facts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iteration_dir", nargs="?", default=str(Path(__file__).parent))
    args = ap.parse_args()
    iteration = Path(args.iteration_dir).resolve()
    baseline_root = iteration / "fixture-baseline"

    written = 0
    for eval_dir in sorted(iteration.glob("eval-*")):
        _, eval_id, eval_name = eval_dir.name.split("-", 2)
        for cfg in ("with_skill", "without_skill"):
            run_dir = eval_dir / cfg
            if not run_dir.is_dir():
                continue
            facts = collect_run(run_dir, int(eval_id), eval_name, baseline_root)
            (run_dir / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")
            written += 1
            d = facts.get("target_tree_diff", {})
            print(
                f"{eval_dir.name}/{cfg}: +{len(d.get('added', []))} "
                f"~{len(d.get('modified', []))} -{len(d.get('removed', []))} "
                f"outputs={facts['outputs_present']}"
            )
    if not written:
        print(f"error: no eval-*/{{with,without}}_skill run dirs under {iteration}; "
              f"pass the iteration directory as an argument", file=sys.stderr)
        return 2
    print(f"\nwrote {written} facts.json files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
