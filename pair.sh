#!/bin/bash
# pair.sh - one-time wireless-debugging pairing for a new phone.
# The phone shows a PAIRING port + 6-digit code under
# Developer options > Wireless debugging > "Pair device with pairing code".
# Usage: pair.sh <pairing-ip> <pairing-port>
# Then paste the 6-digit code when prompted. After this succeeds once,
# the VM's adb key is authorized and future connects use the separate
# CONNECTION port in config.env (no more pairing needed).
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
  echo "paired. Now put the CONNECTION port (main Wireless debugging screen) into config.env as ADB_PORT."
else
  echo "pairing failed."
fi
exit $RC
