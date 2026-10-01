# burner

Give your AI a physical Android phone. burner is a CLI that controls a
dedicated Android phone over ADB, so an agent can drive real mobile apps that
have no API, no MCP server, and no web automation path: marketplaces, banking
apps, social apps, store apps that block bots in the browser.

## Prerequisites

- A Linux or macOS VM/container with Python 3.10+ and network access.
- A spare Android phone (Android 11+) you can dedicate to this. It becomes the
  agent's side phone, so do not use your daily driver.
- Tailscale installed on both the VM and the phone (or both on the same LAN).
- If the agent runs on hosted Muse (not your own hardware): the Muse VM must
  join your tailnet. The agent runs `tailscale up` and you approve it once via
  the link it shows. Without this the VM has no route to the phone. Same-LAN
  setups skip this step.
- A human available once for ~10 minutes to pair the phone (see below).

## First, ask where the user is

Ask which device they are talking to you from, then follow that path:

- **From the spare phone itself:** that phone is the burner phone. Skip any
  "find a spare phone" advice and do the human steps below on the phone they
  are holding. For pairing (step 3), have them put Settings and this chat
  side by side in split screen, so the pairing dialog stays open while they
  send you the code. Leaving the dialog cancels the code.
- **From a computer or their everyday phone:** they need the spare phone in
  hand for the human steps below. If they don't have one yet, stop and tell
  them what to get.

## Install

```bash
curl -fsSL https://useburner.si/install.sh | bash
```

This fetches the source into `~/burner` (or `$BURNER_DIR`) and runs its
`install.sh`. `install.sh` is idempotent and writes nothing outside the repo: it finds or
downloads platform-tools (adb), creates `.venv/`, installs `uiautomator2`,
copies `config.env.example` to `config.env` (never overwrites an existing
one), and makes `bin/burner` executable. No sudo, no system-wide writes.

Then put it on your PATH or call it directly:

```bash
export BURNER_WORKSPACE="$HOME/burner"
export PATH="$HOME/burner/bin:$PATH"
```

## Pair the phone (HUMAN REQUIRED steps marked)

The guided path is `burner setup`: it walks through every step below, shows a
screenshot for each human step (in `setup/`), runs the agent steps itself,
and finishes with `burner doctor`. Keep the burner phone in hand during setup:
pairing codes expire in about a minute.

Do these on the phone. The agent cannot do them for you.

1. **HUMAN REQUIRED:** Connect the phone to WiFi, plug it into a charger, and
   install Tailscale from the Play Store. Sign in, leave it connected, and set
   Tailscale battery usage to Unrestricted so Android does not kill it.
   (Screenshot: `setup/setup-01-tailscale.png`.)
2. **HUMAN REQUIRED:** Enable Developer options (Settings > About phone > tap
   Build number 7 times), then turn on **Wireless debugging**.
   (Screenshots: `setup/setup-02-build-number.png`,
   `setup/setup-03-wireless-debugging.png`.)
3. **HUMAN REQUIRED:** Tap "Pair device with pairing code" and send the agent
   the IP, the pairing port, and the 6-digit code. The code expires fast
   (about a minute), so send it right after the phone shows it and keep the
   phone in hand. **Turn Tailscale on first** -
   after a reboot it does not auto-start, and the dialog shows the unreachable
   WiFi IP instead of the tailnet IP.
   (Screenshots: `setup/setup-04-pairing-dialog.png`,
   `setup/setup-05-wireless-debugging-screen.png`.)
