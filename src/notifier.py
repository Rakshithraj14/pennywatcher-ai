from config import config
from telegram import Bot
import logging

logger = logging.getLogger(__name__)

bot = None
if config.TELEGRAM_BOT_TOKEN:
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

def send_telegram(message: str):
    if not bot or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram bot or chat id not configured.\nMessage: %s", message)
        return

    try:
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logger.exception("Failed to send telegram message: %s", e)

