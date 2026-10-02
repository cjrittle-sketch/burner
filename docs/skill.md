> Install: curl -fsSL https://useburner.si/install.sh | bash (full guide below)

# burner

Give your AI a physical Android phone. burner is a CLI that controls a
dedicated Android phone over ADB, so an agent can drive real mobile apps that
have no API, no MCP server, and no web automation path: marketplaces, banking
apps, social apps, store apps that block bots in the browser.

When the user says "use my burner", "use my burner phone" or "do it on my
burner", that means this phone: use the `burner` commands below.

## Common requests

| The user says | Do this |
|---|---|
| "What's on my burner?" | Means the screen right now, not the installed apps. Take a screenshot and send the image back (below). |
| "Take a screenshot of my burner" | Same: take a screenshot and send the image. |

To send a screenshot, save it where your chat can show files from, usually
your working folder: `burner shot --out ./burner-screen.png`, then attach
that file. Plain `burner shot` saves under `~/burner/shots/`, which many chat
apps can't display.

## Prerequisites

- A Linux or macOS VM/container with Python 3.10+ and network access.
- A spare Android phone (Android 11+) you can dedicate to this. It becomes the
  agent's side phone, so do not use your daily driver.
- Tailscale installed on both the VM and the phone (or both on the same LAN).
- If the agent runs on a hosted service (not your own hardware), its
  computer joins your tailnet during setup (step 3 of the setup order).
- A human available once for ~10 minutes to pair the phone (see below).

## How to talk to the user during setup

Keep updates short, plain and non-technical. Say what's happening for them,
not how: "Installing burner on my side, this takes a minute" or "Done, now
one thing on your phone." Most people don't need installer output or the
names of the parts (platform tools, adb, venv, Python, uiautomator2,
ports), so leave those out unless they ask. If something fails, say so
plainly.

## Setup order

Go in this order, so the user sees progress before being asked for anything:

1. Tell them you're starting ("Setting up burner, I'll install it on my side
   first") and run the install (below).
