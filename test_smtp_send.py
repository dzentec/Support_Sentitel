import asyncio
from app.services.smtp import send_email
from app.utils.logging import setup_logging


async def main():
    setup_logging()
    recipient = "dzentec@gmail.com"  # Укажите ваш email для теста

    print(f"Отправка тестового письма на {recipient}...")
    try:
        await send_email(
            to=recipient,
            subject="Тест системы AI Support Sentinel",
            body_text="Это тестовое сообщение от системы AI Support Sentinel v3.3. Если вы его получили, SMTP настроен верно.",
        )
        print("Письмо успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке: {e}")


if __name__ == "__main__":
    asyncio.run(main())
