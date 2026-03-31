from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.bot_instance import application
from app.config import settings
from app.utils.logging import logger
from app.database import AsyncSessionLocal
from app.models import Ticket, SpamSender, PendingEdit
from app.tasks.ticket_tasks import send_final_reply, close_ticket
from app.services.imap import poll_imap
from app.scheduler import scheduler
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.services.templates import render_email_template

# Global start time
START_TIME = datetime.utcnow()

logger.info("Telegram bot application instance imported.")


async def check_access(update: Update):
    user_id = update.effective_user.id
    if user_id not in settings.ALLOWED_TELEGRAM_IDS:
        logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
        if update.message:
            await update.message.reply_text(f"Access denied. Your ID: {user_id}")
        elif update.callback_query:
            await update.callback_query.answer(
                f"Access denied. Your ID: {user_id}", show_alert=True
            )
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    keyboard = [["Status", "Pending", "New & Open"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Bot started.", reply_markup=reply_markup)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    async with AsyncSessionLocal() as session:
        # Counters by new statuses: New, Open, Pending, Closed
        new_count = await session.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.status == "new")
        )
        open_count = await session.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.status == "open")
        )
        pending_count = await session.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.status == "pending")
        )
        closed_count = await session.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.status == "closed")
        )

    uptime = datetime.utcnow() - START_TIME
    text = (
        f"⚙️ System Status:\n\n"
        f"⏱ Uptime: {str(uptime).split('.')[0]}\n"
        f"🆕 New: {new_count or 0}\n"
        f"📂 Open: {open_count or 0}\n"
        f"⏳ Pending: {pending_count or 0}\n"
        f"✅ Closed: {closed_count or 0}"
    )

    keyboard = [[InlineKeyboardButton("Check New Tickets", callback_data="check_now")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)


async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.status == "pending").limit(10)
        )
        tickets = result.scalars().all()

    if not tickets:
        await update.message.reply_text("No tickets in Pending status.")
        return

    text = "⏳ Tickets Pending:"
    await send_ticket_list(update, tickets, text)


async def list_new_and_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.status.in_(["new", "open"])).limit(10)
        )
        tickets = result.scalars().all()

    if not tickets:
        await update.message.reply_text("No New or Open tickets.")
        return

    text = "📂 Tickets in Progress (New & Open):"
    await send_ticket_list(update, tickets, text)


async def send_ticket_list(update, tickets, text):
    keyboard = []
    for t in tickets:
        display_id = t.zoho_id or t.id
        # Add date/time to button text, format: DD/MM/YYYY HH:MM
        time_str = t.replied_at.strftime("%d/%m/%Y %H:%M") if t.replied_at else "---"
        # Since Telegram buttons don't support right alignment, we include the time at the end.
        button_text = f"#{display_id} | {t.subject[:15]}... | {time_str}"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"show|{t.id}")]
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
            InlineKeyboardButton("Approve", callback_data=f"approve|{ticket.id}"),
            InlineKeyboardButton("Edit", callback_data=f"edit|{ticket.id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    name = ticket.sender_name or "Unknown"
    subject = ticket.subject or "(no subject)"
    draft = ticket.ai_draft or "No draft available."
    display_id = ticket.zoho_id or ticket.id

    text = (
        f"🎫 Ticket #{display_id}\nFrom: {name}\nSubject: {subject}\n\nDraft:\n{draft}"
    )
    await bot.send_message(chat_id, text, reply_markup=reply_markup)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    query = update.callback_query
    print(f"DEBUG: Callback received! Data: {query.data}")
    logger.info(f"Callback received: {query.data}")
    await query.answer()

    try:
        data = query.data
        if "|" in data:
            action, ticket_id = data.split("|")
            ticket_id = int(ticket_id)
        else:
            action = data
            ticket_id = None

        async with AsyncSessionLocal() as session:
            if ticket_id:
                ticket = await session.get(Ticket, ticket_id)
                if not ticket:
                    await query.edit_message_text("Ticket not found.")
                    return
            else:
                ticket = None

            if action == "show":
                await query.delete_message()
                await send_ticket_details(context.bot, query.message.chat_id, ticket)

            elif action == "check_now":
                await query.edit_message_text("🔄 Checking mail...")
                await poll_imap()
                await query.edit_message_text("✅ Check completed.")

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
                ticket.status = "pending"
                ticket.replied_at = datetime.utcnow()
                await session.commit()
                display_id = ticket.zoho_id or ticket.id
                await query.edit_message_text(
                    f"✅ Reply sent for ticket #{display_id}. Status: pending"
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
                    "✏️ Editing started. Reply to the next message with your corrected text:"
                )
                # Отправляем черновик как отдельное сообщение для удобного Reply/Quote
                await query.message.reply_text(
                    f"```\n{ticket.ai_draft}\n```", parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"Callback Error: {e}", exc_info=True)
        await query.message.reply_text(f"Error: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
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

                await msg.reply_text("✅ Draft updated.")
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
    application.add_handler(CommandHandler("newopen", list_new_and_open))

    # 2. Обработка текстовых кнопок меню
    application.add_handler(MessageHandler(filters.Text(["Status"]), status))
    application.add_handler(MessageHandler(filters.Text(["Pending"]), list_pending))
    application.add_handler(
        MessageHandler(filters.Text(["New & Open"]), list_new_and_open)
    )

    # 3. Регистрация CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 4. Обработка текстовых ответов
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )
    logger.info("All handlers registered successfully.")
