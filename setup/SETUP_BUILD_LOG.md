# Burner guided setup build log

## 2026-10-01 ~00:00 - kickoff
- Task: guided human setup - setup/ screenshots, `pc setup` wizard, docs, tests.
- Constraints: no wireless-debugging toggle off, no reboot, no BedJet app touches.
- Phone live at 127.0.0.1:15555 (tunnel). BedJet routine running tonight.

## Screenshot capture (in progress)

## Screenshots captured so far (raw, in shots/)
- shot-20261001-045501.png: Tailscale connected (CROP NEEDED: shows email + device list)
- shot-20261001-050127.png: About phone top (has Google account email, may skip)
- shot-20261001-050138.png: About phone bottom w/ Build number BP4A.251205.006 (CROP to Build number row only: IMEIs visible)
- shot-20261001-050205.png: Developer options top

Still needed: dev options w/ wireless debugging toggle, pairing-code dialog, wireless debugging screen (IP:port), adb-auto-enable app, VPN settings w/ Tailscale.

## Phone incident ~05:02
- adbd wedged: TCP connects on 5555 but never completes ADB handshake (verified via manual CNXN).
- Tried: kill-server/start-server, tunnel restart, hard kill adb server, disconnect/reconnect. Still "offline".
- Phone reachable via Tailscale proxy (TCP). Not an adbd-auth issue (would say unauthorized).
- Likely needs physical reboot or wireless-debugging toggle. adb-auto-enable + Always-on VPN should bring it back unattended.
- Lesson: keep screenshot sessions fast; 10s screen timeout + slow pc commands = pain. Use PC_SCRCPY=0 to avoid confusion, wake explicitly.

## 2026-10-01 ~00:15 - phone hands-off, wizard implemented
- Zach reports the screenshot session toggled wireless debugging OFF. He re-enabled it himself and is on the phone. PHONE IS HANDS-OFF until parent says resume. No adb, no taps, no screenshots.
- Prior adbd wedge (~00:03-00:12): TCP connected on 5555 but adbd never completed the ADB handshake (verified via manual CNXN). Exhausted remote recovery: kill-server/start-server, tunnel restart, hard kill adb server, disconnect/reconnect, dropping all forwarded connections + 30s wait. Phone otherwise alive (Tailscale up, bridge :8266 listening, Android userspace fine). BedJet alarm for tomorrow unaffected (runs on units; phone alarm verified set after reboot test #2).
- `pc setup` wizard IMPLEMENTED in bin/pc (~450 lines): 10 steps, --list-steps, --step NAME, --confirm, --yes, --code/--ip/--pair-port/--connect-port. Pairing code passed on stdin to `adb pair`, never stored; "setup" added to record_command_line skip list so codes never land in recipes. State file ~/.cache/pc/setup-state.json.
- Tests: 146/146 pass (128 original + 18 new wizard tests). Fixed pre-existing failure test_config_example_has_placeholders (example intentionally pins ADB_PORT=5555 now).
- Docs updated: SKILL.md, skills/burner/SKILL.md, README.md (pc setup as guided path, setup/ screenshot refs, hosted-Muse tailnet join prereq, no em dashes in user copy).
- setup/: setup-01 (Tailscale, redacted) and setup-02 (Build number, cropped) are real. setup-03 through setup-07 are placeholders. Missing shots: wireless-debugging toggle row, pairing-code dialog, wireless debugging IP:port screen, adb-auto-enable app, VPN settings. Raw shots in shots/ still contain PII, do not copy unprocessed.
