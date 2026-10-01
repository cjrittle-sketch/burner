# setup/ screenshots

Reference images for `burner setup` human steps and the pairing docs. All are
privacy-scrubbed (cropped/redacted, downscaled) before landing here.

## Status

| File | Step | Status |
|------|------|--------|
| setup-01-tailscale.png | Tailscale on the phone (toggle ON, Connected) | DONE (redacted) |
| setup-02-build-number.png | About phone, Build number row | DONE (cropped) |
| setup-03-wireless-debugging.png | Developer options, Wireless debugging toggle | DONE (cropped) |
| setup-04-pairing-dialog.png | Pair device with pairing code dialog | DONE (code and IP redacted) |
| setup-05-wireless-debugging-screen.png | Wireless debugging screen, IP:port | DONE (IP redacted) |
| setup-06-adb-auto-enable.png | ADB Auto Enable app main screen | DONE (URL redacted) |
| setup-07-vpn-settings.png | VPN settings showing Tailscale | DONE |

Raw captures live in `shots/` (gitignored) and still contain PII (email,
IMEIs, MACs, tailnet IPs). Never copy a raw shot into `setup/` without
cropping/redacting first.

## Capture notes

- Keep the phone screen awake (charger + `svc power stayon true`); the 10s
  display timeout lets the screen sleep between slow commands.
- Do NOT toggle wireless debugging off while capturing; toggling it drops
  the adb connection.
- Pairing codes expire in about a minute; capture the dialog fast or not at
  all.
