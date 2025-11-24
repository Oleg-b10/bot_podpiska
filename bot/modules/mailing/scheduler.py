from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.modules.mailing.sender import run_mailing

scheduler = AsyncIOScheduler()

def schedule_mailing(mailing_id: int, run_at=None):
    scheduler.add_job(run_mailing, "date", run_date=run_at, args=[mailing_id])

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
