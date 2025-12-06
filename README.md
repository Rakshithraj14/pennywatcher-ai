# Python Stock Tracker — Enhanced Edition 🚀

A production-ready algorithmic trading system with:

* **Multiple Technical Indicators**: RSI, MACD, Bollinger Bands, SMA, EMA
* **Advanced Strategy Engine**: Combined multi-indicator analysis with confidence scoring
* **Paper Trading System**: Virtual portfolio to test strategies without risking real money
* **Real-time Dashboard**: Web interface with interactive charts and live data
* **Signal State Tracking**: Smart notifications that only alert on meaningful changes
* **REST API**: Full-featured API for programmatic access
* **Comprehensive Error Handling**: Retries, validation, and robust error recovery
* **PostgreSQL Storage**: Efficient storage with proper indexing
* **Telegram Alerts**: Real-time notifications when signals occur
* **Multi-user Support**: Database schema ready for multiple users

---

## 📁 Project Structure

```
pennywatcher-ai/
├── README.md
├── requirements.txt
├── schema.sql
├── .env.example
├── src/
│   ├── config.py              # Configuration management
│   ├── db.py                  # Database operations
│   ├── groww_client.py        # Data fetching (Groww/yfinance)
│   ├── fetcher.py             # Scheduled data fetching
│   ├── indicators.py          # Technical indicators (RSI, MACD, BB, etc.)
│   ├── predictor.py           # Basic SMA strategy
│   ├── enhanced_predictor.py  # Advanced multi-strategy analysis
│   ├── signal_tracker.py      # Signal state tracking (prevents spam)
│   ├── paper_trading.py       # Paper trading portfolio management
│   ├── error_handler.py       # Error handling utilities
│   ├── notifier.py            # Telegram notifications
│   ├── api.py                 # REST API endpoints
│   ├── dashboard.html         # Web dashboard
│   ├── main.py                # Basic entry point
│   └── main_enhanced.py       # Enhanced entry point (recommended)
└── tests/
    ├── __init__.py
    ├── test_indicators.py     # Indicator tests
    └── test_paper_trading.py  # Paper trading tests
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL

```bash
# Create database
createdb stockdb

# Run schema
psql stockdb < schema.sql
```

### 3. Configure Environment

Create `.env` file:

```bash
PG_URL=postgresql://user:password@localhost:5432/stockdb
TRACK_STOCKS=AAPL,GOOGL,MSFT
TELEGRAM_BOT_TOKEN=your_bot_token_from_BotFather
TELEGRAM_CHAT_ID=your_chat_id
FETCH_INTERVAL_MINUTES=30
```

**Getting Telegram Bot Token:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token
4. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

### 4. Run the System

**Enhanced version (recommended):**
```bash
python src/main_enhanced.py
```

**Basic version:**
```bash
python src/main.py
```

### 5. Open Dashboard

Open `src/dashboard.html` in your browser or navigate to `http://localhost:5000`

The API will be running at `http://localhost:5000/api`

---

## 🎯 Features in Detail

### 1. Enhanced Technical Indicators

The system calculates multiple technical indicators:

- **SMA** (Simple Moving Average): 20, 50, 200 periods
- **EMA** (Exponential Moving Average): 12, 26 periods
- **RSI** (Relative Strength Index): 14 period
- **MACD** (Moving Average Convergence Divergence): 12/26/9
- **Bollinger Bands**: 20 period, 2 std dev
- **Volatility**: Annualized historical volatility
- **ATR** (Average True Range): 14 period

### 2. Multiple Trading Strategies

Choose from 5 built-in strategies:

1. **Combined Strategy** (Recommended): Weights multiple indicators with confidence scoring
2. **SMA Crossover**: Classic 20/50 SMA crossover
3. **RSI Strategy**: Oversold/overbought detection
4. **MACD Strategy**: MACD histogram crossover
5. **Bollinger Bands**: Mean reversion strategy

Each strategy returns:
- Signal: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
- Confidence score: 0-1 (higher = more confident)
- Detailed reasoning

### 3. Signal State Tracking

Prevents notification spam by only alerting when signals **change**:

- Tracks signal history in database
- Only notifies on meaningful transitions (BUY → SELL, etc.)
- Stores all signals for analysis
- Configurable notification rules

### 4. Paper Trading System

Full virtual portfolio management:

- **Initial Cash**: $100,000 (configurable)
- **Track Positions**: Buy/sell stocks virtually
- **P&L Tracking**: Unrealized gains/losses
- **Trade History**: Complete audit trail
- **Performance Metrics**: Returns, win rate, etc.
- **Commission Simulation**: 0.1% per trade

### 5. REST API

Full-featured API for programmatic access:

