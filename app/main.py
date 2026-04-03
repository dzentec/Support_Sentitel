from fastapi import FastAPI
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.telegram_bot import setup_bot_handlers
from app.bot_instance import application
from app.utils.logging import logger
from contextlib import asynccontextmanager
from app.services.imap import poll_imap
from app.tasks.ticket_tasks import check_reminders, check_auto_close
from app.config import settings
from app.scheduler import scheduler
from app.rag.indexer import index_all_documents
from app.api.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan...")
    await init_db()
    start_scheduler()

    # RAG Indexing
    logger.info("RAG: Starting knowledge base indexing...")
    try:
        stats = await index_all_documents()
        logger.info(f"RAG: Indexing complete. Stats: {stats}")
    except Exception as e:
        logger.error(f"RAG: Indexing failed: {e}", exc_info=True)

    # Регистрация задач
    scheduler.add_job(
        poll_imap,
        "interval",
        minutes=settings.IMAP_POLL_INTERVAL,
        id="poll_imap",
        replace_existing=True,
    )
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=15,
        id="check_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        check_auto_close,
        "interval",
        hours=1,
        id="check_auto_close",
        replace_existing=True,
    )
    logger.info(
        f"Tasks scheduled. IMAP polling interval: {settings.IMAP_POLL_INTERVAL} min"
    )

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
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "AI Support Sentinel API is running (Polling mode)"}
