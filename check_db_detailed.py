import asyncio
import aiosqlite


async def debug_tickets():
    async with aiosqlite.connect("data/support.db") as db:
        cursor = await db.execute(
            "SELECT id, message_id, status, sender_email, subject FROM tickets ORDER BY id DESC"
        )
        rows = await cursor.fetchall()
        print("--- ВСЕ ТИКЕТЫ В БД ---")
        for row in rows:
            print(
                f"ID: {row[0]}, Status: {row[2]}, Sender: {row[3]}, Subject: {row[4]}"
            )


if __name__ == "__main__":
    asyncio.run(debug_tickets())
