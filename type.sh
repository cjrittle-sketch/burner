#!/bin/bash
# type.sh - type text into the focused field.
# Usage: type.sh "some text"
# Notes: `input text` needs spaces as %s; a few shell-special chars are
# escaped. For passwords or exact strings prefer the on-screen keyboard via
# tap/key. Clears nothing; use key.sh KEYCODE_DEL loops or select-all first.
set -u
cd "$(dirname "$0")"
[ $# -eq 1 ] || { echo 'usage: type.sh "text"'; exit 1; }
TEXT="$1"
# Escape for adb shell: backslash, then wrap safely.
ESCAPED=$(printf '%s' "$TEXT" | sed -e 's/\\/\\\\/g' -e 's/ /%s/g' \
  -e 's/&/\\&/g' -e 's/(/\\(/g' -e 's/)/\\)/g' -e 's/|/\\|/g' \
  -e 's/;/\\;/g' -e 's/</\\</g' -e 's/>/\\>/g' -e "s/'/'\\\\''/g" \
  -e 's/"/\\"/g' -e 's/`/\\`/g' -e 's/\$/\\$/g' -e 's/!/\\!/g' -e 's/*/\\*/g')
./adb.sh shell "input text '${ESCAPED}'"
