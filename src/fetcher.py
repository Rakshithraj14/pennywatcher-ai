from apscheduler.schedulers.background import BackgroundScheduler
from config import config
from groww_client import fetch_historical
from db import save_candles
import logging

logger = logging.getLogger(__name__)

def run_fetch_once():
    logger.info("Starting fetch job for tracked stocks: %s", config.TRACK_STOCKS)
    for s in config.TRACK_STOCKS:
        try:
            candles = fetch_historical(s, period="6mo", interval="1d")
            # save to db
            save_candles(s, candles)
            logger.info("Saved %d candles for %s", len(candles), s)
        except Exception as e:
            logger.exception("Error fetching %s: %s", s, e)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_fetch_once, 'interval', minutes=config.FETCH_INTERVAL_MINUTES, next_run_time=None)
    scheduler.start()
    logger.info("Scheduler started, fetching every %d minutes", config.FETCH_INTERVAL_MINUTES)
    return scheduler

