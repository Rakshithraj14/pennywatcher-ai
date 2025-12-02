import logging
from fetcher import start_scheduler, run_fetch_once
from predictor import simple_sma_signal
from notifier import send_telegram
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_and_notify():
    for s in config.TRACK_STOCKS:
        try:
            sig = simple_sma_signal(s)
            if sig is None:
                continue

            # build message
            msg = f"Signal for {s}: {sig['signal']} — {sig['reason']}"
            logger.info(msg)
            send_telegram(msg)
        except Exception as e:
            logger.exception("Error evaluating %s: %s", s, e)

if __name__ == '__main__':
    # initial fetch to build database
    run_fetch_once()

    # evaluate once at startup
    evaluate_and_notify()

    # start periodic fetcher
    scheduler = start_scheduler()

    # also schedule periodic evaluation (you might hook evaluation to fetch job)
    # keep the main thread alive
    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

