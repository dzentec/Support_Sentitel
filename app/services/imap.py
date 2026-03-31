import aioimaplib
from app.config import settings
from app.tasks.imap_tasks import process_email
from app.utils.logging import logger


async def poll_imap():
    """Подключается к IMAP, получает непрочитанные письма, обрабатывает"""
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)
        await client.select("INBOX")

        # Поиск только непрочитанных (UNSEEN)
        logger.info("Searching for UNSEEN messages...")
        status, data = await client.search("UNSEEN")
        if status != "OK":
            logger.warning("No new messages found or search failed.")
            return

        msg_ids = [msg_id.decode("utf-8") for msg_id in data[0].split()]
        logger.info(f"Found {len(msg_ids)} new unread messages.")

        # Обрабатываем все письма от новых к старым
        for msg_id in reversed(msg_ids):
            try:
                logger.info(f"Fetching message {msg_id}")
                _, msg_data = await client.fetch(str(msg_id), "(BODY.PEEK[])")
                # Проверяем, что msg_data содержит данные (иногда сервер возвращает другой формат)
                if len(msg_data) < 2:
                    logger.error(f"Message {msg_id} returned no data: {msg_data}")
                    continue
                raw_email = msg_data[1]

                await process_email(raw_email)

                # Отмечаем как прочитанное после успешной обработки
                await client.store(msg_id, "+FLAGS", "\\Seen")
                logger.info(f"Message {msg_id} processed and marked as read.")

            except Exception as e:
                # Если письмо не обработалось, оно останется UNSEEN и будет попытка снова
                logger.error(f"Failed to process message {msg_id}: {e}")

        await client.logout()
    except Exception as e:
        logger.error(f"IMAP polling error: {e}")
