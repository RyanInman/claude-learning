#!/usr/bin/env python3
"""
new_manifest.py - Scaffold the smoke-test manifest from a classification, so a
run never has to read smoke_test.py to learn the schema.

Reading a 13 KB script to learn a JSON shape costs those tokens on every apply
run, and re-deriving the shape by hand is where schema mistakes come from. This
writes the skeleton once; the run fills in the expectations, which are the only
part that needs judgment.

Every value the run must supply is written as a "TODO: ..." string, and
smoke_test.py refuses to run a manifest that still contains one -- a scaffold
that let a hollow contract through would be worse than no scaffold.

USAGE
    python3 scripts/new_manifest.py <classification.json> --target <skill-dir>
             --out FILE          <review>/manifest.json
             --fixtures DIR      <review>/fixtures
    All three are required, because inventory.py chooses the review directory at
    run time and a silent default would point at the wrong one.

EXIT CODES
    0  Manifest written.
    1  Nothing to scaffold (no SCRIPT, VALIDATOR, HYBRID, or scripted HOOK rows).
    2  Usage error, unreadable/invalid classification, or bad target.
"""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

NEEDS_SCRIPT = {"SCRIPT", "VALIDATOR", "HYBRID", "HOOK"}  # HOOK only when it carries a proposed_script
# Flags the conventions and this skill's own scripts use without a value.
# Flags that always take a value, checked before the path-like heuristic so
# "--out report.json" is never read as a boolean flag plus a data argument.
VALUE_FLAGS = {"--out", "--review-dir", "--target", "--fixtures", "--timeout",
               "--only", "--config", "--format", "--limit"}
BOOL_FLAGS = {"--json", "--verbose", "--force", "--dry-run", "--review",
              "--no-probe", "--no-backup", "--help", "-h"}
FINDING_WORDS = ("finding", "violation", "problem", "flag", "invalid", "missing",
                 "malformed", "broken", "thin", "unknown")


EXIT_ONE_RE = re.compile(r"(?:^|[\s/,;])1\s*[:=-]?\s*([a-z]+)")


def _kind(exit_spec, klass=None):
    """A script whose exit 1 means "the data has a problem" is a check.

    Only a check needs a bad_data_invocation, because only a check can be
    verified against a failing fixture. VALIDATOR is a check by definition.
    Otherwise the house contract decides: exit 1 documented as anything other
    than a usage error means findings. Finding words are the last fallback,
    so a synonym like "1 outliers" is still a check.
    """
    if klass == "VALIDATOR":
        return "check"
    low = (exit_spec or "").lower()
    m = EXIT_ONE_RE.search(low)
    if m and m.group(1) not in ("usage", "error", "bad"):
        return "check"
    return "check" if any(w in low for w in FINDING_WORDS) else "transform"


def _argv(interface, fixture):
    """Turn a declared interface into argv, pointing it at a fixture.

    The last bare token that is not the interpreter, the script path, a flag,
    or a flag's value is the data argument, so that is what the fixture
    replaces. A token after a value-taking flag such as `--out FILE` is that
    flag's value, never the data argument. When the interface names no data
    argument, the fixture is appended.
    """
    try:
        toks = shlex.split(interface)
    except ValueError:
        toks = interface.split()
    if not toks:
        return ["python3", "TODO: script path", fixture]
    data_idx, prev_flag = None, False
    for i, t in enumerate(toks):
        is_flag = t.startswith("-")
        if (i >= 2 and not is_flag and not prev_flag and not t.endswith(".py")):
            data_idx = i
        # A flag with "=" carries its value inline; a bare flag followed by a
        # non-flag token is assumed to take that token as its value.
        # A flag followed by a path-like token ("/" or "." in it) is boolean;
        # the path is the data argument, not the flag's value.
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        path_like = ("/" in nxt or "." in nxt) and not nxt.startswith("-")
        prev_flag = (is_flag and "=" not in t and
                     (t in VALUE_FLAGS or (t not in BOOL_FLAGS and not path_like)))
    out = list(toks)
    if data_idx is None:
        out.append(fixture)
    else:
        out[data_idx] = fixture
    return out


