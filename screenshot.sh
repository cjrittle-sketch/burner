#!/bin/bash
# screenshot.sh - capture the phone screen to a PNG file.
# Usage: screenshot.sh [output.png]   (default: shots/shot-<timestamp>.png)
set -u
cd "$(dirname "$0")"
mkdir -p shots
OUT="${1:-shots/shot-$(date +%Y%m%d-%H%M%S).png}"

# Wake the screen first (timeout is 10s; harmless if already awake).
./adb.sh shell "input keyevent 224" >/dev/null 2>&1
sleep 1

if ! ./adb.sh exec-out screencap -p > "$OUT" 2>/dev/null; then
  echo "screenshot failed"
  exit 1
fi
# Validate PNG magic bytes.
if ! head -c 8 "$OUT" | od -An -tx1 | grep -q "89 50 4e 47 0d 0a 1a 0a"; then
  echo "screenshot failed: not a valid PNG"
  rm -f "$OUT"
  exit 1
fi
echo "$OUT"
