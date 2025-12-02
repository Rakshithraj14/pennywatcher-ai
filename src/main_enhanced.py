"""
Enhanced main entry point with all improvements
Includes: multiple strategies, signal tracking, paper trading, API server
"""

import logging
import time
import threading
from datetime import datetime

from config import config
from fetcher import start_scheduler, run_fetch_once
from enhanced_predictor import analyze_symbol
from signal_tracker import init_signal_tracking_table, track_and_check_signal
from paper_trading import init_paper_trading_tables, PaperTradingPortfolio
from notifier import send_telegram
from error_handler import retry_on_failure, log_exception_context
from api import run_api

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Strategy to use (can be configured via env)
STRATEGY = 'combined'  # Options: 'sma', 'rsi', 'macd', 'bollinger', 'combined'

# Paper trading settings
PAPER_TRADING_ENABLED = True
AUTO_TRADE_ON_SIGNALS = False  # Set to True to auto-execute paper trades on signals


@log_exception_context
def initialize_database_tables():
    """Initialize all required database tables"""
    logger.info("Initializing database tables...")
    try:
        init_signal_tracking_table()
        init_paper_trading_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
        raise


@retry_on_failure(max_retries=3, delay=2.0)
@log_exception_context
def evaluate_and_notify():
    """Evaluate stocks and send notifications on signal changes"""
    logger.info(f"Evaluating {len(config.TRACK_STOCKS)} stocks with {STRATEGY} strategy...")
    
    for symbol in config.TRACK_STOCKS:
        try:
            # Analyze symbol
            result = analyze_symbol(symbol, strategy=STRATEGY)
            
            if not result:
                logger.warning(f"No analysis result for {symbol}")
                continue
            
            # Check if we should notify
            should_alert = track_and_check_signal(symbol, result, STRATEGY)
            
            if should_alert:
                # Build notification message
                msg = format_signal_message(symbol, result)
                logger.info(f"Signal change detected for {symbol}: {result['signal']}")
                send_telegram(msg)
                
                # Execute paper trade if enabled
                if PAPER_TRADING_ENABLED and AUTO_TRADE_ON_SIGNALS:
                    execute_paper_trade(symbol, result)
            else:
                logger.debug(f"No signal change for {symbol}, skipping notification")
        
        except Exception as e:
            logger.exception(f"Error evaluating {symbol}: {e}")


def format_signal_message(symbol: str, result: dict) -> str:
    """Format a trading signal message for Telegram"""
    msg_parts = [
        f"🚨 Signal Alert: {symbol}",
        f"Signal: {result['signal']}",
        f"Strategy: {result.get('strategy_used', STRATEGY).upper()}",
        f"Reason: {result['reason']}",
        f"Confidence: {result.get('confidence', 0)*100:.0f}%",
    ]
    
    # Add indicator details
    indicators = result.get('indicators', {})
    if indicators:
        msg_parts.append(f"\n📊 Indicators:")
        msg_parts.append(f"Price: ${indicators.get('current_price', 0):.2f}")
        
        if indicators.get('rsi'):
            msg_parts.append(f"RSI: {indicators['rsi']:.2f}")
        
        if indicators.get('sma_20') and indicators.get('sma_50'):
            msg_parts.append(f"SMA: {indicators['sma_20']:.2f} / {indicators['sma_50']:.2f}")
    
    # Add details if available
    if 'details' in result:
        msg_parts.append(f"\nDetails:")
        for detail in result['details'][:3]:  # Limit to 3 details
            msg_parts.append(f"  • {detail}")
    
    return "\n".join(msg_parts)


def execute_paper_trade(symbol: str, result: dict):
    """Execute a paper trade based on signal"""
    try:
        portfolio = PaperTradingPortfolio()
        signal = result['signal']
        price = result.get('indicators', {}).get('current_price')
        
        if not price:
            logger.warning(f"No price available for {symbol}, skipping trade")
            return
        
        # Simple position sizing: $1000 per trade
        quantity = int(1000 / price)
        
        if quantity <= 0:
            return
        
        if signal in ['BUY', 'STRONG_BUY']:
            success = portfolio.execute_trade(
                symbol=symbol,
                action='BUY',
                quantity=quantity,
                price=price,
                strategy=STRATEGY,
                signal=signal
            )
            if success:
                logger.info(f"Paper trade executed: BUY {quantity} {symbol} @ ${price:.2f}")
        
        elif signal in ['SELL', 'STRONG_SELL']:
            # Check if we have position
            positions = portfolio.get_positions()
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if position:
                sell_qty = min(quantity, position['quantity'])
                success = portfolio.execute_trade(
                    symbol=symbol,
                    action='SELL',
                    quantity=sell_qty,
                    price=price,
                    strategy=STRATEGY,
                    signal=signal
                )
                if success:
                    logger.info(f"Paper trade executed: SELL {sell_qty} {symbol} @ ${price:.2f}")
    
    except Exception as e:
        logger.exception(f"Error executing paper trade for {symbol}: {e}")


def run_api_server():
    """Run the API server in a separate thread"""
    logger.info("Starting API server on http://localhost:5000")
    try:
        run_api(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.exception(f"API server error: {e}")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Stock Tracker - Enhanced Version")
    logger.info("=" * 60)
    logger.info(f"Tracking: {', '.join(config.TRACK_STOCKS)}")
    logger.info(f"Strategy: {STRATEGY}")
    logger.info(f"Fetch interval: {config.FETCH_INTERVAL_MINUTES} minutes")
    logger.info(f"Paper trading: {'Enabled' if PAPER_TRADING_ENABLED else 'Disabled'}")
    logger.info("=" * 60)
    
    # Initialize database
    initialize_database_tables()
    
    # Initial data fetch to build database
    logger.info("Running initial data fetch...")
    run_fetch_once()
    
    # Initial evaluation
    logger.info("Running initial signal evaluation...")
    evaluate_and_notify()
    
    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info("API server started in background")
    
    # Start periodic fetcher
    scheduler = start_scheduler()
    logger.info("Scheduler started for periodic data fetching")
    
    # Also schedule periodic evaluation every 30 minutes
    scheduler.add_job(evaluate_and_notify, 'interval', minutes=30)
    
    # Keep the main thread alive
    logger.info("System is running. Press Ctrl+C to stop.")
    logger.info("Dashboard available at: http://localhost:5000")
    logger.info("Open src/dashboard.html in your browser to view the dashboard")
    
    try:
        while True:
            time.sleep(60)
            # Optionally print status
            if int(datetime.now().strftime('%M')) % 10 == 0:  # Every 10 minutes
                logger.info("System running normally...")
    
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown()
        logger.info("Goodbye!")


if __name__ == '__main__':
    main()

