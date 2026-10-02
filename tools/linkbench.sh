#!/bin/bash
# Times the raw link to the phone, separate from burner itself: how long one
# adb call costs, whether batching several commands in one call helps, and
# what the phone's animation settings are (animations make every screen
# change wait). Read-only.
#   bash tools/linkbench.sh
cd "$(dirname "$0")/.." || exit 1
ADB=$(ls "$PWD"/.android-tools/platform-tools/adb 2>/dev/null || command -v adb)
S=${ANDROID_SERIAL:-127.0.0.1:15555}
t() {
  local label=$1 s e; shift
  s=$(date +%s%N)
  "$@" >/dev/null 2>&1
  e=$(date +%s%N)
  printf '%-34s %6d ms\n' "$label" "$(( (e - s) / 1000000 ))"
}
for i in 1 2 3 4 5; do t "adb shell true (call $i)" "$ADB" -s "$S" shell true; done
t "adb 1 call, 5 commands" "$ADB" -s "$S" shell 'true; true; true; true; true'
t "adb 5 calls, 1 command each" bash -c "for i in 1 2 3 4 5; do '$ADB' -s '$S' shell true; done"
t "adb 5 calls in parallel" bash -c "for i in 1 2 3 4 5; do '$ADB' -s '$S' shell true & done; wait"
t "adb exec-out true" "$ADB" -s "$S" exec-out true
for k in window_animation_scale transition_animation_scale animator_duration_scale; do
  printf '%-34s %s\n' "$k" "$("$ADB" -s "$S" shell settings get global $k 2>/dev/null)"
done
printf 'tunnel hops: '; ps -eo args | grep -c '[s]ocat.*15555'
