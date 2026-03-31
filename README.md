# 🤖 AI Support Sentinel v3.3

An automated email support handling system, running in a single container. 🚀

## ✨ Key Features

- 📧 **Automation**: IMAP polling, spam filtering with Gemini, auto-replies to customers.
- 💬 **Support**: Telegram integration for ticket management (approve, edit, snooze) and automated technical spec query templates.
- 🛡️ **Reliability**: SQLite with WAL, persistent APScheduler task management, and robust error fallback mechanisms.
- 📊 **Monitoring**: Structured logging and an interactive TUI for real-time debugging.

## 🛠️ Technology Stack

- 🐍 Python 3.11
- ⚡ FastAPI
- 💾 SQLite
- 🤖 Google Gemini 2.5 Flash-lite
- ✈️ Telegram Bot API
- 🖥️ Textual (TUI)
- 🐳 Docker & Docker Compose

## 🚀 Deployment

1. Clone the repository.
2. Create a `.env` file based on `.env.example` and fill in your variables.
3. Start the system: `docker-compose up -d`

---
*Developed for Lumiring.*
