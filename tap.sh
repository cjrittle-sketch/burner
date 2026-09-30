#!/bin/bash
# tap.sh - tap a screen coordinate.
# Usage: tap.sh <x> <y>
set -u
cd "$(dirname "$0")"
[ $# -eq 2 ] || { echo "usage: tap.sh <x> <y>"; exit 1; }
./adb.sh shell "input keyevent 224" >/dev/null 2>&1
sleep 1
./adb.sh shell input tap "$1" "$2"
