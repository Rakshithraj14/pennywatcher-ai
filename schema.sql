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

