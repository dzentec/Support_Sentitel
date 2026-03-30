import mailparser
from html2text import HTML2Text
import re


def normalize_email(raw_email_bytes):
    """Извлекает текст из email, очищает цитаты и подписи"""
    mail = mailparser.parse_from_bytes(raw_email_bytes)

    sender = mail.from_[0]
    sender_email = sender[1]
    sender_name = sender[0] or sender_email

    subject = mail.subject or "(без темы)"
    message_id = mail.message_id
    references = mail.references
    in_reply_to = mail.in_reply_to

    body = mail.text_plain[0] if mail.text_plain else ""

    lines = body.split("\n")
    cleaned = [l for l in lines if not l.strip().startswith(">")]
    body = "\n".join(cleaned)

    body = re.sub(r"^-- ?\n.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*$", "", body, flags=re.MULTILINE).strip()

    if not body and mail.text_html:
        h = HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        body = h.handle(mail.text_html[0])

    body_for_ai = body[:4000] if len(body) > 4000 else body

    all_refs = []
    if references:
        all_refs.extend(references)
    if in_reply_to:
        all_refs.append(in_reply_to)

    return {
        "message_id": message_id,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": subject,
        "body_normalized": body,
        "body_for_ai": body_for_ai,
        "body_raw": body,
        "thread_references": list(set(all_refs)),
        "is_reply": bool(all_refs),
    }
