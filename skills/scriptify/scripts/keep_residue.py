#!/usr/bin/env python3
"""
keep_residue.py - Move the verification residue into the target skill and prove
it still works there, including after the skill is moved again.

The steps are deterministic: relocate fixtures and manifest, vendor
smoke_test.py, rewrite fixture paths, re-run, then re-run from a copy. Prose
re-derivation of this procedure has shipped a broken residue twice in recorded
runs -- once leaving stale absolute paths that reported PASS while testing the
original tree. A script does it the same way every time.

The last check is the one that matters: the residue is copied to a scratch
directory and run there untouched. That is what the user asked for when they
said they want to re-run the checks later, and it is the property a stale
absolute path breaks silently.

USAGE
    python3 scripts/keep_residue.py <target-dir> [--review-dir DIR] [--timeout S]
             [--force]
             --review-dir  default .delegation-review
             --timeout     per-check timeout passed to smoke_test.py
             --force       replace an existing scripts/tests/fixtures/

EXIT CODES
    0  Residue installed, green in place and green from a relocated copy.
    1  Residue installed but a verification run failed (details on stderr).
    2  Usage error, or the target/review directory is missing what is needed,
       or scripts/tests/ already holds a fixtures/, manifest.json, or
       smoke_test.py and --force was not passed.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SMOKE = Path(__file__).resolve().parent / "smoke_test.py"


def _rewrite_paths(manifest, old_roots):
    """Point every fixture path at the residue's new home.

    `{skill}` expands to target_skill at run time, and a manifest under
    scripts/tests/ derives target_skill from its own location, so the rewritten
    manifest survives any later move with no further edits.

    Rewrite by path containment, not string replacement. A relative root like
    ".delegation-review/fixtures" is a substring of the absolute path that
    names it, so a plain replace leaves the leading directories behind and
    produces "/tmp/run/{skill}/scripts/..." -- a path that silently resolves
    nowhere. Resolving both sides also settles the macOS /tmp vs /private/tmp
    spelling for free.
    """
    new_root = "{skill}/scripts/tests/fixtures"
    roots = {Path(r).resolve() for r in old_roots}
    n = [0]

    def fix(tok):
        if not isinstance(tok, str) or tok.startswith("-"):
            return tok
        try:
            resolved = Path(tok).resolve()
        except OSError:
            return tok
        for root in roots:
            try:
                rel = resolved.relative_to(root)
            except ValueError:
                continue
            n[0] += 1
            return f"{new_root}/{rel.as_posix()}" if rel.parts else new_root
        return tok

    for s in manifest.get("scripts", []):
        for inv in list(s.get("invocations") or []) + [
                s.get("bad_data_invocation"), s.get("bad_invocation")]:
            if inv and inv.get("argv"):
                inv["argv"] = [fix(t) for t in inv["argv"]]
            if inv and inv.get("cwd"):
                inv["cwd"] = fix(inv["cwd"])
    return n[0]


def _run_smoke(manifest_path, timeout):
    r = subprocess.run([sys.executable, str(SMOKE), str(manifest_path),
                        "--timeout", str(timeout)],
                       capture_output=True, text=True)
    # The tally is the last line of stdout; stderr carries notes that would
    # otherwise be mistaken for the result.
    tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1:]
    return r.returncode, tail or [r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""]


def install(target, review_dir, timeout, force=False):
    tests = target / "scripts" / "tests"
    src_fixtures = review_dir / "fixtures"
    src_manifest = review_dir / "manifest.json"
    if not src_manifest.is_file():
        return 2, f"no manifest at {src_manifest}"
    if not src_fixtures.is_dir():
        return 2, f"no fixtures at {src_fixtures}"

    clashes = [p for p in (tests / "fixtures", tests / "manifest.json",
                           tests / "smoke_test.py") if p.exists()]
    if clashes and not force:
        return 2, (f"{tests} already holds "
                   f"{', '.join(p.name for p in clashes)}; it may be the "
                   f"target's own. Re-run with --force to replace it.")
    tests.mkdir(parents=True, exist_ok=True)
    if (tests / "fixtures").exists():
        shutil.rmtree(tests / "fixtures")
    shutil.copytree(src_fixtures, tests / "fixtures")
    shutil.copy2(SMOKE, tests / "smoke_test.py")

    manifest = json.loads(src_manifest.read_text(encoding="utf-8"))
    rewritten = _rewrite_paths(manifest, {src_fixtures, src_fixtures.resolve()})
    manifest["target_skill"] = str(target.resolve())
    (tests / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                         encoding="utf-8")
    print(f"residue -> {tests}  ({rewritten} fixture paths rewritten)")

    code, tail = _run_smoke(tests / "manifest.json", timeout)
    print(f"in place: {tail[0]}")
    if code != 0:
        return 1, f"the moved residue is not green in place (exit {code})"

    # The point of keeping residue is that the user can re-run it later, which
    # means after the skill has been copied or installed somewhere else.
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / target.name
        shutil.copytree(target, copy)
        code, tail = _run_smoke(copy / "scripts" / "tests" / "manifest.json", timeout)
        print(f"from a relocated copy: {tail[0]}")
        if code != 0:
            return 1, (f"the residue is not green from a relocated copy "
                       f"(exit {code}); it would not survive being installed "
                       f"elsewhere")
    return 0, None


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Install and verify the keep-residue test suite.")
    p.add_argument("target", help="Target skill folder")
    p.add_argument("--review-dir", default=".delegation-review",
                   help="Where fixtures/ and manifest.json currently live")
    p.add_argument("--timeout", type=float, default=20.0,
                   help="Per-check timeout for smoke_test.py (default 20)")
    p.add_argument("--force", action="store_true",
                   help="Replace an existing scripts/tests/fixtures/ directory")
    args = p.parse_args(argv)

    target, review = Path(args.target), Path(args.review_dir)
    if not target.is_dir():
        print(f"error: target is not a directory: {args.target}", file=sys.stderr)
        return 2
    if not review.is_dir():
        print(f"error: review dir is not a directory: {args.review_dir}",
              file=sys.stderr)
        return 2
    if not SMOKE.is_file():
        print(f"error: smoke_test.py not found beside this script", file=sys.stderr)
        return 2

    code, err = install(target, review, args.timeout, args.force)
    if err:
        print(f"error: {err}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