def scaffold(cls, target, fixtures_root):
    seen, scripts = {}, []
    for st in cls.get("steps", []):
        if st.get("class") not in NEEDS_SCRIPT:
            continue
        ps = st.get("proposed_script") or {}
        name = ps.get("name")
        if not name or name in seen:
            if name:
                seen[name].append(st.get("id"))
            continue
        seen[name] = [st.get("id")]
        stem = Path(name).stem
        good = f"{fixtures_root}/{stem}/good"
        bad = f"{fixtures_root}/{stem}/bad"
        kind = _kind(ps.get("exit"), st.get("class"))
        entry = {
            "path": f"scripts/{name}",
            "kind": kind,
            "invocations": [{
                "argv": _argv(ps.get("interface", ""), good),
                "expect_exit": 0,
                "expect_stdout_contains": "TODO: a string the clean run must print",
            }],
            "bad_invocation": {
                "argv": ["python3", f"scripts/{name}"],
                "expect_exit_nonzero": True,
            },
        }
        if kind == "check":
            entry["bad_data_invocation"] = {
                "argv": _argv(ps.get("interface", ""), bad),
                "expect_exit_nonzero": True,
                "expect_stdout_contains": "TODO: the finding code this fixture must trip",
            }
        scripts.append(entry)
    # `seen` stays out of the manifest: smoke_test.py never reads it, and an
    # unconsumed field invites a reader to think something validates it.
    return {"target_skill": str(target), "scripts": scripts}, seen


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Scaffold a smoke-test manifest from a classification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FIXTURE LAYOUT it expects you to create
    <fixtures-root>/<script-stem>/good/    the passing example
    <fixtures-root>/<script-stem>/bad/     the failing example (check kinds only)

WHAT EACH TODO MUST BECOME
    invocations[].expect_stdout_contains
        a string the CLEAN run must print -- proves the happy path really ran
    bad_data_invocation.expect_stdout_contains
        the finding code the FAILING fixture must trip -- proves the logic
        discriminates, not just that the interface works

Everything else is filled in for you. You do not need to read this script or
smoke_test.py to write the manifest.
""")
    p.add_argument("classification", help="Path to classification.json")
    p.add_argument("--target", required=True, help="Target skill folder")
    p.add_argument("--out", required=True,
                   help="Where to write the manifest")
    p.add_argument("--fixtures", required=True,
                   help="Fixture root recorded in the manifest")
    args = p.parse_args(argv)

    target = Path(args.target)
    if not target.is_dir():
        print(f"error: target is not a directory: {args.target}", file=sys.stderr)
        return 2
    try:
        cls = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"error: cannot read classification: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error: classification is not valid JSON: {e}", file=sys.stderr)
        return 2

    # Absolute, because smoke_test.py runs every command with the TARGET SKILL
    # as cwd while the fixtures live in the working directory. A relative path
    # here resolves against the wrong tree and the first smoke run fails on
    # paths rather than on behaviour -- observed in two independent runs.
    fixtures = str(Path(args.fixtures.rstrip("/")).resolve())
    m, steps_by_script = scaffold(cls, target.resolve(), fixtures)
    if not m["scripts"]:
        print("no SCRIPT, VALIDATOR, HYBRID, or scripted HOOK rows: nothing to scaffold", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2), encoding="utf-8")

    todos = json.dumps(m).count("TODO:")
    print(f"{len(m['scripts'])} scripts -> {out}")
    for e in m["scripts"]:
        ids = steps_by_script[Path(e["path"]).name]
        print(f"  {e['path']:32} {e['kind']:9} steps={','.join(ids)}")
    print(f"\n{todos} TODO values to fill, plus the fixtures themselves under "
          f"{args.fixtures}/<script-stem>/{{good,bad}}/.")
    print("Derive every expectation from what the STEP must catch, never from "
          "what the script prints. smoke_test.py rejects a manifest with TODOs left.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
