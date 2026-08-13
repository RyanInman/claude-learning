#!/usr/bin/env bash
# Smoke-test the generated scripts: --help exits 0, bad args exit nonzero, happy path exits 0.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="$HERE/../changelogs"
fails=0

check() { # check <expected: zero|nonzero> <label> <cmd...>
  local want="$1" label="$2"; shift 2
  "$@" >/dev/null 2>&1
  local rc=$?
  if { [ "$want" = zero ] && [ $rc -eq 0 ]; } || { [ "$want" = nonzero ] && [ $rc -ne 0 ]; }; then
    echo "ok   $label (exit $rc)"
  else
    echo "FAIL $label (exit $rc, wanted $want)"; fails=$((fails+1))
  fi
}

for s in list_changelogs.py count_entries.py; do
  check zero    "$s --help"          python3 "$HERE/$s" --help
  check nonzero "$s no args"         python3 "$HERE/$s"
  check nonzero "$s unknown flag"    python3 "$HERE/$s" "$DIR" --nope
  check nonzero "$s missing dir"     python3 "$HERE/$s" "$HERE/does-not-exist"
  check zero    "$s happy path"      python3 "$HERE/$s" "$DIR"
done

if [ "$fails" -ne 0 ]; then echo "$fails check(s) failed"; exit 1; fi
echo "all checks passed"
