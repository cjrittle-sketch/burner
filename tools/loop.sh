#!/bin/bash
# One round of the speed loop: bench -> verify -> compare with the last round.
#   bash tools/loop.sh            # 3 timed runs
#   bash tools/loop.sh --runs 5
# Saves the bench to run/bench-history.jsonl. Exit 1 if a check failed or a
# command got slower (tools/benchcmp.py decides), so a regression stops the
# loop before it is pushed on top of.
cd "$(dirname "$0")/.." || exit 1
status=0
echo "== bench"
python3 tools/bench.py --save "$@" || status=1
echo
echo "== verify"
python3 tools/verify.py || status=1
echo
echo "== compare with the previous round"
python3 tools/benchcmp.py || status=1
echo
[ $status -eq 0 ] && echo "round OK" || echo "round FAILED: fix before pushing"
exit $status
