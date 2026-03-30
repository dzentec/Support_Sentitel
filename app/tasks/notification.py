from app.services.telegram_bot import application
from app.config import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def notify_operator(ticket, ai_draft):
    keyboard = [
        [
            InlineKeyboardButton("Одобрить", callback_data=f"approve|{ticket.id}"),
            InlineKeyboardButton("Редактировать", callback_data=f"edit|{ticket.id}"),
        ],
        [InlineKeyboardButton("Спам", callback_data=f"spam|{ticket.id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"🆕 Новый тикет #{ticket.id}\nОт: {ticket.sender_name} ({ticket.sender_email})\nТема: {ticket.subject}\n\nЧерновик:\n{ai_draft}"

    await application.bot.send_message(
        chat_id=settings.TELEGRAM_OPERATOR_CHAT_ID,
        text=text[:1000],
        reply_markup=reply_markup,
    )
