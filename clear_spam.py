import asyncio
import aiosqlite


async def clear_spam():
    async with aiosqlite.connect("data/support.db") as db:
        await db.execute("DELETE FROM spam_senders")
        await db.commit()
        print("Spam list cleared.")


if __name__ == "__main__":
    asyncio.run(clear_spam())
