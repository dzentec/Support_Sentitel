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
    REMINDER_INTERVALS = [
        int(x) for x in os.getenv("REMINDER_INTERVALS", "15,30,60").split(",")
    ]
    SUMMARY_INTERVAL = int(os.getenv("SUMMARY_INTERVAL", 120))
    AUTO_CLOSE_TIMEOUT_HOURS = int(os.getenv("AUTO_CLOSE_TIMEOUT_HOURS", 72))
    IMAP_POLL_INTERVAL = int(os.getenv("IMAP_POLL_INTERVAL", 5))
    ALLOWED_TELEGRAM_IDS = [
        int(s.strip())
        for s in os.getenv("ALLOWED_TELEGRAM_IDS", "").split(",")
        if s.strip()
    ]

    # RAG Settings
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", 5))
    RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", 0.75))
    RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", 500))
    RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", 50))
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


settings = Settings()
