# 🤖 AI Support Sentinel v3.3

An automated email support handling system, running in a single container. 🚀

## ✨ Key Features

- 📧 **Automation**: IMAP polling with thread management, Zoho ticket ID extraction, spam filtering with Gemini, and automatic escalation/cleanup tasks.
- 💬 **Support**: Telegram integration for ticket management (approve, edit, query tech specs) with a new status workflow (New, Open, Pending, Closed).
- 🛡️ **Reliability**: Robust SMTP multipart handling, SQLite with WAL, automatic ticket closing (72h), persistent task management, and error fallback.
- 🔐 **Security**: Telegram access control via whitelist.
- 📊 **Monitoring**: Structured logging, interactive TUI, and real-time status dashboard with escalation reminders.
- ⚙️ **Configurable**: Adjustable IMAP polling intervals and escalation thresholds.

## 🛠️ Technology Stack
...
## 🚀 Deployment

1. Clone the repository.
2. Create a `.env` file based on `.env.example` and fill in your variables, including `ALLOWED_TELEGRAM_IDS`, `IMAP_POLL_INTERVAL`, and escalation thresholds.
3. Start the system: `docker-compose up -d`


---
*Developed for Lumiring.*
