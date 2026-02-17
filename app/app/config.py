import os

def _required(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

BOT_TOKEN = _required("BOT_TOKEN")

# Fly public URL like: https://your-app-name.fly.dev
PUBLIC_URL = _required("PUBLIC_URL").rstrip("/")

# Comma-separated Telegram user IDs who are bot admins (you).
# Example: "123456789,987654321"
ADMIN_IDS = set()
_admin_raw = os.getenv("ADMIN_IDS", "").strip()
if _admin_raw:
    ADMIN_IDS = {int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()}

# Webhook path (security): use token as path
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# Fly listens on 8080 by default
PORT = int(os.getenv("PORT", "8080"))

# DB path (use /data on Fly volume)
DB_PATH = os.getenv("DB_PATH", "/data/bot.db")

# Anti-spam settings
FLOOD_WINDOW_SEC = int(os.getenv("FLOOD_WINDOW_SEC", "8"))     # seconds
FLOOD_MAX_MSG = int(os.getenv("FLOOD_MAX_MSG", "6"))          # messages allowed in window
REPEAT_MAX = int(os.getenv("REPEAT_MAX", "3"))                # repeated same text threshold
LINK_SPAM_ENABLED = os.getenv("LINK_SPAM_ENABLED", "1") == "1"

# Default messages (editable via commands)
DEFAULT_WELCOME = os.getenv("DEFAULT_WELCOME", "Welcome! ✅ Rules follow karo, spam mat karo 🙂")
DEFAULT_RULES = os.getenv(
    "DEFAULT_RULES",
    "Rules:\n1) Spam/Flood nahi\n2) Links bina permission nahi\n3) Abuse nahi\n4) Off-topic limit\nViolation par auto restriction."
)
