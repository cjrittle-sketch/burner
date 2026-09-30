# burner

Give your AI a physical Android phone. burner is a CLI (`pc`) that controls a
dedicated Android phone over ADB, so an agent can drive real mobile apps that
have no API, no MCP server, and no web automation path: marketplaces, banking
apps, social apps, store apps that block bots in the browser.

## Prerequisites

- A Linux or macOS VM/container with Python 3.10+ and network access.
- A spare Android phone (Android 11+) you can dedicate to this. It becomes the
  agent's side phone, so do not use your daily driver.
- Tailscale installed on both the VM and the phone (or both on the same LAN).
- A human available once for ~10 minutes to pair the phone (see below).

## Install

```bash
git clone https://github.com/HALPLACEHOLDER/burner   # placeholder URL, repo not yet published
cd burner
./install.sh
```

`install.sh` is idempotent and writes nothing outside the repo: it finds or
downloads platform-tools (adb), creates `.venv/`, installs `uiautomator2`,
copies `config.env.example` to `config.env` (never overwrites an existing
one), and makes `bin/pc` executable. No sudo, no system-wide writes.

Then put the repo on your PATH or call it directly:

```bash
export PATH="$PWD/bin:$PATH"
```

## Pair the phone (HUMAN REQUIRED steps marked)

Do these on the phone. The agent cannot do them for you.

1. **HUMAN REQUIRED:** Connect the phone to WiFi, plug it into a charger, and
   install Tailscale from the Play Store. Sign in, leave it connected, and set
   Tailscale battery usage to Unrestricted so Android does not kill it.
2. **HUMAN REQUIRED:** Enable Developer options (Settings > About phone > tap
   Build number 7 times), then turn on **Wireless debugging**.
3. **HUMAN REQUIRED:** Tap "Pair device with pairing code" and send the agent
   the IP, the pairing port, and the 6-digit code. The code expires fast, so
   send it right after the phone shows it.
4. The agent runs the one-time pairing (`adb pair`), then you send it the
   **connection** port shown on the main Wireless debugging screen (it looks
   like `192.168.x.x:PORT`; different from the pairing port). The agent puts
   it in `config.env`.

Leave the phone plugged in and on WiFi. Done.

## Verify

```bash
pc doctor     # end-to-end health check: tunnel, adb, uiautomator2, screen
pc dump       # list visible UI text on the phone screen
pc tap "Settings"   # tap the first node with that text
```

If `pc doctor` reports green, the agent can drive the phone.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Phone unreachable / adb connect fails | Wireless debugging may have toggled off and on, which changes the port. **HUMAN:** read the new connection port from the phone's Wireless debugging screen and update `ADB_PORT` in `config.env`. |
| `adb unauthorized` | The adb key was revoked. Re-run the pairing flow above (send a fresh pairing code). |
| u2 daemon dead / commands hang | Run `pc ensure`: it restarts the tunnel, the u2 daemon, and the adb server (~5s). |
| Dumps come back empty | The screen must stay awake. Keep the phone on its charger; use `pc sleep`-free flows, and do not let the display time out mid-run. |
| adb missing after install | `install.sh` downloads platform-tools to `.android-tools/` and `bin/pc` uses it automatically. Check `.android-tools/platform-tools/adb` exists. |

## Command reference (short)

```
pc state                 focused app + top screen texts
pc dump [--all]          every UI node: text, class, bounds
pc tap "Text" [--fuzzy]  tap first matching node (--index 1 for the second)
pc wait "Text" [--timeout 30]   wait for text to appear (or --absent to vanish)
pc type "text" --clear    type char-by-char, Bloks/RN-safe (--field "Hint" focuses first)
pc press BACK|HOME        key events
pc start com.app.pkg     launch an app
pc shot                  screenshot to shots/
pc open <url>            open a deep link / URL in the app
pc do 'step; step'       run a ;-separated flow in one call
pc recipe <name>         run a saved flow from recipes/<name>.pc
pc ensure                heal the tunnel + adb + daemon stack
pc gcode --from ...      pull newest verification code from Gmail (transient, never stored)
pc vcode --from ...      one-shot: wait for code field, pull code, type, submit
pc amazon-status         latest Amazon order status, one shot
pc doctor                full health check
```

Codes are pulled from the user's connected Gmail, typed as plain text, and
never stored. The tool never makes purchases on its own: any buy needs explicit
human approval each time.

Full detail, benchmarks, and architecture: see `README.md`.
