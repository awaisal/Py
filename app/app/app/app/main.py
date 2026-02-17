import logging
import time
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

from .config import BOT_TOKEN, PUBLIC_URL, WEBHOOK_PATH, PORT, ADMIN_IDS
from .db import init_db, forgive_user, set_rules, set_welcome, get_strikes
from .moderation import check_flood, check_link_spam, apply_punishment, send_welcome_if_any

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

def _is_owner(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "✅ Bot is running.\n"
        "Use /help for commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Commands:\n"
        "/start\n"
        "/help\n"
        "/rules - show rules\n"
        "/setrules <text> (admin)\n"
        "/setwelcome <text> (admin)\n"
        "/status (admin) - reply to user message\n"
        "/forgive (admin) - reply to user message (reset strikes)\n"
        "/unrestrict (admin) - reply to user message (remove mute)\n"
        "/ban (admin) - reply to user message\n"
    )

async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .db import get_chat_settings
    from .config import DEFAULT_RULES
    chat = update.effective_chat
    if not chat:
        return
    _, rules = get_chat_settings(chat.id)
    await update.effective_message.reply_text(rules or DEFAULT_RULES)

def _get_reply_user(update: Update):
    msg = update.effective_message
    if not msg or not msg.reply_to_message or not msg.reply_to_message.from_user:
        return None
    return msg.reply_to_message.from_user

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not _is_owner(user.id):
        return
    chat = update.effective_chat
    target = _get_reply_user(update)
    if not chat or not target:
        await update.effective_message.reply_text("Reply to a user's message with /status")
        return
    strikes = get_strikes(chat.id, target.id)
    await update.effective_message.reply_text(f"👤 User: {target.id}\nStrikes: {strikes}")

async def forgive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not _is_owner(user.id):
        return
    chat = update.effective_chat
    target = _get_reply_user(update)
    if not chat or not target:
        await update.effective_message.reply_text("Reply to a user's message with /forgive")
        return
    forgive_user(chat.id, target.id)
    await update.effective_message.reply_text("✅ Strikes reset (forgiven).")

async def unrestrict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not _is_owner(user.id):
        return
    chat = update.effective_chat
    target = _get_reply_user(update)
    if not chat or not target:
        await update.effective_message.reply_text("Reply to a user's message with /unrestrict")
        return
    try:
        # restore default permissions (can send messages)
        from telegram import ChatPermissions
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False,
        )
        await context.bot.restrict_chat_member(chat.id, target.id, perms)
        await update.effective_message.reply_text("✅ User unmuted/unrestricted.")
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed: {e}")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not _is_owner(user.id):
        return
    chat = update.effective_chat
    target = _get_reply_user(update)
    if not chat or not target:
        await update.effective_message.reply_text("Reply to a user's message with /ban")
        return
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.effective_message.reply_text("⛔ User banned.")
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed: {e}")

async def setrules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or not _is_owner(user.id):
        return
    text = update.effective_message.text
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.effective_message.reply_text("Usage: /setrules <rules text>")
        return
    set_rules(chat.id, parts[1].strip())
    await update.effective_message.reply_text("✅ Rules updated.")

async def setwelcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or not _is_owner(user.id):
        return
    text = update.effective_message.text
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.effective_message.reply_text("Usage: /setwelcome <welcome text>")
        return
    set_welcome(chat.id, parts[1].strip())
    await update.effective_message.reply_text("✅ Welcome message updated.")

async def new_members_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # welcome new members
    await send_welcome_if_any(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return

    # ignore service messages
    if not msg.text and not msg.caption:
        return

    text = msg.text or msg.caption or ""

    # admin bypass
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    # spam checks
    if check_flood(chat.id, user.id, text):
        await apply_punishment(update, context, "Flood/Repeated messages")
        return

    if check_link_spam(text):
        await apply_punishment(update, context, "Link spam / unauthorized link")
        return

    # (Optional) add keyword-based abuse filter here if you want later

def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))

    app.add_handler(CommandHandler("setrules", setrules_cmd))
    app.add_handler(CommandHandler("setwelcome", setwelcome_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("forgive", forgive_cmd))
    app.add_handler(CommandHandler("unrestrict", unrestrict_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_members_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.Caption(True), message_handler))

    return app

def main():
    init_db()

    application = build_app()

    webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
    logger.info("Starting webhook on port %s path %s", PORT, WEBHOOK_PATH)
    logger.info("Setting webhook URL: %s", webhook_url)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
