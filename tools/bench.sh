#!/bin/bash
# Times burner's everyday commands against the phone. Run it a few times:
# the first run warms the helpers, later runs show the steady speed.
#   bash tools/bench.sh          # timings only
#   BURNER_TRACE=1 bash tools/bench.sh   # also shows each adb call
cd "$(dirname "$0")/.." || exit 1
t() {
  local s e
  s=$(date +%s%N)
  "$@" >/dev/null 2>"${TMPDIR:-/tmp}/burner-bench.err"
  e=$(date +%s%N)
  printf '%-34s %5.2fs\n' "$*" "$(echo "$e - $s" | bc)"
  [ -n "$BURNER_TRACE" ] && sed 's/^/    /' "${TMPDIR:-/tmp}/burner-bench.err"
}
t python3 bin/burner --help
t bin/burner status
t bin/burner state
t bin/burner dump
t bin/burner dump
t bin/burner shot --out "${TMPDIR:-/tmp}/burner-bench.png"
t bin/burner shot --out "${TMPDIR:-/tmp}/burner-bench.png"
t bin/burner notifications
t bin/burner apps
t bin/burner scroll down
t bin/burner scroll up
