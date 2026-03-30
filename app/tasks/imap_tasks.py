import asyncio
from app.services.email_parser import normalize_email
from app.services.gemini import classify_and_draft
from app.services.smtp import send_email
from app.models import Ticket, TicketEvent, SpamSender
from app.database import AsyncSessionLocal
from app.tasks.notification import notify_operator
from sqlalchemy import select
import json


async def process_email(raw_email_bytes):
    email_data = normalize_email(raw_email_bytes)
    msg_id = email_data["message_id"]

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(Ticket).where(Ticket.message_id == msg_id)
        )
        if existing.scalar_one_or_none():
            return

        spammer = await session.execute(
            select(SpamSender).where(SpamSender.email == email_data["sender_email"])
        )
        if spammer.scalar():
            event = TicketEvent(
                event_type="blocked_by_blocklist", payload=json.dumps(email_data)
            )
            session.add(event)
            await session.commit()
            return

        gemini_result = await classify_and_draft(email_data)

        if gemini_result["classification"] == "spam":
            # Assuming handle_spam logic is minimal or handled here
            spammer = SpamSender(
                email=email_data["sender_email"], reason="AI detected spam"
            )
            session.add(spammer)
            await session.commit()
            return

        ticket = Ticket(
            message_id=msg_id,
            thread_references=json.dumps(email_data["thread_references"]),
            sender_email=email_data["sender_email"],
            sender_name=email_data["sender_name"],
            subject=email_data["subject"],
            body_normalized=email_data["body_normalized"],
            body_raw=email_data["body_raw"],
            category=gemini_result.get("category"),
            spam_confidence=gemini_result.get("confidence"),
            ai_draft=gemini_result.get("draft_reply"),
            status="awaiting_operator",
        )
        session.add(ticket)
        await session.flush()

        # Simple auto-reply implementation placeholder
        # await send_email(...)

        event = TicketEvent(ticket_id=ticket.id, event_type="ticket_created")
        session.add(event)
        await session.commit()

        await notify_operator(ticket, gemini_result.get("draft_reply"))
