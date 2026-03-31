import aiosmtplib
import uuid
import email.utils
import email.policy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings
from app.utils.logging import logger


def _ensure_brackets(msg_id):
    if not msg_id:
        return None
    msg_id = str(msg_id).strip().replace("<", "").replace(">", "")
    return f"<{msg_id}>"


async def send_email(
    to, subject, body_text, body_html=None, in_reply_to=None, references=None
):
    # Создаем политику, которая не будет разбивать и кодировать заголовки
    custom_policy = email.policy.default.clone(max_line_length=0)

    msg = MIMEMultipart("alternative", policy=custom_policy)
    msg["From"] = f"Support Team <{settings.SMTP_SENDER}>"
    msg["To"] = to
    msg["Subject"] = subject

    # Добавляем дату в формате RFC 2822
    msg["Date"] = email.utils.formatdate(localtime=True)

    # Генерируем уникальный Message-ID
    msg_id = f"<{uuid.uuid4()}@lumiring.com>"
    msg["Message-ID"] = msg_id

    # Прямая установка заголовков без кодирования
    if in_reply_to:
        irt_id = _ensure_brackets(in_reply_to)
        msg["In-Reply-To"] = irt_id

    if references:
        if isinstance(references, list):
            refs = " ".join([_ensure_brackets(ref) for ref in references if ref])
        else:
            refs = _ensure_brackets(references)
        msg["References"] = refs

    # Логируем, что реально уходит в заголовках
    logger.info(
        f"DEBUG: Final headers - In-Reply-To: {msg.get('In-Reply-To')}, References: {msg.get('References')}"
    )

    part1 = MIMEText(body_text, "plain", "utf-8")
    msg.attach(part1)

    if body_html:
        part2 = MIMEText(body_html, "html", "utf-8")
        msg.attach(part2)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=True,
        )
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        raise
