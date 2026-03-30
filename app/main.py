from fastapi import FastAPI
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.telegram_bot import application, setup_bot_handlers
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    setup_bot_handlers()
    # Initialize bot webhook/polling if needed
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "AI Support Sentinel API is running"}
