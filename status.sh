#!/bin/bash
# status.sh - show tunnel + device state.
set -u
cd "$(dirname "$0")"
source ./config.env
ADB=~/workspace/.android-tools/platform-tools/adb
./tunnel.sh status 2>&1 | head -1
"$ADB" -s "127.0.0.1:${LOCAL_PORT}" get-state 2>/dev/null \
  && "$ADB" -s "127.0.0.1:${LOCAL_PORT}" shell getprop ro.product.model 2>/dev/null \
  || echo "device: not connected"
