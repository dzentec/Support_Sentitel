import asyncio
from app.services.imap import poll_imap
from app.utils.logging import setup_logging


async def main():
    setup_logging()
    print("Запуск polling IMAP...")
    try:
        await poll_imap()
        print("Polling завершен.")
    except Exception as e:
        print(f"Ошибка при polling IMAP: {e}")


if __name__ == "__main__":
    asyncio.run(main())
