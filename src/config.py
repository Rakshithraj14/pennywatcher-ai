import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PG_URL = os.getenv("PG_URL")
    TRACK_STOCKS = [s.strip() for s in os.getenv("TRACK_STOCKS", "").split(",") if s.strip()]
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))

config = Config()

