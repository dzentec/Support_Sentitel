import asyncio
import aioimaplib
from app.config import settings


async def test_imap():
    print(
        f"Connecting to {settings.IMAP_HOST}:{settings.IMAP_PORT} as {settings.IMAP_USER}..."
    )
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.wait_hello_from_server()  # Correct method name for aioimaplib
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)

        await client.select("INBOX")

        status, data = await client.search("UNSEEN")
        if status == "OK":
            msg_ids = data[0].split()
            print(f"Connection successful. Found {len(msg_ids)} unseen messages.")
        else:
            print(f"Search failed with status: {status}")

        await client.logout()
    except Exception as e:
        print(f"IMAP Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_imap())
