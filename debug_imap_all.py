import asyncio
import aioimaplib
from app.config import settings
import logging

# Настройка простого логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_imap():
    print(f"Connecting to {settings.IMAP_HOST}...")
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)

        # Список папок
        print("Список папок:")
        status, data = await client.list("", "*")
        for folder in data:
            print(f" - {folder}")

        await client.select("INBOX")

        # Поиск всех сообщений, не только UNSEEN
        print("Поиск всех сообщений (ALL)...")
        status, data = await client.search("ALL")
        if status == "OK":
            msg_ids = data[0].split()
            print(f"Найдено сообщений (ALL): {len(msg_ids)}")
            if msg_ids:
                print(f"Последний ID: {msg_ids[-1]}")
        else:
            print(f"Поиск ALL не удался: {status}")

        # Поиск UNSEEN
        print("Поиск непрочитанных (UNSEEN)...")
        status, data = await client.search("UNSEEN")
        if status == "OK":
            msg_ids = data[0].split()
            print(f"Найдено непрочитанных: {len(msg_ids)}")
        else:
            print(f"Поиск UNSEEN не удался: {status}")

        await client.logout()
    except Exception as e:
        print(f"Ошибка IMAP: {e}")


if __name__ == "__main__":
    asyncio.run(debug_imap())
