import aiosqlite
import asyncio


async def check_db():
    try:
        async with aiosqlite.connect("data/support.db") as db:
            cursor = await db.execute("SELECT count(*) FROM tickets")
            count = await cursor.fetchone()
            print(f"Total tickets: {count[0]}")

            cursor = await db.execute(
                "SELECT id, subject, sender_email FROM tickets LIMIT 5"
            )
            rows = await cursor.fetchall()
            for row in rows:
                print(f" - #{row[0]}: {row[1]} from {row[2]}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_db())
