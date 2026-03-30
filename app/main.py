from fastapi import FastAPI, Request
from telegram import Update
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.telegram_bot import application, setup_bot_handlers
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    setup_bot_handlers()
    # Инициализация приложения бота
    await application.initialize()
    await application.start()
    yield
    await application.stop()
    await application.shutdown()
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook/tg")
async def telegram_webhook(request: Request):
    update_dict = await request.json()
    update = Update.de_json(data=update_dict, bot=application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "AI Support Sentinel API is running"}
