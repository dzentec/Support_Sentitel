import json
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal
from app.models import Ticket
from app.services.smtp import send_email
from sqlalchemy import select
from app.config import settings
from app.tasks.notification import notify_operator
from app.utils.logging import logger


def get_reminder_trigger(ticket: Ticket):
    if not ticket.created_at:
        return None
    elapsed = (datetime.utcnow() - ticket.created_at).total_seconds() / 60
    sent_intervals = (
        ticket.reminders_sent_intervals.split(",")
        if ticket.reminders_sent_intervals
        else []
    )
    for interval in settings.REMINDER_INTERVALS:
        if interval <= elapsed < interval + 5:  # 5-minute window for polling
            if str(interval) not in sent_intervals:
                return interval
    return None


async def send_final_reply(ticket, text):
    subject = f"Re: {ticket.subject}"
    final_text = text if text else "Thank you for your request. We are processing it."

    # Parse JSON string from DB to list
    references = (
        json.loads(ticket.thread_references) if ticket.thread_references else None
    )

    # Передаем заголовки для ветки
    await send_email(
        ticket.sender_email,
        subject,
        final_text,
        in_reply_to=ticket.message_id,
        references=references,
    )
    ticket.final_reply = final_text


async def close_ticket(ticket_id):
    async with AsyncSessionLocal() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket and ticket.status != "closed":
            ticket.status = "closed"
            ticket.closed_at = datetime.utcnow()
            await session.commit()
            # Send close warning email
            await send_email(
                ticket.sender_email,
                "Обращение закрыто",
                "Ваше обращение было закрыто в связи с отсутствием ответа.",
            )


async def check_reminders():
    async with AsyncSessionLocal() as session:
        tickets = await session.execute(select(Ticket).where(Ticket.status == "open"))


# ...
async def check_auto_close():
    async with AsyncSessionLocal() as session:
        tickets = await session.execute(
            select(Ticket).where(Ticket.status.in_(["pending", "in_progress"]))
        )

        for ticket in tickets.scalars().all():
            interval = get_reminder_trigger(ticket)
            if interval:
                await notify_operator(ticket, ticket.ai_draft, reminder=True)

                sent_intervals = (
                    ticket.reminders_sent_intervals.split(",")
                    if ticket.reminders_sent_intervals
                    else []
                )
                sent_intervals.append(str(interval))
                ticket.reminders_sent_intervals = ",".join(sent_intervals)

                await session.commit()
                logger.info(f"Reminder sent for ticket {ticket.id} after {interval}m")


async def check_auto_close():
    async with AsyncSessionLocal() as session:
        tickets = await session.execute(
            select(Ticket).where(Ticket.status.in_(["awaiting_client", "in_progress"]))
        )
        for ticket in tickets.scalars().all():
            if not ticket.replied_at:
                continue
            if (
                datetime.utcnow() - ticket.replied_at
            ).total_seconds() / 3600 >= settings.AUTO_CLOSE_TIMEOUT_HOURS:
                ticket.status = "closed"
                ticket.closed_at = datetime.utcnow()
                await session.commit()
                await send_email(
                    ticket.sender_email,
                    "Ticket Closed",
                    "Your ticket has been closed due to inactivity. Feel free to open a new one if needed.",
                )
                logger.info(f"Ticket {ticket.id} auto-closed")
