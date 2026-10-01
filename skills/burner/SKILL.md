---
name: burner
description: Give your AI a physical Android phone. Control a dedicated Android phone over ADB via the pc CLI: dump UI, tap, type, wait, screenshots, deep links, and transient verification-code flows. For apps with no API or MCP (marketplaces, banking, social, bot-blocking store apps). Pairs over Tailscale or LAN with one-time human-assisted wireless-debugging pairing.
---

# burner

Give your AI a physical Android phone. burner is a CLI (`pc`) that drives a
dedicated Android phone over ADB, so an agent can operate real mobile apps that
have no API, no MCP server, and no web automation path: marketplaces, banking
apps, social apps, store apps that block bots in browsers.

## Install

```bash
git clone https://github.com/useburner/burner   
cd burner
./install.sh          # idempotent; local-only, no sudo
export PATH="$PWD/bin:$PATH"
```

Needs: Linux/macOS VM with Python 3.10+, a spare Android 11+ phone,
Tailscale (or same LAN), and a human once for ~10 minutes to pair.

## Pair the phone

**HUMAN REQUIRED:** on the phone, enable Developer options, turn on Wireless
debugging, tap "Pair device with pairing code", and send the agent the IP,
pairing port, and 6-digit code (it expires fast; turn Tailscale on first so
the dialog shows the tailnet IP). After the one-time `adb pair`, the agent
installs **adb-auto-enable** (open source, `com.tpn.adbautoenable`), grants
it `WRITE_SECURE_SETTINGS`, and exempts it from battery optimization; then
**HUMAN REQUIRED:** open the app and finish its one-time self-pairing. From
then on ADB re-enables on every boot on the fixed port **5555**, so
`ADB_PORT="5555"` in `config.env` is permanent — reboots need no human action.

Security: port 5555 listens on the phone's WiFi and tailnet interfaces (never
the internet; ADB is unencrypted, so trusted networks only). Any new computer
triggers an on-device authorization prompt — never approve one uninitiated.

## Verify

```bash
pc doctor
pc dump
pc tap "Settings"
```

## Core commands

```
pc state | pc dump [--all] | pc tap "Text" [--fuzzy] [--index N]
pc wait "Text" [--timeout 30] [--absent] | pc type "text" --clear [--field "Hint"]
pc press BACK | pc start com.app.pkg | pc shot | pc open <url>
pc do 'step; step' | pc recipe <name> | pc ensure
pc gcode --from ... | pc vcode --from ...   # email verification codes, transient, never stored
pc amazon-status | pc doctor
```

## Rules that matter

- The phone has no SIM: verification codes come from email (`gcode`/`vcode`),
  typed as plain text, never stored, never asked of the user.
- Never buy anything without explicit human approval, every time.
- **Stop before submission:** text entry and tapping Send/Post/Buy are two
  separately authorized steps. Type, verify the rendered text via `pc shot`
  or `pc dump`, then tap submit only with explicit approval for that specific
  action. Never auto-submit in an unattended flow.
- Keep the phone on its charger: dumps come back empty if the screen sleeps.
- After a reboot, wait ~60-90s for boot plus ~30s for adb-auto-enable to
  switch adbd to port 5555, then `pc ensure`.
- `pc ensure` heals a wedged stack (tunnel, adb, u2 daemon) in ~5s.

See the repo-root `SKILL.md` and `README.md` for the full guide, benchmarks,
architecture, and troubleshooting.
