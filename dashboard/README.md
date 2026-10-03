# Burner Dashboard

A small, mobile-friendly remote control for the Android emulator attached to the
Mac mini. It uses the existing Burner CLI for screenshots, taps, typing, app
launches, and recipe playback.

> **Authentication is mandatory.** Every page and API endpoint requires HTTP
> Basic Auth. The server refuses to start unless both `DASHBOARD_USER` and
> `DASHBOARD_PASS` are set. Keep the service bound to localhost; Basic Auth does
> not encrypt traffic, so use an SSH tunnel or an HTTPS reverse proxy for remote
> access. Never put real credentials in this repository.

## Install on the Mac mini

Open Terminal and run:

```bash
cd /Users/christopherrittle/burner/dashboard
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The dashboard calls Burner at
`/Users/christopherrittle/.venvs/burner/bin/burner`, uses the already-connected
emulator at `127.0.0.1:5555`, and reads recipes from
`/Users/christopherrittle/burner/recipes/`.

## Run locally

Choose a long, unique password. Export it in the terminal—do **not** add it to a
file in the repository:

```bash
export DASHBOARD_USER='admin'
export DASHBOARD_PASS='replace-with-a-long-random-password'
.venv/bin/python app.py
```

Then open <http://127.0.0.1:5000> and enter those credentials. To access it from
another computer without exposing the unencrypted service, create an SSH tunnel:

```bash
ssh -L 5000:127.0.0.1:5000 your-mac-mini
```

Then browse to `http://127.0.0.1:5000` on that computer.

## Start automatically with launchd

Create `~/Library/LaunchAgents/com.burner.dashboard.plist` on the Mac mini. The
example below contains placeholders: replace them locally and never commit the
result. `launchd` does not expand shell variables or `~`, so use full paths.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.burner.dashboard</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/christopherrittle/burner/dashboard/.venv/bin/python</string>
    <string>/Users/christopherrittle/burner/dashboard/app.py</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/christopherrittle/burner/dashboard</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>DASHBOARD_USER</key>
    <string>REPLACE_WITH_USERNAME</string>
    <key>DASHBOARD_PASS</key>
    <string>REPLACE_WITH_LONG_RANDOM_PASSWORD</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/Users/christopherrittle/Library/Logs/burner-dashboard.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/christopherrittle/Library/Logs/burner-dashboard-error.log</string>
</dict>
</plist>
```

Set restrictive permissions and load it:

```bash
chmod 600 ~/Library/LaunchAgents/com.burner.dashboard.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.burner.dashboard.plist
```

After editing the plist, restart it with:

```bash
launchctl bootout gui/$(id -u)/com.burner.dashboard
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.burner.dashboard.plist
```

## API

All routes, including `/`, require Basic Auth.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/shot` | Capture and return the latest PNG |
| `POST` | `/tap` | Tap `{ "x": 0..1000, "y": 0..1000 }` relative to the screen |
| `POST` | `/type` | Type `{ "text": "hello" }` |
| `POST` | `/press` | Press `{ "key": "home" }` or `{ "key": "back" }` |
| `GET` | `/apps` | List installed app package names |
| `POST` | `/launch` | Launch `{ "package": "com.example.app" }` |
| `GET` | `/recipes` | List recipes |
| `POST` | `/recipe/<name>` | Replay a known recipe |

Commands are executed directly without a shell. App package names, recipe names,
key names, input sizes, and tap coordinates are validated by the server.
