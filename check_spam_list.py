import asyncio
import aiosqlite


async def check_spam():
    async with aiosqlite.connect("data/support.db") as db:
        cursor = await db.execute("SELECT * FROM spam_senders")
        rows = await cursor.fetchall()
        print("--- БЛОК-ЛИСТ (spam_senders) ---")
        for row in rows:
            print(f"Email: {row[0]}, Reason: {row[2]}, Added: {row[1]}")


if __name__ == "__main__":
    asyncio.run(check_spam())
