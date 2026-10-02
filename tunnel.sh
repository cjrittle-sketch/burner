#!/bin/bash
# tunnel.sh - TCP tunnel: localhost:LOCAL_PORT -> phone ADB port over Tailscale.
#
# The VM cannot route to the tailnet directly; it reaches tailnet TCP
# services through the runtime's HTTP CONNECT proxy (same host as
# HTTPS_PROXY, port 3130). socat forwards a local listening port through
# that proxy to the phone's wireless-debugging port. A computer on the
# tailnet itself (a Mac, Linux, WSL) has no HTTPS_PROXY and connects
# straight to the phone.
#
# Usage: tunnel.sh [start|stop|status]   (default: start if not running)
set -u
cd "$(dirname "$0")"
source ./config.env

: "${PHONE_TAILSCALE_IP:?PHONE_TAILSCALE_IP not set in config.env}"
: "${ADB_PORT:?ADB_PORT not set in config.env}"

PIDFILE="tunnel.pid"
LOGFILE="tunnel.log"

# Proxy host is the same as HTTPS_PROXY, port 3130 = Tailscale tunnel.
if [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_HOST="${HTTPS_PROXY#http://}"
  PROXY_HOST="${PROXY_HOST#*@}"
  PROXY_HOST="${PROXY_HOST%%:*}"
  PROXY_AUTH="${HTTPS_PROXY#http://}"
  PROXY_AUTH="${PROXY_AUTH%%@*}"
  TO="PROXY:${PROXY_HOST}:${PHONE_TAILSCALE_IP}:${ADB_PORT},proxyport=3130,proxyauth=${PROXY_AUTH}"
else
  TO="TCP:${PHONE_TAILSCALE_IP}:${ADB_PORT}"
fi

tunnel_running() {
  [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

case "${1:-start}" in
  start)
    if tunnel_running; then
      echo "tunnel already running (pid $(cat "$PIDFILE")): 127.0.0.1:$LOCAL_PORT -> $PHONE_TAILSCALE_IP:$ADB_PORT"
      exit 0
    fi
    # A leftover socat (from an earlier run or setup) can still hold the
    # port without a pid file, so the new one fails to bind. Clear it.
    pkill -f "TCP-LISTEN:${LOCAL_PORT}," >/dev/null 2>&1 && sleep 0.5
    # -d -d for logging; fork so each adb connection gets its own tunnel leg.
    socat -d -d \
      "TCP-LISTEN:${LOCAL_PORT},bind=127.0.0.1,reuseaddr,fork" \
      "$TO" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    if tunnel_running; then
      echo "tunnel up: 127.0.0.1:$LOCAL_PORT -> $PHONE_TAILSCALE_IP:$ADB_PORT"
    else
      echo "tunnel failed to start; see $LOGFILE"
      exit 1
    fi
    ;;
  stop)
    if tunnel_running; then
      kill "$(cat "$PIDFILE")" && rm -f "$PIDFILE"
      echo "tunnel stopped"
    else
      echo "tunnel not running"
    fi
    ;;
  status)
    if tunnel_running; then
      echo "tunnel running (pid $(cat "$PIDFILE")): 127.0.0.1:$LOCAL_PORT -> $PHONE_TAILSCALE_IP:$ADB_PORT"
    else
      echo "tunnel not running"
    fi
    ;;
esac
