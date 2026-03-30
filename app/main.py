from fastapi import FastAPI
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.telegram_bot import application, setup_bot_handlers
from app.utils.logging import logger
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan...")
    await init_db()
    start_scheduler()
    setup_bot_handlers()
    # Инициализация приложения бота
    await application.initialize()
    logger.info("Bot initialized")
    await application.start()
    logger.info("Bot started")
    # Принудительно сбрасываем вебхук перед началом polling
    await application.bot.delete_webhook(drop_pending_updates=True)
    # Разрешаем сообщения и callback_query
    await application.updater.start_polling(
        allowed_updates=["message", "callback_query"]
    )
    logger.info("Polling started with allowed_updates=['message', 'callback_query']")

    yield
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "AI Support Sentinel API is running (Polling mode)"}
