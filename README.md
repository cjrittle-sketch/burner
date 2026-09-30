# burner

give your AI a physical side phone.

## What it does

burner hands an AI agent a real, dedicated Android phone it can see and touch:
read the screen as a UI tree, tap buttons, type into fields, open deep links,
take screenshots, and pull email verification codes. The whole thing runs
through one CLI: `pc`.

Why a phone at all? Plenty of apps have no API, no MCP server, and actively
block bots in a browser. Think Tinder, Snapchat, Vinted, most banking apps,
and store apps that fingerprint automation. A spare phone on your network is a
legit client those apps cannot tell apart from you holding it.

Repo: https://github.com/HALPLACEHOLDER/burner (placeholder URL, not yet published)

## How it works

```
agent
  |
  v
pc CLI (bin/pc)
  |-- adb -----------------------> phone, over ADB
  |-- u2 daemon (lib/u2/u2mux.py) -> fast UI dumps, taps, text entry
  |-- scrcpy mux ----------------> hardware keys only (home/back/wake)
  |
  v
socat tunnel: 127.0.0.1:LOCAL_PORT -> CONNECT proxy -> PHONE_IP:ADB_PORT (Tailscale or LAN)
```

The phone runs wireless debugging. The VM reaches it through a local socat
tunnel (`tunnel.sh`) that forwards through the runtime's HTTP CONNECT proxy to
the phone's tailnet IP and ADB port. Pairing is one-time (`adb pair` with a
6-digit code); after that the VM's adb key stays authorized. `pc ensure`
heals a wedged stack (tunnel, adb server, u2 daemon) in about 5 seconds.

The u2 daemon keeps a persistent connection to the phone and caches UI dumps,
which is where the speed comes from (see benchmarks). Taps go through
`adb shell input tap`, which is orientation-aware; the u2 dump's `rotation`
attribute is the source of truth for screen orientation.

## Benchmarks

Measured 2026-09-30 on a Pixel 7 over Tailscale:

| Operation | Time |
|---|---|
| Cached tap (dump cache hit) | ~0.33s |
| Cold exact-text tap | ~0.56s |
| `pc wait` (match found) | ~0.77s |
| Cold UI dump | ~1.01s |
| Cached UI dump | ~0.09s |

## Quickstart

```bash
git clone https://github.com/HALPLACEHOLDER/burner   # placeholder URL, not yet published
cd burner
./install.sh          # idempotent; local-only, no sudo
export PC_WORKSPACE="$PWD"
export PATH="$PWD/bin:$PATH"
```

Then pair the phone (needs a human once, ~10 minutes):

1. On the phone: install Tailscale, sign in, leave it connected, set its
   battery usage to Unrestricted. Connect to WiFi, plug into a charger.
2. Enable Developer options, turn on Wireless debugging.
3. Tap "Pair device with pairing code" and give the agent the IP, pairing
   port, and 6-digit code (expires fast). After the one-time pair, give the
   agent the connection port from the main Wireless debugging screen and put
   it in `config.env` as `ADB_PORT`.

Verify:

```bash
pc doctor
pc dump
pc tap "Settings"
```

## Command reference

```
pc dump [--verbose] [--all] [--json]
    List visible UI text and bounds. --all includes empty-text nodes.

pc tap "Text" [--fuzzy] [--index N] [--xy] [--no-occlusion-check] [--json]
    Tap the first node matching the text. --index picks the Nth match,
    --fuzzy allows close matches, --xy taps raw coordinates.

pc wait "Text" [--timeout 30] [--fuzzy] [--absent] [--json]
    Poll until text appears (exit 1 on timeout), or until it disappears
    with --absent.

pc type "text" [--field "Hint"] [--clear] [--unicode] [--ascii]
    Type char-by-char, safe on React Native / Bloks fields where bulk
    `adb shell input text` is ignored. --field taps the field first,
    --clear empties it first.

pc press BACK|HOME|<keycode>
    Key events: BACK, HOME, ENTER, DEL, volume, dpad, wake/sleep...

pc state [--json]
    Focused app plus the top screen texts and orientation.

pc start com.example.app
    Launch an app by package name.

pc shot
    Screenshot, saved under shots/.

pc open <url>
    Open a URL or deep link via VIEW intent. Deep links skip menu
    navigation, e.g. pc open https://www.amazon.com/gp/css/order-history

pc sleep <seconds>
    Sleep, mainly for use inside pc do flows.

pc do 'open URL; wait "Cart" --timeout 30; tap "Checkout"'
    Run a ;-separated flow in one call, stopping on the first failure.

pc recipe <name>
    Run a saved flow from recipes/<name>.pc (same ;-separated format,
    one step per line, # comments allowed).

pc ensure
    Heal the stack: restart tunnel, reconnect adb, revive the u2 daemon.

pc gcode --from "sender@example.com" [--mins 15]
    Pull the newest verification code from Gmail. Transient: read, used,
    never stored.

pc vcode --from "sender@example.com" [--mins 15] [--timeout 60] [--submit "Continue"]
    One-shot code flow: wait for the code field, pull the email code,
    clear, type char-by-char, wait for the submit button to enable, tap it.

pc amazon-status
    Latest Amazon order status in one shot (stops at the order list).

pc doctor [--json]
    End-to-end health check: tunnel, adb auth, u2 daemon, screen state.
```

Verification codes come from email, never SMS: the side phone has no SIM, so
any SMS code screen is a dead end. `gcode`/`vcode` pull the code from the
connected Gmail, type it as plain text, and never store it or ask the user to
paste it.

## Security notes

- Your phone, your network. The tunnel binds to localhost and reaches the
  phone over Tailscale (or your LAN). Do not expose the adb tunnel publicly:
  anyone who can reach it gets full control of the phone.
- Verification codes are transient: pulled, typed, never written to disk.
- `config.env` holds your tailnet IP and ports and is gitignored. Never
  commit it. Pairing codes and one-time passwords never go in config files.
- Screenshots land in `shots/`, which is also gitignored: they are your
  personal screen content.

## Gotchas

- The wireless debugging port changes whenever you toggle wireless debugging
  off and on. If the phone goes unreachable, read the new connection port off
  the phone and update `ADB_PORT` in `config.env`.
- The screen must stay awake or dumps come back empty. Keep the phone on its
  charger; short display timeouts will break long flows.
- No SIM needed. The phone is WiFi-only; codes arrive by email.
- Purchases need human approval. burner never buys anything on its own: every
  purchase is an explicit human decision, every time.
- First `adb connect` right after pairing can transiently fail; a retry
  connects fine.

## Install details

`install.sh` checks for python3 >= 3.10 and pip, finds adb on PATH or
downloads Google's platform-tools for your OS into `.android-tools/`, creates
`.venv/` with `uiautomator2`, copies `config.env.example` to `config.env`
(never overwrites), and makes `bin/pc` executable. It writes nothing outside
the repo and needs no sudo. For the agent-focused guide, see `SKILL.md`; the
Claude Code plugin skill lives in `skills/burner/`.

## License

MIT, author Hal. See `LICENSE`.
