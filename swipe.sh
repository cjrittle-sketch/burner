#!/bin/bash
# swipe.sh - swipe from one point to another.
# Usage: swipe.sh <x1> <y1> <x2> <y2> [duration_ms]
set -u
cd "$(dirname "$0")"
[ $# -ge 4 ] || { echo "usage: swipe.sh <x1> <y1> <x2> <y2> [duration_ms]"; exit 1; }
DUR="${5:-300}"
./adb.sh shell "input keyevent 224" >/dev/null 2>&1
sleep 1
./adb.sh shell input swipe "$1" "$2" "$3" "$4" "$DUR"
