# app/automation.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

logger = logging.getLogger("app.automation")

def scheduled_fetch_job(fetch_func, tickers):
    """
    fetch_func should accept a ticker string, fetch and persist results
    """
    for t in tickers:
        try:
            logger.info(f"Scheduled fetch for {t} at {datetime.utcnow()}")
            fetch_func(t)
        except Exception as e:
            logger.exception(f"Error fetching {t}: {e}")

def start_scheduler(fetch_func, tickers, minutes: int = 60):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: scheduled_fetch_job(fetch_func, tickers), 'interval', minutes=minutes)
    scheduler.start()
    return scheduler
