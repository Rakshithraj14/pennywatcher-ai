from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime, timedelta

from db import fetch_last_n, get_conn
from enhanced_predictor import analyze_symbol
from signal_tracker import get_signal_history, init_signal_tracking_table
from paper_trading import PaperTradingPortfolio, init_paper_trading_tables
from indicators import get_all_indicators
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize database tables
try:
    init_signal_tracking_table()
    init_paper_trading_tables()
except Exception as e:
    logger.error(f"Error initializing tables: {e}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/stocks', methods=['GET'])
def get_tracked_stocks():
    """Get list of tracked stocks"""
    return jsonify({
        'stocks': config.TRACK_STOCKS,
        'count': len(config.TRACK_STOCKS)
    })


@app.route('/api/stocks/<symbol>/candles', methods=['GET'])
def get_candles(symbol):
    """Get historical candles for a symbol"""
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)  # Cap at 1000
        
        candles = fetch_last_n(symbol, limit)
        
        return jsonify({
            'symbol': symbol,
            'candles': candles,
            'count': len(candles)
        })
    except Exception as e:
        logger.exception(f"Error fetching candles for {symbol}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<symbol>/indicators', methods=['GET'])
def get_indicators(symbol):
    """Get technical indicators for a symbol"""
    try:
        n_candles = request.args.get('candles', 200, type=int)
        candles = fetch_last_n(symbol, n_candles)
        
        if not candles:
            return jsonify({'error': 'No data available'}), 404
        
        indicators = get_all_indicators(candles, symbol)
        
        return jsonify(indicators)
    except Exception as e:
        logger.exception(f"Error calculating indicators for {symbol}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<symbol>/analyze', methods=['GET'])
def analyze(symbol):
    """Analyze a symbol and get trading signal"""
    try:
        strategy = request.args.get('strategy', 'combined')
        
        result = analyze_symbol(symbol, strategy=strategy)
        
        if not result:
            return jsonify({'error': 'Unable to analyze symbol'}), 404
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error analyzing {symbol}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<symbol>/signals', methods=['GET'])
def get_signals(symbol):
    """Get signal history for a symbol"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = get_signal_history(symbol, limit)
        
        return jsonify({
            'symbol': symbol,
            'signals': history,
            'count': len(history)
        })
    except Exception as e:
        logger.exception(f"Error fetching signals for {symbol}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get paper trading portfolio"""
    try:
        user_id = request.args.get('user_id', 'default')
        portfolio = PaperTradingPortfolio(user_id)
        
        portfolio_data = portfolio.get_portfolio()
        positions = portfolio.get_positions()
        performance = portfolio.get_performance()
        
        return jsonify({
            'portfolio': portfolio_data,
            'positions': positions,
            'performance': performance
        })
    except Exception as e:
        logger.exception("Error fetching portfolio")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/positions', methods=['GET'])
def get_positions():
    """Get open positions"""
    try:
        user_id = request.args.get('user_id', 'default')
        portfolio = PaperTradingPortfolio(user_id)
        positions = portfolio.get_positions()
        
        return jsonify({'positions': positions, 'count': len(positions)})
    except Exception as e:
        logger.exception("Error fetching positions")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/trades', methods=['GET', 'POST'])
def trades():
    """Get trade history or execute a new trade"""
    try:
        user_id = request.args.get('user_id', 'default')
        portfolio = PaperTradingPortfolio(user_id)
        
        if request.method == 'GET':
            limit = request.args.get('limit', 50, type=int)
            history = portfolio.get_trade_history(limit)
            return jsonify({'trades': history, 'count': len(history)})
        
        else:  # POST
            data = request.json
            
            required = ['symbol', 'action', 'quantity', 'price']
            if not all(k in data for k in required):
                return jsonify({'error': 'Missing required fields'}), 400
            
            success = portfolio.execute_trade(
                symbol=data['symbol'],
                action=data['action'],
                quantity=int(data['quantity']),
                price=float(data['price']),
                strategy=data.get('strategy'),
                signal=data.get('signal')
            )
            
            if success:
                return jsonify({'success': True, 'message': 'Trade executed'})
            else:
                return jsonify({'success': False, 'error': 'Trade failed'}), 400
    
    except Exception as e:
        logger.exception("Error in trades endpoint")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/performance', methods=['GET'])
def get_performance():
    """Get portfolio performance metrics"""
    try:
        user_id = request.args.get('user_id', 'default')
        portfolio = PaperTradingPortfolio(user_id)
        performance = portfolio.get_performance()
        
        return jsonify(performance)
    except Exception as e:
        logger.exception("Error fetching performance")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        conn = get_conn()
        stats = {}
        
        with conn.cursor() as cur:
            # Total candles
            cur.execute("SELECT COUNT(*) FROM stock_prices")
            stats['total_candles'] = cur.fetchone()[0]
            
            # Unique symbols
            cur.execute("SELECT COUNT(DISTINCT symbol) FROM stock_prices")
            stats['unique_symbols'] = cur.fetchone()[0]
            
            # Latest data timestamp
            cur.execute("SELECT MAX(timestamp) FROM stock_prices")
            latest = cur.fetchone()[0]
            stats['latest_data'] = latest.isoformat() if latest else None
            
            # Total signals
            cur.execute("SELECT COUNT(*) FROM signal_history")
            stats['total_signals'] = cur.fetchone()[0]
            
            # Total trades
            cur.execute("SELECT COUNT(*) FROM paper_trades")
            stats['total_trades'] = cur.fetchone()[0]
        
        conn.close()
        return jsonify(stats)
    except Exception as e:
        logger.exception("Error fetching stats")
        return jsonify({'error': str(e)}), 500


def run_api(host='0.0.0.0', port=5000, debug=False):
    """Run the API server"""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_api(debug=True)

