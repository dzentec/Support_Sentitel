import aiosmtplib
from email.message import EmailMessage
from app.config import settings
from app.utils.logging import logger


def _ensure_brackets(msg_id):
    if not msg_id:
        return None
    msg_id = msg_id.strip()
    if not msg_id.startswith("<"):
        msg_id = f"<{msg_id}"
    if not msg_id.endswith(">"):
        msg_id = f"{msg_id}>"
    return msg_id


async def send_email(
    to, subject, body_text, body_html=None, in_reply_to=None, references=None
):
    message = EmailMessage()
    message["From"] = settings.SMTP_SENDER
    message["To"] = to
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = _ensure_brackets(in_reply_to)
    if references:
        # References header should be a space-separated string
        if isinstance(references, list):
            message["References"] = " ".join(
                [_ensure_brackets(ref) for ref in references if ref]
            )
        else:
            message["References"] = _ensure_brackets(references)

    message.set_content(body_text)
    if body_html:
        message.add_alternative(body_html, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=True,
        )
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        raise
