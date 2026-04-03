import asyncio
import aiosqlite


async def clear_all_data():
    try:
        async with aiosqlite.connect("data/support.db") as db:
            await db.execute("DELETE FROM tickets")
            await db.execute("DELETE FROM ticket_events")
            await db.execute("DELETE FROM pending_edits")
            await db.execute("DELETE FROM spam_senders")
            await db.commit()
            print("Database tables cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")


if __name__ == "__main__":
    asyncio.run(clear_all_data())
