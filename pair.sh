#!/bin/bash
# pair.sh - one-time wireless-debugging pairing for a new phone.
# PREREQUISITE: Tailscale must be ENABLED and connected on the phone BEFORE
# pairing. After a phone reboot, Tailscale does NOT auto-start — the phone
# will show its WiFi IP (192.168.x.x) instead of its tailnet IP (100.x.x.x)
# in the pairing dialog, and the VM cannot reach the WiFi IP reliably.
# Enable Tailscale on the phone first, then the pairing dialog will show
# the 100.x.x.x tailnet IP.
#
# The phone shows a PAIRING port + 6-digit code under
# Developer options > Wireless debugging > "Pair device with pairing code".
# Usage: pair.sh <pairing-ip> <pairing-port>
# Then paste the 6-digit code when prompted. After this succeeds once,
# the VM's adb key is authorized. The rest of setup (adb-auto-enable install,
# WRITE_SECURE_SETTINGS grant, battery exemption, in-app self-pairing) pins
# adbd to the FIXED port 5555 on every boot — set ADB_PORT="5555" in
# config.env once and never touch the random wireless-debugging port again.
# NOTE: Pairing codes expire in ~60-90 seconds. Have the code in hand and
# run this IMMEDIATELY after the phone displays it.
set -u
cd "$(dirname "$0")"
source ./config.env
[ $# -eq 2 ] || { echo "usage: pair.sh <pairing-ip> <pairing-port>"; exit 1; }

ADB=~/workspace/.android-tools/platform-tools/adb
PAIR_LOCAL=15556

# Tunnel the pairing port the same way as the ADB port.
PROXY_HOST="${HTTPS_PROXY#http://}"; PROXY_HOST="${PROXY_HOST#*@}"; PROXY_HOST="${PROXY_HOST%%:*}"
PROXY_AUTH="${HTTPS_PROXY#http://}"; PROXY_AUTH="${PROXY_AUTH%%@*}"
socat "TCP-LISTEN:${PAIR_LOCAL},bind=127.0.0.1,reuseaddr" \
  "PROXY:${PROXY_HOST}:$1:$2,proxyport=3130,proxyauth=${PROXY_AUTH}" &
SOCAT_PID=$!
sleep 1

"$ADB" pair "127.0.0.1:${PAIR_LOCAL}"
RC=$?
kill "$SOCAT_PID" 2>/dev/null
if [ $RC -eq 0 ]; then
  echo "paired. adb-auto-enable setup comes next: install the APK, grant WRITE_SECURE_SETTINGS, exempt from battery optimization, finish its in-app self-pairing, then set ADB_PORT=\"5555\" in config.env."
else
  echo "pairing failed."
fi
exit $RC
