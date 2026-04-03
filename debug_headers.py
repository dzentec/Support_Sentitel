import asyncio
import aioimaplib
from app.config import settings
import mailparser


async def debug_first_email():
    print(f"Подключение к {settings.IMAP_HOST}...")
    client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    await client.wait_hello_from_server()
    await client.login(settings.IMAP_USER, settings.IMAP_PASS)
    await client.select("INBOX")

    status, data = await client.search("UNSEEN")
    if status == "OK":
        msg_ids = data[0].split()
        if msg_ids:
            msg_id = msg_ids[0]
            print(f"Получение заголовков письма {msg_id}...")
            status, msg_data = await client.fetch(msg_id, "(RFC822)")
            print(f"Status: {status}")
            print(f"Data content: {msg_data}")

        else:
            print("Нет новых писем для отладки.")

    await client.logout()


if __name__ == "__main__":
    asyncio.run(debug_first_email())
