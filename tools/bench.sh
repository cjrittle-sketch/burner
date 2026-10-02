#!/bin/bash
# Times burner's everyday commands against the phone. Kept for muscle memory;
# the work is in tools/bench.py (warm-up pass, median of N runs, --save to
# the history that tools/benchcmp.py compares).
#   bash tools/bench.sh                  # timings only
#   bash tools/bench.sh --runs 5 --save
#   BURNER_TRACE=1 bash tools/bench.sh   # also shows each adb call
exec python3 "$(dirname "$0")/bench.py" "$@"
