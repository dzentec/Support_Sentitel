from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.config import settings
from app.utils.logging import logger
from app.database import AsyncSessionLocal
from app.models import Ticket, SpamSender, PendingEdit
from app.tasks.ticket_tasks import send_final_reply, close_ticket
from app.scheduler import scheduler
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.services.templates import render_email_template

# Global start time
START_TIME = datetime.utcnow()

application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
logger.info("Telegram bot application instance created.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Status", "Pending"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Бот запущен.", reply_markup=reply_markup)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        processed = await session.scalar(select(func.count()).select_from(Ticket))
        sent = await session.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status.in_(["awaiting_client", "closed"]))
        )
        pending = await session.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == "awaiting_operator")
        )

    uptime = datetime.utcnow() - START_TIME
    text = (
        f"⚙️ Статус системы:\n\n"
        f"⏳ Uptime: {str(uptime).split('.')[0]}\n"
        f"📦 Processed: {processed or 0}\n"
        f"📤 Sent: {sent or 0}\n"
        f"📥 Pending: {pending or 0}"
    )
    await update.message.reply_text(text)


async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.status == "awaiting_operator").limit(10)
        )
        tickets = result.scalars().all()

    if not tickets:
        await update.message.reply_text("Нет активных тикетов в ожидании.")
        return

    text = "📥 Активные тикеты (ожидают оператора):"
    keyboard = []
    for t in tickets:
        display_id = t.zoho_id or t.id
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"#{display_id} - {t.subject}", callback_data=f"show|{t.id}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def send_ticket_details(bot, chat_id, ticket):
    keyboard = [
        [
            InlineKeyboardButton(
                "Query Tech spec ACS", callback_data=f"query_acs|{ticket.id}"
            ),
            InlineKeyboardButton(
                "Query Tech spec WW", callback_data=f"query_ww|{ticket.id}"
            ),
        ],
        [
            InlineKeyboardButton("Одобрить", callback_data=f"approve|{ticket.id}"),
            InlineKeyboardButton("Редактировать", callback_data=f"edit|{ticket.id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    name = ticket.sender_name or "Unknown"
    subject = ticket.subject or "(no subject)"
    draft = ticket.ai_draft or "No draft available."
    display_id = ticket.zoho_id or ticket.id

    text = f"🎫 Тикет #{display_id}\nОт: {name}\nТема: {subject}\n\nЧерновик:\n{draft}"
    await bot.send_message(chat_id, text, reply_markup=reply_markup)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"DEBUG: Callback received! Data: {query.data}")
    logger.info(f"Callback received: {query.data}")
    await query.answer()

    try:
        data = query.data
        action, ticket_id = data.split("|")
        ticket_id = int(ticket_id)

        async with AsyncSessionLocal() as session:
            ticket = await session.get(Ticket, ticket_id)
            if not ticket:
                await query.edit_message_text("Тикет не найден.")
                return

            if action == "show":
                await query.delete_message()
                await send_ticket_details(context.bot, query.message.chat_id, ticket)

            elif action in ["query_acs", "query_ww"]:
                template = (
                    "tech_query.txt" if action == "query_acs" else "tech_query_ww.txt"
                )
                draft = render_email_template(
                    template, {"ticket_id": ticket.zoho_id or ticket.id}
                )
                ticket.ai_draft = draft
                await session.commit()
                await query.delete_message()
                await send_ticket_details(context.bot, query.message.chat_id, ticket)

            elif action == "approve":
                await send_final_reply(ticket, ticket.ai_draft)
                ticket.status = "awaiting_client"
                ticket.replied_at = datetime.utcnow()
                await session.commit()
                display_id = ticket.zoho_id or ticket.id
                await query.edit_message_text(
                    f"✅ Ответ отправлен на тикет #{display_id}"
                )

            elif action == "edit":
                # Используем merge для обновления или создания записи
                pending = PendingEdit(
                    chat_id=query.message.chat_id, ticket_id=ticket.id
                )
                await session.merge(pending)
                await session.commit()

                # Обновляем сообщение и отправляем черновик для редактирования
                await query.edit_message_text(
                    "✏️ Редактирование начато. Ответьте на следующее сообщение с вашим исправленным текстом:"
                )
                # Отправляем черновик как отдельное сообщение для удобного Reply/Quote
                await query.message.reply_text(
                    f"```\n{ticket.ai_draft}\n```", parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"Callback Error: {e}", exc_info=True)
        await query.message.reply_text(f"Ошибка: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        logger.info("Message handler: no reply_to_message")
        return

    async with AsyncSessionLocal() as session:
        logger.info(f"Looking for PendingEdit for chat_id: {msg.chat_id}")

        result = await session.execute(
            select(PendingEdit).where(PendingEdit.chat_id == msg.chat_id)
        )
        pending = result.scalar_one_or_none()

        if pending:
            logger.info(f"Found pending edit for ticket: {pending.ticket_id}")
            ticket = await session.get(Ticket, pending.ticket_id)
            if ticket:
                ticket.ai_draft = msg.text
                await session.commit()

                await session.delete(pending)
                await session.commit()

                await msg.reply_text("✅ Черновик обновлен.")
                # Вызов отправки карточки
                await send_ticket_details(context.bot, msg.chat_id, ticket)
                logger.info("Sent updated ticket details to operator")
            else:
                logger.error("Pending record found, but ticket not found in DB")
        else:
            logger.info("No pending edit found for this chat")


def setup_bot_handlers():
    logger.info("Registering bot handlers...")

    # 1. Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("pending", list_pending))

    # 2. Обработка текстовых кнопок меню
    application.add_handler(MessageHandler(filters.Text(["Status"]), status))
    application.add_handler(MessageHandler(filters.Text(["Pending"]), list_pending))

    # 3. Регистрация CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 4. Обработка текстовых ответов
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )
    logger.info("All handlers registered successfully.")
