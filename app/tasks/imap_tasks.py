import asyncio
import json
from sqlalchemy import select
from app.config import settings
from app.utils.logging import logger
from app.services.email_parser import normalize_email
from app.services.gemini import classify_and_draft
from app.services.smtp import send_email
from app.models import Ticket, TicketEvent
from app.database import AsyncSessionLocal
from app.tasks.notification import notify_operator
from app.services.templates import render_email_template


async def process_email(raw_email_bytes):
    email_data = normalize_email(raw_email_bytes)
    msg_id = email_data["message_id"]

    # 1. Проверка белого списка
    if (
        settings.WHITELISTED_SENDERS
        and email_data["sender_email"] not in settings.WHITELISTED_SENDERS
    ):
        logger.info(f"Sender {email_data['sender_email']} not in whitelist, skipping.")
        return

    async with AsyncSessionLocal() as session:
        # Дедупликация
        existing = await session.execute(
            select(Ticket).where(Ticket.message_id == msg_id)
        )
        if existing.scalar_one_or_none():
            return

        # 2. Анализ релевантности через Gemini
        gemini_result = await classify_and_draft(email_data)

        # 3. Если спам - просто игнорируем (никаких списков)
        if gemini_result.get("classification") == "spam":
            logger.info(f"Message {msg_id} classified as SPAM/Irrelevant. Discarding.")
            return

        # 4. Если не спам - полный цикл обработки
        try:
            ticket = Ticket(
                message_id=msg_id,
                zoho_id=email_data.get("zoho_id"),
                thread_references=json.dumps(email_data["thread_references"]),
                sender_email=email_data["sender_email"],
                sender_name=email_data["sender_name"],
                subject=email_data["subject"],
                body_normalized=email_data["body_normalized"],
                body_raw=email_data["body_raw"],
                category=gemini_result.get("category"),
                spam_confidence=gemini_result.get("confidence"),
                ai_draft=gemini_result.get("draft_reply"),
                status="new",
            )
            session.add(ticket)
            await session.flush()

            # Отправка автоответа
            subject = f"Your request has been received [Ticket #{ticket.zoho_id or ticket.id}]"
            body_text = render_email_template(
                "auto_reply.txt",
                {
                    "ticket_id": ticket.zoho_id or ticket.id,
                    "sender_name": ticket.sender_name,
                    "subject": ticket.subject,
                },
            )
            body_html = render_email_template(
                "auto_reply.html",
                {
                    "ticket_id": ticket.zoho_id or ticket.id,
                    "sender_name": ticket.sender_name,
                    "subject": ticket.subject,
                },
            )
            # Передаем In-Reply-To и References
            await send_email(
                ticket.sender_email,
                subject,
                body_text,
                body_html=body_html,
                in_reply_to=email_data["message_id"],
                references=email_data["thread_references"],
            )

            event = TicketEvent(ticket_id=ticket.id, event_type="ticket_created")
            session.add(event)
            await session.commit()
            logger.info(f"Successfully created ticket ID: {ticket.id}")

            await notify_operator(ticket, gemini_result.get("draft_reply"))
        except Exception as e:
            logger.error(f"Failed to create ticket in DB: {e}", exc_info=True)
            await session.rollback()
