import aioimaplib
from app.config import settings
from app.tasks.imap_tasks import process_email
from app.utils.logging import logger


async def poll_imap():
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)
        await client.select("INBOX")

        _, data = await client.search("UNSEEN")
        msg_ids = data[0].split()
        for msg_id in msg_ids:
            _, msg_data = await client.fetch(msg_id, "(RFC822)")
            raw_email = msg_data[1]
            await process_email(raw_email)
            await client.store(msg_id, "+FLAGS", "\\Seen")

        await client.logout()
    except Exception as e:
        logger.error(f"IMAP polling error: {e}")
