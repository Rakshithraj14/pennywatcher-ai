import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Dict
from config import config

# Simple connection helper 
def get_conn():
    if not config.PG_URL:
        raise RuntimeError("PG_URL not set in env")
    return psycopg2.connect(config.PG_URL)

def save_candles(symbol: str, candles: List[Dict]):
    """candles: list of dicts with keys: t (datetime), o,h,l,c,v"""
    if not candles:
        return

    rows = []
    for c in candles:
        # ensure timestamp is a datetime
        t = c.get("t")
        if isinstance(t, str):
            t = datetime.fromisoformat(t)
        rows.append((symbol, t, c.get("o"), c.get("h"), c.get("l"), c.get("c"), c.get("v")))

    insert_sql = """
    INSERT INTO stock_prices (symbol, timestamp, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (symbol, timestamp) DO NOTHING
    """

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_sql, rows)
    finally:
        conn.close()

def fetch_last_n(symbol: str, n: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT timestamp, open, high, low, close, volume FROM stock_prices WHERE symbol=%s ORDER BY timestamp DESC LIMIT %s",
                (symbol, n),
            )
            rows = cur.fetchall()
            # return oldest -> newest
            return [
                {
                    "t": r[0].isoformat(),
                    "o": float(r[1]) if r[1] is not None else None,
                    "h": float(r[2]) if r[2] is not None else None,
                    "l": float(r[3]) if r[3] is not None else None,
                    "c": float(r[4]) if r[4] is not None else None,
                    "v": int(r[5]) if r[5] is not None else None,
                }
                for r in reversed(rows)
            ]
    finally:
        conn.close()

