import asyncio
import aioimaplib
from app.config import settings


async def find_email():
    print(f"Connecting to {settings.IMAP_HOST}...")
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)
        await client.select("INBOX")

        # Search for subject specifically
        subject_to_find = "#3968 Problem with RFID Readers 102"
        # IMAP search SUBJECT is case insensitive usually
        status, data = await client.search(f'SUBJECT "{subject_to_find}"')

        if status == "OK":
            msg_ids = data[0].split()
            print(f"Found {len(msg_ids)} messages with subject: '{subject_to_find}'")
            for msg_id in msg_ids:
                print(f" - Message ID on server: {msg_id.decode()}")
        else:
            print(f"Search failed with status: {status}")

        await client.logout()
    except Exception as e:
        print(f"IMAP Error: {e}")


if __name__ == "__main__":
    asyncio.run(find_email())
