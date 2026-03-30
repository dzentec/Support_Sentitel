from telegram.ext import Application
from app.config import settings
from app.utils.logging import logger

application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()


async def setup_bot_handlers():
    from app.services.telegram_bot import start, callback_handler, message_handler
    from telegram.ext import (
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )


async def set_webhook():
    await application.bot.set_webhook(f"{settings.WEBHOOK_URL}/webhook/tg")
