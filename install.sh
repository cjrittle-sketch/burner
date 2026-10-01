#!/usr/bin/env bash
# install.sh - one-command burner setup. Idempotent, Linux + macOS.
# Writes nothing outside this repo. No sudo, no system-wide changes.
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

die() { echo "install.sh: ERROR: $*" >&2; exit 1; }
info() { echo "install.sh: $*"; }

# --- 1. python3 >= 3.10 -------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 not found. Install Python 3.10+ first."
PYVER="$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
PYMAJOR="$(python3 -c 'import sys; print(sys.version_info.major)')"
PYMINOR="$(python3 -c 'import sys; print(sys.version_info.minor)')"
[ "$PYMAJOR" -gt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -ge 10 ]; } \
  || die "python3 is $PYVER; burner needs 3.10+."
info "python3 $PYVER OK"

# --- 2. pip -------------------------------------------------------------------
if ! python3 -m pip --version >/dev/null 2>&1; then
  info "pip missing, bootstrapping with ensurepip..."
  python3 -m ensurepip --upgrade >/dev/null 2>&1 \
    || die "could not bootstrap pip. Install pip for your python3 and re-run."
fi
info "pip OK"

# --- 3. adb -------------------------------------------------------------------
# bin/burner looks for adb at $BURNER_WORKSPACE/.android-tools/platform-tools/adb
# (BURNER_WORKSPACE defaults to the repo's parent dir, so we install repo-local
# and export BURNER_WORKSPACE in the next steps below).
ATOOLS="$ROOT/.android-tools/platform-tools"
ADB_BIN="$ATOOLS/adb"

if [ -x "$ADB_BIN" ]; then
  info "adb already present at $ADB_BIN"
elif command -v adb >/dev/null 2>&1; then
  SYS_ADB="$(command -v adb)"
  info "found adb on PATH ($SYS_ADB); linking into $ATOOLS"
  mkdir -p "$ATOOLS" || die "cannot create $ATOOLS"
  ln -sf "$SYS_ADB" "$ADB_BIN" || die "cannot link adb"
else
  OS="$(uname -s)"
  case "$OS" in
    Linux)  PT_URL="https://dl.google.com/android/repository/platform-tools-latest-linux.zip" ;;
    Darwin) PT_URL="https://dl.google.com/android/repository/platform-tools-latest-darwin.zip" ;;
    *) die "unsupported OS: $OS (Linux and macOS only)" ;;
  esac
  command -v unzip >/dev/null 2>&1 || die "unzip not found. Install unzip and re-run."
  if command -v curl >/dev/null 2>&1; then
    FETCH="curl -fsSL -o"
  elif command -v wget >/dev/null 2>&1; then
    FETCH="wget -q -O"
  else
    die "need curl or wget to download platform-tools."
  fi
  info "downloading platform-tools for $OS..."
  mkdir -p "$ROOT/.android-tools" || die "cannot create $ROOT/.android-tools"
  TMPZIP="$(mktemp /tmp/platform-tools-XXXXXX.zip)"
  $FETCH "$TMPZIP" "$PT_URL" || { rm -f "$TMPZIP"; die "download failed: $PT_URL"; }
  unzip -q -o "$TMPZIP" -d "$ROOT/.android-tools" || { rm -f "$TMPZIP"; die "unzip failed"; }
  rm -f "$TMPZIP"
  [ -x "$ADB_BIN" ] || die "adb not found after unzip (expected $ADB_BIN)"
  info "adb installed at $ADB_BIN"
fi
"$ADB_BIN" version >/dev/null 2>&1 || die "adb at $ADB_BIN is not runnable"

# --- 4. venv + uiautomator2 ----------------------------------------------------
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  info "creating .venv..."
  python3 -m venv "$ROOT/.venv" || die "venv creation failed"
fi
info "installing uiautomator2 into .venv (may take a minute)..."
"$ROOT/.venv/bin/python" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
"$ROOT/.venv/bin/python" -m pip install --quiet uiautomator2 \
  || die "pip install uiautomator2 failed (check network access)"
info "uiautomator2 OK"

# --- 5. config.env --------------------------------------------------------------
if [ -f "$ROOT/config.env" ]; then
  info "config.env exists, leaving it untouched"
else
  [ -f "$ROOT/config.env.example" ] || die "config.env.example missing; cannot create config.env"
  cp "$ROOT/config.env.example" "$ROOT/config.env" || die "cannot copy config.env.example"
  info "created config.env from config.env.example (fill in your phone's details)"
fi

# --- 6. executable bit -----------------------------------------------------------
chmod +x "$ROOT/bin/burner" || die "cannot chmod bin/burner"
info "bin/burner is executable"

# --- next steps ------------------------------------------------------------------
cat <<EOF

burner installed. Next steps:

  1. export BURNER_WORKSPACE="$ROOT"
     export PATH="$ROOT/bin:\$PATH"
     (add both lines to your shell rc to make them permanent)

  2. Pair your phone: on the phone, enable Developer options, turn on
     Wireless debugging, tap "Pair device with pairing code", and hand the
     IP + pairing port + 6-digit code to your agent for the one-time pair
     (turn Tailscale on first so the dialog shows the tailnet IP).

  3. Your agent installs adb-auto-enable (re-enables ADB on every boot,
     fixed port 5555). Put ADB_PORT="5555" in config.env, then run:
       burner doctor

See SKILL.md for the agent guide and README.md for full docs.
EOF
