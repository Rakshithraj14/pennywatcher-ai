import numpy as np
from db import fetch_last_n

def simple_sma_signal(symbol: str, n_short=20, n_long=50):
    # get enough candles for long SMA
    rows = fetch_last_n(symbol, n_long)
    if len(rows) < n_long:
        return None

    closes = np.array([r['c'] for r in rows], dtype=float)
    sma_short = closes[-n_short:].mean()
    sma_long = closes[-n_long:].mean()

    if sma_short > sma_long:
        return {"symbol": symbol, "signal": "BUY", "reason": "sma_short > sma_long"}
    else:
        return {"symbol": symbol, "signal": "SELL", "reason": "sma_short <= sma_long"}

