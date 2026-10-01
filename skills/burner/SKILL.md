---
name: burner
description: Give your AI a physical Android phone. Control a dedicated Android phone over ADB via the burner CLI: dump UI, tap, type, wait, screenshots, deep links, and transient verification-code flows. For apps with no API or MCP (marketplaces, banking, social, bot-blocking store apps). Pairs over Tailscale or LAN with one-time human-assisted wireless-debugging pairing.
---

# burner

Give your AI a physical Android phone. burner is a CLI (`burner`) that drives a
dedicated Android phone over ADB, so an agent can operate real mobile apps that
have no API, no MCP server, and no web automation path: marketplaces, banking
apps, social apps, store apps that block bots in browsers.

## Install

```bash
curl -fsSL https://useburner.si/install.sh | bash   # idempotent; no sudo; installs to ~/burner
export BURNER_WORKSPACE="$HOME/burner"
export PATH="$HOME/burner/bin:$PATH"
```

Needs: Linux/macOS VM with Python 3.10+, a spare Android 11+ phone,
Tailscale (or same LAN), and a human once for ~10 minutes to pair.
If the agent runs on hosted Muse: the Muse VM must join your tailnet first
(the agent runs `tailscale up`, you approve it once); without this the VM
has no route to the phone. Same-LAN setups skip this.

## Pair the phone

The guided path is `burner setup`: it walks every step, shows a screenshot for
each human step (in `setup/`), runs the agent steps itself, and finishes with
`burner doctor`. Pairing codes last about a minute: pair as soon as one arrives,
and ask for a fresh one if it expires. Talk to the user in plain, non-technical words during setup: say what's
happening for them ("Installing burner on my side"), leave out installer
output and part names (adb, venv, Python, ports) unless they ask. First work out which device the user is chatting from (infer it from the
client, platform or user agent, confirm in one line, ask only if unsure): if it's
the burner phone itself, skip "use a spare phone" advice. Switching apps
cancels the pairing code, so have them open Settings and the chat in split
screen (Recent apps > Settings icon > Split screen) before tapping Pair. Walk the human steps one at a time,
giving the full Settings path for each tap (the wizard prints them).

**HUMAN REQUIRED:** on the phone, enable Developer options, turn on Wireless
debugging, tap "Pair device with pairing code", and send the agent the
code and IP & port line as shown, or on the same phone (in split screen) a
screenshot of the dialog (never
ask for "the pairing port" by name; turn Tailscale on first so
the dialog shows the tailnet IP). After the one-time `adb pair`, the agent
runs `burner setup --step verify` and gets burner green first. Then it
finishes the phone with burner itself, nothing for the user to tap:
Tailscale battery Unrestricted (`tailscale-battery`), screen
stays awake while charging (`stay-awake`), lock screen off (`screen-lock`;
if there's a PIN only the user can remove it), **adb-auto-enable** installed
from GitHub and self-paired (warn the user their assistant may ask to reach
api.github.com), Always-on VPN for Tailscale (lockdown off), and adbd pinned
to port **5555** (`fix-port`). After that, reboots need no human action.

Security: port 5555 listens on the phone's WiFi and tailnet interfaces (never
the internet; ADB is unencrypted, so trusted networks only). Any new computer
triggers an on-device authorization prompt - never approve one uninitiated.

## Verify

```bash
burner doctor
burner dump
burner tap "Settings"
```

## Core commands

```
burner state | burner dump [--all] | burner tap "Text" [--fuzzy] [--index N]
burner wait "Text" [--timeout 30] [--absent] | burner type "text" --clear [--field "Hint"]
burner press BACK | burner start com.app.pkg | burner shot | burner open <url>
burner do 'step; step' | burner recipe <name> | burner ensure
burner gcode --from ... | burner vcode --from ...   # email verification codes, transient, never stored
burner amazon-status | burner doctor
```

## Rules that matter

- The phone has no SIM: verification codes come from email (`gcode`/`vcode`),
  typed as plain text, never stored, never asked of the user.
- Never buy anything without explicit human approval, every time.
- **Stop before submission:** text entry and tapping Send/Post/Buy are two
  separately authorized steps. Type, verify the rendered text via `burner shot`
  or `burner dump`, then tap submit only with explicit approval for that specific
  action. Never auto-submit in an unattended flow.
- Keep the phone on its charger: dumps come back empty if the screen sleeps.
- After a reboot, wait ~60-90s for boot plus ~30s for adb-auto-enable to
  switch adbd to port 5555, then `burner ensure`.
- `burner ensure` heals a wedged stack (tunnel, adb, u2 daemon) in ~5s.

See the repo-root `SKILL.md` and `README.md` (or https://useburner.si/skill.md)
for the full guide, benchmarks, architecture, and troubleshooting.
