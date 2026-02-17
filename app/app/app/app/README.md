# Telegram Webhook Bot (Fly.io)

## Features
- Webhook-based Telegram bot (no polling)
- Welcome message for new members
- Anti-spam: flood/repeat detection + link spam
- Escalation:
  - 1st strike: 5 days mute
  - 2nd strike: 1 month mute
  - 3rd strike: permanent ban
- Owner controls:
  - /unrestrict (reply)
  - /forgive (reply)
  - /ban (reply)
  - /status (reply)
  - /setrules <text>
  - /setwelcome <text>

## Deploy Steps (Fly.io)
1) Install flyctl and login:
   fly auth login

2) Create app:
   fly launch --no-deploy

3) Create volume for SQLite persistence:
   fly volumes create botdata --size 1

4) Set secrets:
   fly secrets set BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
   fly secrets set ADMIN_IDS="123456789"
   fly secrets set PUBLIC_URL="https://YOUR_FLY_APP_NAME.fly.dev"

5) Update fly.toml app name:
   app = "YOUR_FLY_APP_NAME"

6) Deploy:
   fly deploy

## Telegram side
- Add bot to your group
- Promote bot as admin (needed for restrict/ban)
- You (ADMIN_IDS) should be admin too.

## Notes
- Without Fly volume, SQLite data can reset on redeploy/restart.
