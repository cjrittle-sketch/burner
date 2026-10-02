#!/bin/bash
# Install burner from this checkout into a throwaway HOME, the way the web
# installer lays it out, and check a clean install needs no hand patches.
# No phone needed. Linux or macOS (or WSL); needs network for adb + pip.
#   bash tools/fresh-install-test.sh
# Checks: install.sh succeeds; nothing is written outside the burner folder;
# --help, version and recipes work; doctor reports the missing phone and
# exits non-zero instead of hanging; update recipes leaves user recipes alone.
set -u
SRC="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
export HOME="$T/home"
DEST="$HOME/burner"
mkdir -p "$DEST"
fail=0
ok()  { echo "PASS $*"; }
bad() { echo "FAIL $*"; fail=1; }

# Same file set the release tarball has: tracked files only, no .git.
(cd "$SRC" && git ls-files -z | tar --null -T - -cf -) | (cd "$DEST" && tar -xf -)
: > "$DEST/.burner-web-install"
touch "$T/before"
sleep 1

if (cd "$DEST" && bash install.sh) >"$T/install.log" 2>&1; then
  ok "install.sh"
else
  bad "install.sh failed:"; tail -20 "$T/install.log"
fi

# Anything new under HOME but outside ~/burner? (pip and adb caches allowed.)
stray=$(find "$HOME" -newer "$T/before" -type f 2>/dev/null \
  | grep -v "^$DEST/" | grep -vE "/\.cache/pip/|/\.android/" | head -5)
[ -z "$stray" ] && ok "nothing written outside the burner folder" \
  || bad "wrote outside the burner folder: $stray"

B="$DEST/bin/burner"
"$B" --help >/dev/null 2>&1 && ok "burner --help" || bad "burner --help"
"$B" version >/dev/null 2>&1 && ok "burner version: $("$B" version)" || bad "burner version"
"$B" recipes >/dev/null 2>&1 && ok "burner recipes" || bad "burner recipes"

s=$(date +%s)
if timeout 150 "$B" doctor >"$T/doctor.log" 2>&1; then
  bad "doctor says healthy with no phone"
else
  rc=$?
  if [ $rc -eq 124 ]; then
    bad "doctor hung (150s)"
  elif grep -q Traceback "$T/doctor.log"; then
    bad "doctor crashed:"; tail -5 "$T/doctor.log"
  else
    ok "doctor reports no phone, exit $rc, $(( $(date +%s) - s ))s"
  fi
fi

echo "my-own-flow: steps" > "$DEST/recipes/my-own.burner"
if "$B" update recipes >/dev/null 2>&1; then
  [ -f "$DEST/recipes/my-own.burner" ] && ok "update recipes keeps user recipes" \
    || bad "update recipes deleted a user recipe"
else
  echo "SKIP update recipes (no network to GitHub)"
fi

exit $fail
