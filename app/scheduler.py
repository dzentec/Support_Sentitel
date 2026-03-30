from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.config import settings

jobstores = {"default": SQLAlchemyJobStore(url=settings.SCHEDULER_DB_URL)}

scheduler = AsyncIOScheduler(jobstores=jobstores)


def start_scheduler():
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