```
GET  /api/health                           # Health check
GET  /api/stocks                           # List tracked stocks
GET  /api/stocks/<symbol>/candles          # Historical candles
GET  /api/stocks/<symbol>/indicators       # Technical indicators
GET  /api/stocks/<symbol>/analyze          # Analyze & get signal
GET  /api/stocks/<symbol>/signals          # Signal history
GET  /api/portfolio                        # Portfolio status
GET  /api/portfolio/positions              # Open positions
GET  /api/portfolio/trades                 # Trade history
POST /api/portfolio/trades                 # Execute trade
GET  /api/portfolio/performance            # Performance metrics
GET  /api/stats                            # Overall statistics
```

### 6. Web Dashboard

Interactive dashboard featuring:

- **Real-time Price Charts**: Candlestick charts with indicators
- **Portfolio Overview**: Cash, positions, P&L
- **Signal Analysis**: Run strategies on demand
- **Position Tracking**: View all open positions
- **Performance Metrics**: Returns, win rate, Sharpe ratio
- **Auto-refresh**: Updates every 60 seconds

### 7. Error Handling & Validation

Robust error handling throughout:

- **Retry Logic**: Automatic retries with exponential backoff
- **Data Validation**: Validates OHLCV data for sanity
- **API Error Handling**: Graceful handling of rate limits, timeouts
- **Logging**: Comprehensive logging for debugging
- **Exception Context**: Detailed error messages with context

---

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_indicators.py

# Run with coverage
pytest --cov=src tests/
```

---

## ⚙️ Configuration Options

### Strategy Selection

In `src/main_enhanced.py`, change:

```python
STRATEGY = 'combined'  # Options: 'sma', 'rsi', 'macd', 'bollinger', 'combined'
```

### Paper Trading Auto-Execution

```python
PAPER_TRADING_ENABLED = True
AUTO_TRADE_ON_SIGNALS = False  # Set True to auto-trade on signals
```

### Fetch Interval

In `.env`:
```
FETCH_INTERVAL_MINUTES=30  # Fetch data every 30 minutes
```

---

## 📈 Strategy Performance Tips

### Backtesting (Recommended)

Before live/paper trading:

1. Fetch 6-12 months of historical data
2. Run strategy on historical data
3. Calculate metrics (Sharpe ratio, max drawdown, win rate)
4. Compare against buy-and-hold
5. Optimize parameters

### Risk Management

Implement these before real money:

1. **Position Sizing**: Never risk more than 2% per trade
2. **Stop Losses**: Set automatic stop losses (e.g., 5%)
3. **Take Profits**: Lock in gains at predetermined levels
4. **Diversification**: Don't put all eggs in one basket
5. **Max Drawdown Limit**: Stop trading if portfolio drops X%

### Improving Strategies

Ways to improve the combined strategy:

- Add volume confirmation (high volume = stronger signal)
- Filter by market trend (only buy in uptrends)
- Add support/resistance levels
- Incorporate fundamental data (P/E, earnings)
- Use machine learning (XGBoost, LSTM)

---

## 🚀 Production Deployment

For production use:

1. **Use Connection Pooling**: Replace `get_conn()` with connection pool
2. **Add Authentication**: Protect API with JWT/OAuth
3. **Use HTTPS**: Set up SSL certificates
4. **Environment Secrets**: Use secret manager (AWS Secrets, HashiCorp Vault)
5. **Rate Limiting**: Add rate limiting to API endpoints
6. **Monitoring**: Set up Prometheus + Grafana
7. **Alerting**: Configure PagerDuty/Sentry for errors
8. **Backup Database**: Automated PostgreSQL backups
9. **Load Balancing**: Use nginx or similar for high availability
10. **Docker**: Containerize for easy deployment

### Docker Setup (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main_enhanced.py"]
```

---

## 📚 Further Reading

- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [Quantitative Trading by Ernest Chan](https://www.amazon.com/Quantitative-Trading-Build-Algorithmic-Business/dp/1119800064)
- [Python for Finance by Yves Hilpisch](https://www.oreilly.com/library/view/python-for-finance/9781492024323/)
- [Backtesting.py Documentation](https://kernc.github.io/backtesting.py/)

---

## ⚠️ Disclaimer

This is a **learning/educational project**. 

**DO NOT use for real trading without:**
- ✅ Extensive backtesting (6+ months)
- ✅ Paper trading validation (3+ months)
- ✅ Understanding of all strategies
- ✅ Proper risk management
- ✅ Financial advisor consultation

**The strategies provided are for demonstration purposes and will likely underperform in real markets.**

**Past performance does not guarantee future results.**

---

## 📝 License

MIT License - feel free to use and modify for your needs.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure tests pass
5. Submit a pull request

---

## 💬 Support

For issues or questions:
- Open a GitHub issue
- Check the troubleshooting section above
- Review the code documentation

---

**Happy Trading! 📈**

---

Built with ⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖
