#!/bin/bash
# screenshot.sh - capture the phone screen to a PNG file.
# Usage: screenshot.sh [output.png]   (default: shots/shot-<timestamp>.png)
#
# Saves the PNG on the phone and pulls it. Streaming it with
# `adb exec-out screencap -p` takes about 13s through the tunnel for a 1.5MB
# image (small packets); screencap-to-file plus `adb pull` takes about 3s.
set -u
cd "$(dirname "$0")"
mkdir -p shots
OUT="${1:-shots/shot-$(date +%Y%m%d-%H%M%S).png}"
REMOTE=/data/local/tmp/burner-shot.png

# Wake the screen first (timeout is 10s; harmless if already awake).
./adb.sh shell "input keyevent 224" >/dev/null 2>&1
sleep 0.5

ok=0
if ./adb.sh shell "screencap -p $REMOTE" >/dev/null 2>&1 \
   && ./adb.sh pull "$REMOTE" "$OUT" >/dev/null 2>&1; then
  ok=1
fi
./adb.sh shell "rm -f $REMOTE" >/dev/null 2>&1 &

# Fall back to streaming if the file route failed.
if [ "$ok" != 1 ] && ! ./adb.sh exec-out screencap -p > "$OUT" 2>/dev/null; then
  echo "screenshot failed"
  rm -f "$OUT"
  exit 1
fi
# Validate PNG magic bytes.
if ! head -c 8 "$OUT" | od -An -tx1 | grep -q "89 50 4e 47 0d 0a 1a 0a"; then
  echo "screenshot failed: not a valid PNG"
  rm -f "$OUT"
  exit 1
fi
echo "$OUT"
