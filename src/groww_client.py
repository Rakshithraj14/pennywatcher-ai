"""
Attempt to use an unofficial groww python client if available.
If not, fall back to yfinance (which may have good coverage).
Returns candles as list of dicts with keys: t (ISO str), o,h,l,c,v
"""

from datetime import datetime
import traceback

try:
    from pygrowwapi import Groww
    _HAS_GROWW = True
except Exception:
    _HAS_GROWW = False

import yfinance as yf

def _normalize_yf(df, symbol):
    candles = []
    for idx, row in df.iterrows():
        candles.append({
            "t": idx.to_pydatetime().isoformat(),
            "o": float(row["Open"]) if not (row["Open"] != row["Open"]) else None,
            "h": float(row["High"]),
            "l": float(row["Low"]),
            "c": float(row["Close"]),
            "v": int(row["Volume"]),
        })
    return candles

def fetch_historical(symbol: str, period: str = "3mo", interval: str = "1d"):
    """Return list of candles (newest last)
    period examples: '1mo','3mo','1y'
    interval examples: '1d','1h'
    """
    if _HAS_GROWW:
        try:
            client = Groww()
            # the exact method below depends on the unofficial client implementation
            raw = client.get_historical(symbol, period=period, interval=interval)
            # try to normalize expected structure
            candles = []
            for c in raw.get("candles", []):
                candles.append({
                    "t": datetime.fromtimestamp(c[0] / 1000).isoformat(),
                    "o": c[1],
                    "h": c[2],
                    "l": c[3],
                    "c": c[4],
                    "v": c[5],
                })
            return candles
        except Exception:
            traceback.print_exc()
            # fallthrough to yfinance

    # Fallback to yfinance (useful and reliable for many stocks)
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        return []
    return _normalize_yf(df, symbol)

