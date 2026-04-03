import asyncio
import aioimaplib
from app.config import settings


async def list_last_10_emails():
    print(f"Connecting to {settings.IMAP_HOST}...")
    try:
        client = aioimaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(settings.IMAP_USER, settings.IMAP_PASS)
        await client.select("INBOX")

        status, data = await client.search("ALL")
        if status == "OK":
            msg_ids = [m.decode() for m in data[0].split()]
            last_10 = msg_ids[-10:]
            print(f"Total messages: {len(msg_ids)}. Showing last {len(last_10)}:")

            for msg_id in reversed(last_10):
                # Fetch only subject
                _, msg_data = await client.fetch(
                    msg_id, "(BODY[HEADER.FIELDS (SUBJECT)])"
                )
                # msg_data format in aioimaplib: [b'ID (BODY[HEADER.FIELDS (SUBJECT)] {length}', b'Subject: ...', b')']
                subject = "Unknown"
                if len(msg_data) > 1:
                    subject = msg_data[1].decode("utf-8", errors="ignore").strip()
                print(f" - #{msg_id}: {subject}")
        else:
            print(f"Search failed: {status}")

        await client.logout()
    except Exception as e:
        print(f"IMAP Error: {e}")


if __name__ == "__main__":
    asyncio.run(list_last_10_emails())
