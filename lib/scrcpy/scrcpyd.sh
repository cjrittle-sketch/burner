#!/bin/bash
# scrcpyd.sh — launch the scrcpy control-only server on the phone.
# Runs in the foreground: this script's lifetime == server's lifetime.
# Verifies the server jar is on the device (re-pushes if missing) and
# kills any stale server before starting.
set -u
ADB="${ADB:-$HOME/workspace/.android-tools/platform-tools/adb}"
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:15555}"
PORT="${SCRCPY_PORT:-27183}"
JAR_LOCAL="$HOME/workspace/phone-control/lib/scrcpy/scrcpy-server-v4.1"
JAR_REMOTE="/data/local/tmp/scrcpy-server.jar"

# make sure the jar is actually on the device (/data/local/tmp can be cleaned)
SIZE_LOCAL=$(stat -c%s "$JAR_LOCAL" 2>/dev/null || echo 0)
SIZE_REMOTE=$("$ADB" shell stat -c%s "$JAR_REMOTE" 2>/dev/null | tr -d '\r' || echo 0)
if [ "$SIZE_LOCAL" != "$SIZE_REMOTE" ]; then
  "$ADB" push "$JAR_LOCAL" "$JAR_REMOTE" >/dev/null 2>&1
fi

# kill any stale server (pattern in brackets so pkill doesn't match itself)
"$ADB" shell 'pkill -f "[c]om.genymobile.scrcpy.Server"' >/dev/null 2>&1
sleep 0.5

# (re)create the forward; harmless if it already exists
"$ADB" forward --remove "tcp:$PORT" >/dev/null 2>&1
"$ADB" forward "tcp:$PORT" localabstract:scrcpy >/dev/null 2>&1

exec "$ADB" shell CLASSPATH="$JAR_REMOTE" app_process / \
  com.genymobile.scrcpy.Server 4.1 \
  tunnel_forward=true control=true video=false audio=false \
  send_device_meta=false send_dummy_byte=true cleanup=false
