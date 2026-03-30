from datetime import datetime, timedelta
from app.database import AsyncSessionLocal
from app.models import Ticket
from app.services.smtp import send_email
from sqlalchemy import select


async def send_final_reply(ticket, text):
    subject = f"Re: {ticket.subject}"
    await send_email(ticket.sender_email, subject, text)
    ticket.final_reply = text


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
