from fastapi import FastAPI
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "AI Support Sentinel API is running"}
