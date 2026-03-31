from app.services.telegram_bot import application
from app.config import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def notify_operator(ticket, ai_draft):
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
    draft = ai_draft or "No draft available."
    display_id = ticket.zoho_id or ticket.id

    text = f"🎫 Новый тикет #{display_id}\nОт: {name} ({ticket.sender_email})\nТема: {subject}\n\nЧерновик:\n{draft}"

    await application.bot.send_message(
        chat_id=settings.TELEGRAM_OPERATOR_CHAT_ID,
        text=text[:1000],
        reply_markup=reply_markup,
    )
