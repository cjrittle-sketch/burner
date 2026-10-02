#!/bin/bash
# status.sh - show tunnel + device state.
set -u
cd "$(dirname "$0")"
source ./config.env
# adb: $BURNER_WORKSPACE, else this folder (install.sh puts it here), else
# the folder above it (older layout).
for d in "${BURNER_WORKSPACE:-}" "$PWD" "$(dirname "$PWD")"; do
  [ -n "$d" ] && [ -x "$d/.android-tools/platform-tools/adb" ] && { ADB="$d/.android-tools/platform-tools/adb"; break; }
done
ADB="${ADB:-$(command -v adb)}"
./tunnel.sh status 2>&1 | head -1
"$ADB" -s "127.0.0.1:${LOCAL_PORT}" get-state 2>/dev/null \
  && "$ADB" -s "127.0.0.1:${LOCAL_PORT}" shell getprop ro.product.model 2>/dev/null \
  || echo "device: not connected"
