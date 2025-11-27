# Python Stock Tracker — Groww + PostgreSQL + Telegram Alerts

This repository is a complete starter project to:

* Fetch historical and live stock data (via unofficial Groww client if available, with fallback to yfinance)
* Store OHLCV candles in PostgreSQL
* Run scheduled fetch jobs to build history
* Run a simple SMA crossover predictor
* Send real-time alerts to a Telegram chat when signals occur

---

## Project structure

```
python-stock-tracker/
├── README.md
├── requirements.txt
├── schema.sql
├── .env.example
├── src/
│   ├── config.py
│   ├── db.py
│   ├── groww_client.py
│   ├── fetcher.py
│   ├── predictor.py
│   ├── notifier.py
│   └── main.py
```

---

## How to run

1. Create a virtualenv and install requirements:

```bash
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

2. Create your PostgreSQL DB and run `schema.sql`.

3. Copy `.env.example` to `.env` and fill values:
   - `PG_URL`: PostgreSQL connection string
   - `TRACK_STOCKS`: Comma-separated stock symbols (e.g., SUZLON.NS,IDEA.NS,PNB.NS)
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (BotFather)
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
   - `FETCH_INTERVAL_MINUTES`: How often to fetch data (default: 30)

4. Run `python src/main.py`.

---

## Environment Variables

Create a `.env` file with the following variables:

```
PG_URL=postgresql://user:password@localhost:5432/stockdb
TRACK_STOCKS=SUZLON.NS,IDEA.NS,PNB.NS
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
FETCH_INTERVAL_MINUTES=30
```

---

## Features

- **Multiple Data Sources**: Attempts to use unofficial Groww API, falls back to yfinance
- **PostgreSQL Storage**: Efficient storage with proper indexing and duplicate prevention
- **Scheduled Fetching**: Automatic data updates using APScheduler
- **SMA Strategy**: Simple 20/50 SMA crossover predictor
- **Telegram Alerts**: Real-time notifications when signals occur

---

## Next steps & improvements

* Use a proper DB connection pool (psycopg2 pool or asyncpg) for production
* Add error handling & retries for network calls
* Use websocket / streaming APIs if you need tick-level real-time data
* Build a React dashboard to visualize candles and signals
* Replace SMA with ML models (XGBoost, LSTM) and add backtesting
* Add paper-trading mode before using real money
* Implement proper risk management (stop losses, position sizing)
* Add signal state tracking to avoid notification spam

---

## Disclaimer

This is a **learning/educational project**. Do NOT use it for real trading without:
- Extensive backtesting
- Proper risk management
- Understanding of the strategy
- Paper trading for several months

The simple SMA strategy included is for demonstration purposes and will likely underperform in real markets.

---

