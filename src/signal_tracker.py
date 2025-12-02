import logging
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from config import config

logger = logging.getLogger(__name__)


def get_conn():
    """Get database connection"""
    if not config.PG_URL:
        raise RuntimeError("PG_URL not set in env")
    return psycopg2.connect(config.PG_URL)


def init_signal_tracking_table():
    """Create signal_history table if it doesn't exist"""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
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
                    
                    CREATE INDEX IF NOT EXISTS idx_signal_symbol_ts 
                    ON signal_history(symbol, timestamp DESC);
                """)
    finally:
        conn.close()


def get_last_signal(symbol: str, strategy: str = 'combined') -> Optional[Dict]:
    """Get the last recorded signal for a symbol"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT signal, strategy, reason, confidence, score, timestamp, notified
                FROM signal_history
                WHERE symbol = %s AND strategy = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol, strategy))
            
            row = cur.fetchone()
            if row:
                return {
                    'signal': row[0],
                    'strategy': row[1],
                    'reason': row[2],
                    'confidence': float(row[3]) if row[3] else None,
                    'score': float(row[4]) if row[4] else None,
                    'timestamp': row[5],
                    'notified': row[6]
                }
            return None
    finally:
        conn.close()


def save_signal(symbol: str, signal: str, strategy: str, reason: str, 
                confidence: float = None, score: float = None, notified: bool = False):
    """Save a new signal to history"""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO signal_history 
                    (symbol, signal, strategy, reason, confidence, score, timestamp, notified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (symbol, signal, strategy, reason, confidence, score, datetime.now(), notified))
    finally:
        conn.close()


def should_notify(symbol: str, new_signal: Dict, strategy: str = 'combined') -> bool:
    """
    Determine if we should send a notification for this signal
    
    Rules:
    - Always notify on first signal
    - Notify if signal changed (BUY -> SELL or SELL -> BUY)
    - Don't notify if signal is the same as last time
    - Notify on STRONG signals even if direction same
    """
    last_signal = get_last_signal(symbol, strategy)
    
    # First signal - always notify
    if not last_signal:
        return True
    
    current = new_signal['signal']
    previous = last_signal['signal']
    
    # Mapping for comparison
    buy_signals = ['BUY', 'STRONG_BUY']
    sell_signals = ['SELL', 'STRONG_SELL']
    
    # Signal direction changed - always notify
    if (current in buy_signals and previous in sell_signals) or \
       (current in sell_signals and previous in buy_signals):
        return True
    
    # Strong signal and previous was regular - notify
    if current == 'STRONG_BUY' and previous == 'BUY':
        return True
    if current == 'STRONG_SELL' and previous == 'SELL':
        return True
    
    # Changed from HOLD to action - notify
    if previous == 'HOLD' and current in (buy_signals + sell_signals):
        return True
    
    # Otherwise, don't spam
    return False


def track_and_check_signal(symbol: str, signal_result: Dict, strategy: str = 'combined') -> bool:
    """
    Track signal and determine if notification should be sent
    
    Args:
        symbol: Stock symbol
        signal_result: Result from analyzer
        strategy: Strategy name
    
    Returns:
        True if notification should be sent, False otherwise
    """
    if not signal_result:
        return False
    
    should_alert = should_notify(symbol, signal_result, strategy)
    
    # Save signal to history
    save_signal(
        symbol=symbol,
        signal=signal_result['signal'],
        strategy=strategy,
        reason=signal_result.get('reason', ''),
        confidence=signal_result.get('confidence'),
        score=signal_result.get('score'),
        notified=should_alert
    )
    
    return should_alert


def get_signal_history(symbol: str, limit: int = 10) -> list:
    """Get signal history for a symbol"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT signal, strategy, reason, confidence, timestamp, notified
                FROM signal_history
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, limit))
            
            rows = cur.fetchall()
            return [
                {
                    'signal': r[0],
                    'strategy': r[1],
                    'reason': r[2],
                    'confidence': float(r[3]) if r[3] else None,
                    'timestamp': r[4].isoformat(),
                    'notified': r[5]
                }
                for r in rows
            ]
    finally:
        conn.close()

