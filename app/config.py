import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_OPERATOR_CHAT_ID = int(os.getenv("TELEGRAM_OPERATOR_CHAT_ID", 0))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    IMAP_HOST = os.getenv("IMAP_HOST")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER = os.getenv("IMAP_USER")
    IMAP_PASS = os.getenv("IMAP_PASS")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    SMTP_SENDER = os.getenv("SMTP_SENDER")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/support.db")
    SCHEDULER_DB_URL = os.getenv("SCHEDULER_DB_URL", "sqlite:///./data/scheduler.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
    WHITELISTED_SENDERS = [
        s.strip() for s in os.getenv("WHITELISTED_SENDERS", "").split(",") if s.strip()
    ]


settings = Settings()
