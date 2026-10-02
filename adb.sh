#!/bin/bash
# adb.sh - run adb commands against the phone through the Tailscale tunnel.
# Usage: adb.sh <adb args...>
# Ensures the tunnel is up and the device is connected first.
set -u
cd "$(dirname "$0")"
source ./config.env

# adb: $BURNER_WORKSPACE, else this folder (install.sh puts it here), else
# the folder above it (older layout).
for d in "${BURNER_WORKSPACE:-}" "$PWD" "$(dirname "$PWD")"; do
  [ -n "$d" ] && [ -x "$d/.android-tools/platform-tools/adb" ] && { ADB="$d/.android-tools/platform-tools/adb"; break; }
done
ADB="${ADB:-$(command -v adb)}"
TARGET="127.0.0.1:${LOCAL_PORT}"

./tunnel.sh start >/dev/null 2>&1 || { echo "tunnel failed"; exit 1; }

# (Re)connect; harmless if already connected.
"$ADB" connect "$TARGET" >/dev/null 2>&1

STATE=$("$ADB" -s "$TARGET" get-state 2>/dev/null)
if [ "$STATE" != "device" ]; then
  echo "phone not reachable (state: ${STATE:-none}). Is wireless debugging on and Tailscale connected on the phone?"
  exit 1
fi

exec "$ADB" -s "$TARGET" "$@"