2. Ask which device they're on (next section).
3. Get this computer onto their tailnet: run `burner setup --step tailnet`.
   If it's already on, move on. If not, it prints an approval
   link: send the link as its own message with one plain line ("Tap this to
   let my computer reach your phone, then tell me when it's done"), wait,
   and re-run the step. A fresh assistant session can be a new computer
   that needs approving again. Same-Wi-Fi setups skip this.
4. Walk them through the phone steps, then finish with burner.

## First, work out where the user is

Work out which device they are talking to you from before asking. Use what
you already know: the app or client they're chatting in, its platform or
user agent, or anything they've said (a mobile app on Android usually means
they're holding a phone, a desktop or web client means a computer). Then
always ask with these three choices, putting your best guess first:

- This is my spare phone (the one I'm setting up)
- I'm on my everyday phone
- I'm on a computer

If your app can show tappable choices, use them. Then follow that path:

- **From the spare phone itself:** that phone is the burner phone. Skip any
  "find a spare phone" advice and do the human steps below on the phone they
  are holding. Switching apps closes the pairing dialog and cancels the
  code, so before step 3 have them put Settings and this chat side by side
  in split screen: open Recent apps (swipe up and hold), tap the Settings
  icon at the top of its card, tap "Split screen" (Samsung: "Open in split
  screen view"), then pick this chat app. Only then tap "Pair device with
  pairing code" in the Settings half and type the code into the chat half.
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

The guided path is `burner setup`: it walks through every step below, runs the agent
steps itself, and finishes with `burner doctor`. Pairing codes only last about a minute, so
run the pair step as soon as the user sends one. If a code expires, ask for
a fresh one.

Do these on the phone. The agent cannot do them for you.

Walk the user through them one at a time, as part of setup: say what to tap
and wait for them to say it's done before the next
step. Never hand them a list to do "meanwhile" while you install. Give the
full Settings path for every tap, never just a screen name. Menus differ by
brand (paths below are Pixel, with Samsung noted), so know the brand first:
infer it from their device if you can (a phone model in the user agent, or
something they said), and ask only if you can't.

1. **HUMAN REQUIRED:** Connect the phone to WiFi, install Tailscale from the
   Play Store, sign in, and leave it connected. Check first: if
   `burner setup --list-steps` shows `tailscale-phone` done (your tailnet
   already has an Android phone online), this step is already done; just
   tell them so and move on.
2. **HUMAN REQUIRED:** Enable Developer options, then turn on
   **Wireless debugging**:
   - Settings > About phone > tap **Build number** 7 times, until it says
     "You are now a developer" (enter the phone PIN if asked). On Samsung,
     Build number is in Settings > About phone > Software information.
   - Go back to Settings > System > **Developer options** (on Samsung,
     Developer options is at the bottom of the main Settings list).
   - Scroll down to the Debugging section and turn on **Wireless debugging**.
     When it asks "Allow wireless debugging on this network?", check
     **Always allow on this network**, then tap Allow. Shortcut: search
     Settings for "Wireless debugging".
3. **HUMAN REQUIRED:** Tap the words **Wireless debugging** (not the switch)
   to open its screen, tap "Pair device with pairing code", and send the agent
   the code and the numbers under "IP address & Port" exactly as shown.

   **If they're chatting on the burner phone itself, this is where people
   get stuck.** The pairing code only works while its dialog stays open.
   Closing it, tapping outside it, going Back, or switching to the chat app
   turns pairing off and the code stops working. So before they tap "Pair
   device with pairing code", tell them this in plain words and get them
   into split screen first, Settings in one half and this chat in the other
   (steps in "First, work out where the user is"). Once the dialog is open,
   they leave it alone, take a screenshot, and send it from the chat half.
   If the dialog closes, it's fine: tap "Pair device with pairing code"
   again for a new code.

   Read the IP, port and code off what they send, rather
   than asking for each value separately. **Turn Tailscale on first** -
   after a reboot it does not auto-start, and the dialog shows the unreachable
   WiFi IP instead of the tailnet IP.
4. The agent runs the one-time pairing (`adb pair`), then
   `burner setup --step verify` (`burner doctor`). **burner must be green
   before anything else**: the remaining steps are niceties, and the agent
   does them itself with burner, so there is nothing more for the user to
   tap except removing a PIN (step 5).

   **Keep the user posted from here on; the rest takes a few minutes and
   silence feels broken.** The moment pairing works, send a message before
   running anything else, e.g. "Paired, your phone is connected. I'm
   finishing setup now. Your phone may flip through screens on its own for
   a few minutes; you can set it down." Then run the step 5 commands one at
   a time and send a short line as each finishes ("Screen set to stay on
   while charging", "Tailscale will now start by itself after a restart"),
   so they always see what just happened. End with a clear "All done".
5. The agent finishes the phone with burner, one `burner setup --step` each:
   - `tailscale-battery`: Tailscale battery usage set to Unrestricted, so
     Android doesn't stop it.
   - `stay-awake`: screen stays on while charging, so the phone never
     sleeps mid-task.
   - `screen-lock`: turns off the lock screen so the phone opens straight to
     the home screen after a restart. If the phone has a PIN, pattern or
     password, burner can't remove it (it needs their PIN): ask the user to
     do it in Settings > Security & privacy > Device unlock > Screen lock >
     None (Samsung: Settings > Lock screen > Screen lock type > None).
   - `install-adb-auto-enable`: tell the user first that this downloads a
     small free app from GitHub, so if their assistant asks to reach
     api.github.com or github.com, that's expected. Installs
     **adb-auto-enable** (open source, `com.tpn.adbautoenable`,
     https://github.com/mouldybread/adb-auto-enable/releases), grants it
     `WRITE_SECURE_SETTINGS`, and exempts it from battery optimization.
   - `self-pair`: opens the app once, opens the pairing dialog in Settings,
     reads the code off the screen, and hands it to the app. This step is
     optional and best effort: if the app's pairing page doesn't come up,
     the step skips itself. burner still works; the only cost is that after
     a phone restart the user turns Wireless debugging back on once. Tell
     the user that in a sentence and carry on; there's nothing for them to
     fix.
   - `always-on-vpn`: sets Always-on VPN for Tailscale, so Tailscale starts
     itself after a reboot (lockdown stays off, so if Tailscale ever fails
     the phone still has normal internet).
   - `fix-port`: pins adbd to port **5555** and writes `ADB_PORT="5555"` to
     `config.env`. From then on the app re-enables ADB on every boot, the
     random wireless-debugging port is never used again, and reboots need
     no human action.

Last, close with a short message that's about them, not the setup parts,
e.g. "All done. Plug the phone into a charger and leave it there on Wi-Fi."
(The screen only stays on while charging, which is why it lives on the
charger.) Done.

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
| No Wireless debugging option in Developer options | It needs Android 11 or newer. Check Settings > About phone > Android version. If it's 11+, scroll to the Debugging section of Developer options or search Settings for "Wireless debugging". On Android 10 or older, the phone can't be a burner phone. |
| Phone shows "Unsafe app blocked: ATX" | An older burner tried to install an extra keyboard app burner doesn't need. Tap OK to dismiss it, then update burner (re-run the installer). |
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
burner scroll [down|up|left|right] [--times N] [--to "Text"]   scroll; --to stops when Text shows
burner press BACK|HOME        key events (--repeat N, --delay MS, --ctrl/--shift/--alt/--meta)
burner start com.app.pkg     launch an app
burner shot                  screenshot to shots/
burner open <url> [pkg]      open a deep link / URL (pkg targets one app)
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

burner shot [--out PATH]
    Screenshot, saved under shots/ or to PATH.

burner open <url> [package]
    Open a URL or deep link via VIEW intent. Deep links skip menu
    navigation, e.g. burner open https://www.amazon.com/gp/css/order-history
    A package targets one app and skips the "Open with" chooser, e.g.
    burner open market://details?id=com.example.app com.android.vending

burner sleep <seconds>
    Sleep, mainly for use inside burner do flows.

burner do 'open URL; wait "Cart" --timeout 30; tap "Checkout"'
    Run a ;-separated flow in one call, stopping on the first failure.

burner recipe <name>
    Run a saved flow from recipes/<name>.burner (same ;-separated format,
    one step per line, # comments allowed). $VAR in a step expands from the
    environment; an unset $VAR stops the recipe before it runs.
    PLAY_PACKAGE=com.example.app burner recipe play-install

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

burner update [recipes]
    Update burner and its built-in recipes to the latest. Keeps config.env,
    the phone pairing and recipes you recorded under your own names.
    `burner update recipes` refreshes only the built-in recipes.

burner uninstall [--yes]
    Undo the phone changes setup made (stay awake, lock screen, always-on
    VPN, helper apps, wireless debugging). Without --yes it only lists them.
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
