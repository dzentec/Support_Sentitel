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

# Global start time
START_TIME = datetime.utcnow()

application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Status"]]
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


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action, ticket_id = data.split("|")
    ticket_id = int(ticket_id)

    async with AsyncSessionLocal() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            await query.edit_message_text("Тикет не найден.")
            return

        if action == "approve":
            await send_final_reply(ticket, ticket.ai_draft)
            ticket.status = "awaiting_client"
            ticket.replied_at = datetime.utcnow()

            job_id = f"close_ticket_{ticket.id}"
            scheduler.add_job(
                close_ticket,
                "date",
                run_date=datetime.utcnow() + timedelta(hours=48),
                id=job_id,
                args=[ticket.id],
            )
            ticket.close_job_id = job_id
            await session.commit()
            await query.edit_message_text(f"✅ Ответ отправлен на тикет #{ticket.id}")

        elif action == "edit":
            # Just a placeholder for now as we don't have the full card logic here
            pending = PendingEdit(chat_id=query.message.chat_id, ticket_id=ticket.id)
            session.add(pending)
            await session.commit()
            await query.edit_message_text(
                "✏️ Редактирование начато. Напишите новый текст ответа."
            )

        elif action == "spam":
            ticket.status = "spam_confirmed"
            spammer = SpamSender(
                email=ticket.sender_email, reason="confirmed by operator"
            )
            session.add(spammer)
            await session.commit()
            await query.edit_message_text(f"🚫 Тикет #{ticket.id} помечен как спам.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PendingEdit).where(PendingEdit.chat_id == msg.chat_id)
        )
        pending = result.scalar_one_or_none()
        if pending:
            ticket = await session.get(Ticket, pending.ticket_id)
            if ticket:
                await send_final_reply(ticket, msg.text)
                ticket.status = "awaiting_client"
                ticket.replied_at = datetime.utcnow()
                await session.commit()
                await msg.reply_text("✅ Ответ отправлен.")
                await session.delete(pending)
                await session.commit()


def setup_bot_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.Text(["Status"]), status))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )


async def set_webhook():
    await application.bot.set_webhook(f"{settings.WEBHOOK_URL}/webhook/tg")
