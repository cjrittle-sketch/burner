<img src="https://useburner.si/logo.png" alt="burner logo" width="120">

# burner

Give your AI assistant a physical side phone.

burner lets your AI assistant use a spare Android phone that sits in a drawer at
home, so it can use the apps you use.

## What it can do for you

- "Screen my Tinder matches and tell me who's worth a reply."
- "Keep my Snapchat streaks alive while I'm on vacation."
- "Spot underpriced flips on Vinted before anyone else sees them."
- "Check whether my paycheck landed and tell me the balance."
- "Message that Marketplace seller and offer 20 percent less."
- "Order my usual from the store app that never works in my browser."

## Get started

Paste this to your AI assistant:

```
Set up burner for me. Read the guide at https://useburner.si/skill.md and do everything in it. Walk me through the parts that need me.
```

Your AI assistant reads the guide and walks you through the rest. Setup takes
about 10 minutes, once, and any spare Android phone works. After that, plug the
phone in, leave it in a drawer, and never touch it again.

## Questions

**Will it buy things on its own?**
Never without your explicit okay. Every purchase, message, or post waits for
your yes.

**Does it work when I'm away from home?**
Yes. The phone stays plugged in at home, and your AI assistant can use it from
wherever you are.

**Is my stuff private?**
Yes. It runs on your own phone, on your own Wi-Fi at home, not in someone
else's data center. There's no burner account and no burner server, so once
it's set up nothing you do ever passes through us. Only you and your AI
assistant can reach the phone. Sign-in codes come from your email and are never
stored.

**Will apps see it as coming from my home?**
Yes. The phone uses your own Wi-Fi, so apps see a regular phone at your house,
not a computer in some faraway data center. It also uses your location like any
phone would, so nearby stores, delivery, and local listings match where you
live.

**What if the phone restarts?**
It comes back on its own. You don't need to do anything.

**Do I need to pay or sign up?**
No. burner is free and open source, and there's no burner account or burner
server. The one other app it uses, Tailscale, is free for personal use, so a
normal setup at home costs nothing.

**Where can I find the technical details?**
Start with [How it works](#how-it-works) below. The full setup steps and every
command are in [SKILL.md](SKILL.md).

## Security notes

- It's your phone on your own Wi-Fi. Only computers signed in to your own
  Tailscale can reach it. Never open the phone up to the public internet:
  anyone who reaches it gets full control of the phone.
- Sign-in codes get read, typed and forgotten. They're never saved.
- Your phone's address lives in `config.env` on your computer and is kept out
  of GitHub. Pairing codes are never saved anywhere.
- Screenshots stay in the `shots/` folder and are kept out of GitHub too,
  since they show your personal stuff.

## Gotchas

- After a restart, give the phone about 2 minutes to come back. If your AI
  assistant still can't reach it, `pc ensure` reconnects it.
- Tailscale has to turn itself on after a restart. Your AI assistant sets that
  up during setup, so you never have to open the app.
- Keep the phone on its charger with the screen allowed to stay on. If the
  screen goes dark, your AI assistant can't see what's on it.
- No SIM needed. The phone only uses Wi-Fi, and sign-in codes come by email.
- Nothing gets bought, sent or posted without your yes. Every time.
- The first connection right after pairing sometimes fails. Trying again fixes
  it.

## How it works

burner is a small command-line tool, `pc`, that your AI assistant runs. It
connects to the phone through Android's wireless debugging, over Tailscale (or
your home Wi-Fi when both are on the same network). From there it reads what's
on the screen, taps, types, opens apps and links, and takes screenshots, the
same way you would. Sign-in codes come from your email, so the phone doesn't
need a SIM. Everything the phone does in your apps happens on your own Wi-Fi.

The full setup steps and command reference are in [SKILL.md](SKILL.md).

## License

MIT, co-authors Muse & Claude. See [LICENSE](LICENSE).