4. The agent runs the one-time pairing (`adb pair`), then installs
   **adb-auto-enable** (open source, `com.tpn.adbautoenable`,
   https://github.com/mouldybread/adb-auto-enable/releases), grants it
   `WRITE_SECURE_SETTINGS`, and exempts it from battery optimization.
   **HUMAN REQUIRED:** open the app on the phone and finish its one-time
   self-pairing (enter the code it shows; takes about a minute).
   (Screenshot: `setup/setup-06-adb-auto-enable.png`.)
5. From then on the app re-enables ADB on every boot and pins adbd to the
   fixed port **5555**. Put `ADB_PORT="5555"` in `config.env` once - the
   random wireless-debugging port is never used again, and reboots need no
   human action.
6. The agent sets Always-on VPN for Tailscale over adb, so Tailscale
   auto-starts after reboot (without it the phone is unreachable until a
   human opens the app manually):

   ```bash
   adb -s <device> shell settings put secure always_on_vpn_app com.tailscale.ipn
   ```

   Leave lockdown off (default): if Tailscale ever fails, the phone still
   has normal internet. Verify with
   `settings get secure always_on_vpn_app` returning `com.tailscale.ipn`.
   (Screenshot: `setup/setup-07-vpn-settings.png`.)

Leave the phone plugged in and on WiFi. Done.

## Security notes

- Port 5555 listens on all the phone's interfaces (WiFi and Tailscale), but
  only to trusted networks - nothing is exposed to the internet. The ADB
  protocol itself is unencrypted, so only use the phone on networks you trust.
- Every new computer that connects triggers an on-device "Allow USB
  debugging?" prompt with a key fingerprint. Never approve one you did not
  initiate - that prompt is the tripwire.

## Verify

```bash
burner doctor     # end-to-end health check: tunnel, adb, uiautomator2, screen
burner dump       # list visible UI text on the phone screen
burner tap "Settings"   # tap the first node with that text
```

If `burner doctor` reports green, the agent can drive the phone.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Phone unreachable after a reboot / adb connect fails | Wait 60-90s for boot plus ~30s for adb-auto-enable to switch adbd to port 5555, then run `burner ensure`. If it stays down, check the app is still installed and exempt from battery optimization. |
| `adb unauthorized` | The adb key was revoked. Re-run the pairing flow above (send a fresh pairing code). |
| u2 daemon dead / commands hang | Run `burner ensure`: it restarts the tunnel, the u2 daemon, and the adb server (~5s). |
| Dumps come back empty | The screen must stay awake. Keep the phone on its charger; use `burner sleep`-free flows, and do not let the display time out mid-run. |
| adb missing after install | `install.sh` downloads platform-tools to `.android-tools/` and `bin/burner` uses it automatically. Check `.android-tools/platform-tools/adb` exists. |

## Command reference (short)

```
burner state                 focused app + top screen texts
burner dump [--all]          every UI node: text, class, bounds
burner snap [--all]          numbered snapshot: @e1..@eN handles for exact taps
burner tap "Text" [--fuzzy]  tap matching node; refuses when ambiguous (see below)
burner tap @e3                tap a snap handle's exact coordinates (no re-matching)
burner tap "A || B"          fallback labels: tries A, then B
burner tap "Text" --settle   wait for the screen to stop changing, show the diff
burner wait "Text" [--timeout 30]   wait for text to appear (or --absent to vanish)
burner type "text" --clear    type char-by-char, Bloks/RN-safe (--field "Hint" focuses first)
burner press BACK|HOME        key events (--repeat N, --delay MS, --ctrl/--shift/--alt/--meta)
burner start com.app.pkg     launch an app
burner shot                  screenshot to shots/
burner open <url>            open a deep link / URL in the app
burner do 'step; step'       run a ;-separated flow in one call
burner recipe <name>         run a saved flow from recipes/<name>.burner
burner record <name>         record actions to recipes/<name>.burner (stop with --stop)
burner replay <name>         replay a recorded session step-by-step
burner whereami              current screen fingerprint + known transitions
burner route "Label"         find a route to a screen via navigation memory
burner forget --yes          clear navigation memory
burner ensure                heal the tunnel + adb + daemon stack
burner gcode --from ...      pull newest verification code from Gmail (transient, never stored)
burner vcode --from ...      one-shot: wait for code field, pull code, type, submit
burner amazon-status         latest Amazon order status, one shot
burner doctor                full health check
```

Codes are pulled from the user's connected Gmail, typed as plain text, and
never stored. The tool never makes purchases on its own: any buy needs explicit
human approval each time.

## Command reference (full)

```
burner setup [--list-steps] [--step NAME] [--confirm] [--yes]
    Guided phone setup wizard. --list-steps shows each step's status;
    --step runs one step; --confirm records a human step as done.
    Pairing codes passed via --code are never stored.

burner dump [--verbose] [--all] [--json]
    List visible UI text and bounds. --all includes empty-text nodes.

burner tap "Text" [--fuzzy] [--index N] [--xy] [--no-occlusion-check] [--json]
    Tap the first node matching the text. --index picks the Nth match,
    --fuzzy allows close matches, --xy taps raw coordinates.

burner wait "Text" [--timeout 30] [--fuzzy] [--absent] [--json]
    Poll until text appears (exit 1 on timeout), or until it disappears
    with --absent.

burner type "text" [--field "Hint"] [--clear] [--unicode] [--ascii]
    Type char-by-char, safe on React Native / Bloks fields where bulk
    `adb shell input text` is ignored. --field taps the field first,
    --clear empties it first.

burner press BACK|HOME|<keycode>
    Key events: BACK, HOME, ENTER, DEL, volume, dpad, wake/sleep...

burner state [--json]
    Focused app plus the top screen texts and orientation.

burner start com.example.app
    Launch an app by package name.

burner shot
    Screenshot, saved under shots/.

burner open <url>
    Open a URL or deep link via VIEW intent. Deep links skip menu
    navigation, e.g. burner open https://www.amazon.com/gp/css/order-history

burner sleep <seconds>
    Sleep, mainly for use inside burner do flows.

burner do 'open URL; wait "Cart" --timeout 30; tap "Checkout"'
    Run a ;-separated flow in one call, stopping on the first failure.

burner recipe <name>
    Run a saved flow from recipes/<name>.burner (same ;-separated format,
    one step per line, # comments allowed).

burner ensure
    Heal the stack: restart tunnel, reconnect adb, revive the u2 daemon.

burner gcode --from "sender@example.com" [--mins 15]
    Pull the newest verification code from Gmail. Transient: read, used,
    never stored.

burner vcode --from "sender@example.com" [--mins 15] [--timeout 60] [--submit "Continue"]
    One-shot code flow: wait for the code field, pull the email code,
    clear, type char-by-char, wait for the submit button to enable, tap it.

burner amazon-status
    Latest Amazon order status in one shot (stops at the order list).

burner doctor [--json]
    End-to-end health check: tunnel, adb auth, u2 daemon, screen state.
```

Verification codes come from email, never SMS: the side phone has no SIM, so
any SMS code screen is a dead end. `gcode`/`vcode` pull the code from the
connected Gmail, type it as plain text, and never store it or ask the user to
paste it.

## Tapping precisely (read this before driving the UI)

`burner tap` refuses to guess. If a label matches two or more nodes it fails with
the candidate list instead of tapping the first one - re-run with `--index N`
(picks the Nth candidate) or a longer, unique label. `"A || B"` tries fallback
labels in order, so `burner tap "Checkout || Proceed to checkout"` survives
renames. `--fuzzy` substring matching auto-retries when the exact label
misses, and is flagged in ambiguity errors.

For multi-step flows, `burner snap` prints the same rows as `dump` numbered
`@e1..@eN`, and `burner tap @eN` taps that handle's exact coordinates - no
re-matching, no ambiguity. Handles are single-use: any tap, press, type, or
launch deletes the snap, so a handle can never outlive its screen.

After important taps, `--settle` re-reads the screen until it stops changing
(500ms quiet, 10s max) and prints only what appeared/disappeared, capped at
80 lines, or `unchanged`. Use it instead of `dump` → eyeball → `dump` loops.

## Safety: stop before submission (read this before automating purchases, messages, or posts)

Text entry and submission are two separately authorized steps. Never type
into a field and tap Send/Post/Buy/Submit in the same unattended flow.

1. Type the text (`burner type`), then STOP.
2. Verify what the phone actually rendered: `burner shot` and read the screenshot,
   or `burner dump` and confirm the field's text matches what you intended.
3. Only then, with the rendered text confirmed, tap the submit button - and
   only when the human explicitly approved that specific submission.

This applies to purchases, messages, posts, emails, form submissions, and
anything irreversible. The tool never makes purchases on its own: any buy
needs explicit human approval each time, and the approval covers the exact
item, price, and payment method - not "buy something like this."

**Privacy:** typed text is never recorded. The navigation memory (`burner whereami` /
`burner route`) stores screen structures and action types only - never the content
of typed text, passwords, or messages. Screenshots are never stored in the
navigation database.

How it works, security notes and gotchas: see `README.md`.
