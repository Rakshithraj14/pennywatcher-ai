import logging
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from config import config

logger = logging.getLogger(__name__)


def get_conn():
    """Get database connection"""
    if not config.PG_URL:
        raise RuntimeError("PG_URL not set in env")
    return psycopg2.connect(config.PG_URL)


def init_paper_trading_tables():
    """Create paper trading tables"""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Portfolio table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_portfolio (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'default',
                        cash NUMERIC NOT NULL DEFAULT 100000,
                        total_value NUMERIC NOT NULL DEFAULT 100000,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        UNIQUE(user_id)
                    );
                    
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
                    
                    CREATE INDEX IF NOT EXISTS idx_trades_user_ts 
                    ON paper_trades(user_id, timestamp DESC);
                """)
                
                # Initialize default portfolio if not exists
                cur.execute("""
                    INSERT INTO paper_portfolio (user_id, cash, total_value)
                    VALUES ('default', 100000, 100000)
                    ON CONFLICT (user_id) DO NOTHING
                """)
    finally:
        conn.close()


class PaperTradingPortfolio:
    """Paper trading portfolio manager"""
    
    def __init__(self, user_id: str = 'default', initial_cash: float = 100000):
        self.user_id = user_id
        self.initial_cash = initial_cash
        self._ensure_portfolio_exists()
    
    def _ensure_portfolio_exists(self):
        """Ensure portfolio exists in database"""
        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO paper_portfolio (user_id, cash, total_value)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, (self.user_id, self.initial_cash, self.initial_cash))
        finally:
            conn.close()
    
    def get_portfolio(self) -> Dict:
        """Get current portfolio status"""
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT cash, total_value, created_at, updated_at
                    FROM paper_portfolio
                    WHERE user_id = %s
                """, (self.user_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return {
                    'user_id': self.user_id,
                    'cash': float(row[0]),
                    'total_value': float(row[1]),
                    'created_at': row[2],
                    'updated_at': row[3]
                }
        finally:
            conn.close()
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, quantity, avg_price, current_price, 
                           unrealized_pnl, opened_at, updated_at
                    FROM paper_positions
                    WHERE user_id = %s AND quantity > 0
                    ORDER BY symbol
                """, (self.user_id,))
                
                rows = cur.fetchall()
                return [
                    {
                        'symbol': r[0],
                        'quantity': r[1],
                        'avg_price': float(r[2]),
                        'current_price': float(r[3]) if r[3] else None,
                        'unrealized_pnl': float(r[4]) if r[4] else 0,
                        'total_value': r[1] * float(r[3]) if r[3] else 0,
                        'opened_at': r[5],
                        'updated_at': r[6]
                    }
                    for r in rows
                ]
        finally:
            conn.close()
    
    def execute_trade(self, symbol: str, action: str, quantity: int, price: float,
                     strategy: str = None, signal: str = None) -> bool:
        """
        Execute a paper trade
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Price per share
            strategy: Strategy name
            signal: Signal that triggered trade
        
        Returns:
            True if successful, False otherwise
        """
        if action not in ['BUY', 'SELL']:
            logger.error(f"Invalid action: {action}")
            return False
        
        if quantity <= 0 or price <= 0:
            logger.error(f"Invalid quantity or price: {quantity}, {price}")
            return False
        
        total_value = quantity * price
        commission = total_value * 0.001  # 0.1% commission
        
        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    portfolio = self.get_portfolio()
                    
                    if action == 'BUY':
                        # Check if enough cash
                        required = total_value + commission
                        if portfolio['cash'] < required:
                            logger.warning(
                                f"Insufficient cash for {symbol}: "
                                f"need ${required:.2f}, have ${portfolio['cash']:.2f}"
                            )
                            return False
                        
                        # Update or insert position
                        cur.execute("""
                            SELECT quantity, avg_price
                            FROM paper_positions
                            WHERE user_id = %s AND symbol = %s
                        """, (self.user_id, symbol))
                        
                        row = cur.fetchone()
                        
                        if row:
                            old_qty, old_avg = row
                            new_qty = old_qty + quantity
                            new_avg = ((old_qty * float(old_avg)) + total_value) / new_qty
                            
                            cur.execute("""
                                UPDATE paper_positions
                                SET quantity = %s, avg_price = %s, updated_at = NOW()
                                WHERE user_id = %s AND symbol = %s
                            """, (new_qty, new_avg, self.user_id, symbol))
                        else:
                            cur.execute("""
                                INSERT INTO paper_positions 
                                (user_id, symbol, quantity, avg_price, current_price)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (self.user_id, symbol, quantity, price, price))
                        
                        # Update portfolio cash
                        new_cash = portfolio['cash'] - required
                        cur.execute("""
                            UPDATE paper_portfolio
                            SET cash = %s, updated_at = NOW()
                            WHERE user_id = %s
                        """, (new_cash, self.user_id))
                    
                    else:  # SELL
                        # Check if have enough shares
                        cur.execute("""
                            SELECT quantity, avg_price
                            FROM paper_positions
                            WHERE user_id = %s AND symbol = %s
                        """, (self.user_id, symbol))
                        
                        row = cur.fetchone()
                        
                        if not row or row[0] < quantity:
                            logger.warning(
                                f"Insufficient shares for {symbol}: "
                                f"need {quantity}, have {row[0] if row else 0}"
                            )
                            return False
                        
                        old_qty = row[0]
                        new_qty = old_qty - quantity
                        
                        if new_qty == 0:
                            cur.execute("""
                                DELETE FROM paper_positions
                                WHERE user_id = %s AND symbol = %s
                            """, (self.user_id, symbol))
                        else:
                            cur.execute("""
                                UPDATE paper_positions
                                SET quantity = %s, updated_at = NOW()
                                WHERE user_id = %s AND symbol = %s
                            """, (new_qty, self.user_id, symbol))
                        
                        # Update portfolio cash
                        proceeds = total_value - commission
                        new_cash = portfolio['cash'] + proceeds
                        cur.execute("""
                            UPDATE paper_portfolio
                            SET cash = %s, updated_at = NOW()
                            WHERE user_id = %s
                        """, (new_cash, self.user_id))
                    
                    # Record trade
                    cur.execute("""
                        INSERT INTO paper_trades
                        (user_id, symbol, action, quantity, price, total_value, 
                         commission, strategy, signal)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (self.user_id, symbol, action, quantity, price, total_value,
                          commission, strategy, signal))
                    
                    logger.info(
                        f"Paper trade executed: {action} {quantity} {symbol} @ ${price:.2f}"
                    )
                    return True
        except Exception as e:
            logger.exception(f"Error executing trade: {e}")
            return False
        finally:
            conn.close()
    
    def update_positions(self, prices: Dict[str, float]):
        """Update current prices and unrealized P&L for all positions"""
        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    for symbol, price in prices.items():
                        cur.execute("""
                            UPDATE paper_positions
                            SET current_price = %s,
                                unrealized_pnl = (current_price - avg_price) * quantity,
                                updated_at = NOW()
                            WHERE user_id = %s AND symbol = %s
                        """, (price, self.user_id, symbol))
        finally:
            conn.close()
    
    def get_performance(self) -> Dict:
        """Get portfolio performance metrics"""
        portfolio = self.get_portfolio()
        positions = self.get_positions()
        
        if not portfolio:
            return None
        
        positions_value = sum(p['total_value'] for p in positions)
        total_value = portfolio['cash'] + positions_value
        
        pnl = total_value - self.initial_cash
        pnl_pct = (pnl / self.initial_cash) * 100
        
        return {
            'initial_cash': self.initial_cash,
            'current_cash': portfolio['cash'],
            'positions_value': positions_value,
            'total_value': total_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'num_positions': len(positions)
        }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, action, quantity, price, total_value, 
                           commission, strategy, signal, timestamp
                    FROM paper_trades
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (self.user_id, limit))
                
                rows = cur.fetchall()
                return [
                    {
                        'symbol': r[0],
                        'action': r[1],
                        'quantity': r[2],
                        'price': float(r[3]),
                        'total_value': float(r[4]),
                        'commission': float(r[5]),
                        'strategy': r[6],
                        'signal': r[7],
                        'timestamp': r[8].isoformat()
                    }
                    for r in rows
                ]
        finally:
            conn.close()

