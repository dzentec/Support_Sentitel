from telegram.ext import Application
from app.config import settings

application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
