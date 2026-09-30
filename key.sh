#!/bin/bash
# key.sh - press a hardware/software key.
# Usage: key.sh <name|code>
# Names: back, home, enter, search, del, tab, up, down, left, right,
#        wake, sleep, volup, voldown, app_switch, power, menu.
# Or pass a raw KEYCODE_* / numeric code straight through.
set -u
cd "$(dirname "$0")"
[ $# -eq 1 ] || { echo "usage: key.sh <name|code>"; exit 1; }
case "$1" in
  back)       CODE=4;;
  home)       CODE=3;;
  enter)      CODE=66;;
  search)     CODE=84;;
  del)        CODE=67;;
  tab)        CODE=61;;
  up)         CODE=19;;
  down)       CODE=20;;
  left)       CODE=21;;
  right)      CODE=22;;
  wake)       CODE=224;;
  sleep)      CODE=223;;
  volup)      CODE=24;;
  voldown)    CODE=25;;
  app_switch) CODE=187;;
  power)      CODE=26;;
  menu)       CODE=82;;
  *)          CODE="$1";;
esac
./adb.sh shell input keyevent "$CODE"
