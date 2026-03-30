import aiosmtplib
from email.message import EmailMessage
from app.config import settings
from app.utils.logging import logger


async def send_email(to, subject, body):
    message = EmailMessage()
    message["From"] = settings.SMTP_SENDER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

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
