import asyncio
from app.tasks.notification import notify_operator
from app.models import Ticket
from app.utils.logging import setup_logging


async def test_telegram():
    setup_logging()

    # Создаем фиктивный тикет для теста
    mock_ticket = Ticket(
        id=999,
        sender_name="Тестовый Пользователь",
        sender_email="test@example.com",
        subject="Тест уведомления бота",
    )

    print("Отправка тестового уведомления в Telegram...")
    try:
        await notify_operator(
            mock_ticket, "Это тестовый черновик ответа, который сгенерировал ИИ."
        )
        print("Уведомление успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке: {e}")


if __name__ == "__main__":
    asyncio.run(test_telegram())
