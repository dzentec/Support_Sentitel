from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, unique=True, nullable=False)
    thread_references = Column(Text)
    sender_email = Column(String, nullable=False)
    sender_name = Column(String)
    subject = Column(String)
    body_normalized = Column(Text)
    body_raw = Column(Text)
    category = Column(
        String, CheckConstraint("category IN ('billing','technical','general','other')")
    )
    spam_confidence = Column(Float)
    ai_draft = Column(Text)
    final_reply = Column(Text)
    status = Column(String, default="awaiting_operator")
    snooze_count = Column(Integer, default=0)
    snooze_until = Column(DateTime)
    tg_message_id = Column(Integer)
    tg_chat_id = Column(Integer)
    tg_edit_prompt_msg_id = Column(Integer)
    close_job_id = Column(String)
    created_at = Column(DateTime, default=func.now())
    auto_reply_sent_at = Column(DateTime)
    operator_action_at = Column(DateTime)
    replied_at = Column(DateTime)
    close_warning_sent_at = Column(DateTime)
    closed_at = Column(DateTime)


class TicketEvent(Base):
    __tablename__ = "ticket_events"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    event_type = Column(String, nullable=False)
    actor = Column(String, default="system")
    payload = Column(Text)
    created_at = Column(DateTime, default=func.now())


class SpamSender(Base):
    __tablename__ = "spam_senders"
    email = Column(String, primary_key=True)
    added_at = Column(DateTime, default=func.now())
    reason = Column(String)
    count = Column(Integer, default=1)


class PendingEdit(Base):
    __tablename__ = "pending_edits"
    chat_id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
