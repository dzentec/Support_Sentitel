import asyncio
import aiosqlite


async def debug_tickets():
    async with aiosqlite.connect("data/support.db") as db:
        cursor = await db.execute(
            "SELECT id, status, subject FROM tickets ORDER BY id DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
        print("Последние тикеты в БД:")
        for row in rows:
            print(f"ID: {row[0]}, Status: {row[1]}, Subject: {row[2]}")


if __name__ == "__main__":
    asyncio.run(debug_tickets())
