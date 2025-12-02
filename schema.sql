-- Stock prices table (OHLCV candles)
CREATE TABLE IF NOT EXISTS stock_prices (
  id SERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  close NUMERIC,
  volume BIGINT,
  UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_symbol_ts ON stock_prices(symbol, timestamp DESC);

-- Signal history table (track all generated signals)
CREATE TABLE IF NOT EXISTS signal_history (
  id SERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,
  signal TEXT NOT NULL,
  strategy TEXT NOT NULL,
  reason TEXT,
  confidence NUMERIC,
  score NUMERIC,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  notified BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_signal_symbol_ts ON signal_history(symbol, timestamp DESC);

-- Paper trading portfolio
CREATE TABLE IF NOT EXISTS paper_portfolio (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'default',
  cash NUMERIC NOT NULL DEFAULT 100000,
  total_value NUMERIC NOT NULL DEFAULT 100000,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Paper trading positions
CREATE TABLE IF NOT EXISTS paper_positions (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'default',
  symbol TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  avg_price NUMERIC NOT NULL,
  current_price NUMERIC,
  unrealized_pnl NUMERIC DEFAULT 0,
  opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, symbol)
);

-- Paper trading trade history
CREATE TABLE IF NOT EXISTS paper_trades (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'default',
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  price NUMERIC NOT NULL,
  total_value NUMERIC NOT NULL,
  commission NUMERIC DEFAULT 0,
  strategy TEXT,
  signal TEXT,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_user_ts ON paper_trades(user_id, timestamp DESC);

-- Users table (for multi-user support)
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  telegram_chat_id TEXT,
  tracked_stocks TEXT[],
  strategy_preference TEXT DEFAULT 'combined',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Initialize default user and portfolio
INSERT INTO users (user_id, telegram_chat_id, tracked_stocks, strategy_preference)
VALUES ('default', NULL, '{}', 'combined')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO paper_portfolio (user_id, cash, total_value)
VALUES ('default', 100000, 100000)
ON CONFLICT (user_id) DO NOTHING;

