#!/usr/bin/env bash
# Start the deck design studio. Runs in the foreground — Ctrl-C stops it.
# Run it from the project root; specs resolve against your current directory.
#
#   <skill>/scripts/studio.sh                     # the only deck under decks/
#   <skill>/scripts/studio.sh <deck-name>         # decks/<deck-name>/<deck-name>-spec.yaml
#   <skill>/scripts/studio.sh path/to/spec.yaml   # any spec by path
#   PORT=4322 <skill>/scripts/studio.sh           # a different port
#
# Nothing is written to disk until you press Save + build in the browser.

set -euo pipefail

SPEC="${1:-}"
if [ -z "$SPEC" ]; then
  # No argument: fine when the project has exactly one deck, ambiguous otherwise.
  # A leading underscore (decks/_archive) marks a directory that is not a deck.
  DECKS=()
  for d in decks/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    case "$name" in _*) continue ;; esac
    DECKS+=("$name")
  done
  if [ ${#DECKS[@]} -eq 1 ]; then
    SPEC="${DECKS[0]}"
  else
    echo "Name a deck. Available:" >&2
    printf '  %s\n' "${DECKS[@]}" >&2
    exit 1
  fi
fi
# A bare deck name is shorthand for that deck's spec.
case "$SPEC" in */*) ;; *) SPEC="decks/$SPEC/$SPEC-spec.yaml" ;; esac

PORT="${PORT:-4321}"
STUDIO="$(cd "$(dirname "$0")" && pwd)/studio.js"

[ -f "$SPEC" ] || { echo "No such spec: $SPEC" >&2; exit 1; }

# A studio left over from an earlier session holds a stale copy of the spec in
# memory, and saving from it would overwrite the current file. Clear it out.
if OLD=$(lsof -tnP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null); then
  echo "Stopping the studio already on port $PORT (pid $OLD)"
  kill $OLD
  sleep 1
fi

URL="http://127.0.0.1:$PORT"
if command -v open >/dev/null 2>&1; then
  ( sleep 2; open "$URL" ) &
elif command -v xdg-open >/dev/null 2>&1; then
  ( sleep 2; xdg-open "$URL" ) &
fi

exec node "$STUDIO" "$SPEC" --port "$PORT"
