#!/bin/bash
# launch.sh - launch an app by package name (default: Amazon shopping app).
# Usage: launch.sh [package.name]
set -u
cd "$(dirname "$0")"
source ./config.env
PKG="${1:-$AMAZON_PKG}"
./adb.sh shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
