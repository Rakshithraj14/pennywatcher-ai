import logging
from typing import Dict, Optional, List
from db import fetch_last_n
from indicators import get_all_indicators

logger = logging.getLogger(__name__)


class Signal:
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


def sma_crossover_strategy(indicators: Dict) -> Optional[Dict]:
    """Simple 20/50 SMA crossover strategy"""
    if not indicators or not indicators.get('sma_20') or not indicators.get('sma_50'):
        return None
    
    sma_20 = indicators['sma_20']
    sma_50 = indicators['sma_50']
    
    if sma_20 > sma_50:
        signal = Signal.BUY
        reason = f"SMA20({sma_20:.2f}) > SMA50({sma_50:.2f})"
    else:
        signal = Signal.SELL
        reason = f"SMA20({sma_20:.2f}) <= SMA50({sma_50:.2f})"
    
    return {
        'signal': signal,
        'reason': reason,
        'confidence': 0.6  # Medium confidence
    }


def rsi_strategy(indicators: Dict) -> Optional[Dict]:
    """RSI-based strategy (oversold/overbought)"""
    rsi = indicators.get('rsi')
    if rsi is None:
        return None
    
    if rsi < 30:
        signal = Signal.STRONG_BUY
        reason = f"RSI oversold ({rsi:.2f})"
        confidence = 0.8
    elif rsi > 70:
        signal = Signal.STRONG_SELL
        reason = f"RSI overbought ({rsi:.2f})"
        confidence = 0.8
    elif rsi < 40:
        signal = Signal.BUY
        reason = f"RSI low ({rsi:.2f})"
        confidence = 0.6
    elif rsi > 60:
        signal = Signal.SELL
        reason = f"RSI high ({rsi:.2f})"
        confidence = 0.6
    else:
        signal = Signal.HOLD
        reason = f"RSI neutral ({rsi:.2f})"
        confidence = 0.5
    
    return {
        'signal': signal,
        'reason': reason,
        'confidence': confidence
    }


def macd_strategy(indicators: Dict) -> Optional[Dict]:
    """MACD crossover strategy"""
    macd = indicators.get('macd')
    if not macd:
        return None
    
    macd_line = macd['macd']
    signal_line = macd['signal']
    histogram = macd['histogram']
    
    if histogram > 0 and macd_line > signal_line:
        signal = Signal.BUY
        reason = f"MACD bullish crossover (hist: {histogram:.2f})"
        confidence = 0.75
    elif histogram < 0 and macd_line < signal_line:
        signal = Signal.SELL
        reason = f"MACD bearish crossover (hist: {histogram:.2f})"
        confidence = 0.75
    else:
        signal = Signal.HOLD
        reason = "MACD neutral"
        confidence = 0.5
    
    return {
        'signal': signal,
        'reason': reason,
        'confidence': confidence
    }


def bollinger_strategy(indicators: Dict) -> Optional[Dict]:
    """Bollinger Bands mean reversion strategy"""
    bb = indicators.get('bollinger')
    if not bb:
        return None
    
    current = bb['current']
    upper = bb['upper']
    lower = bb['lower']
    middle = bb['middle']
    
    # Calculate position within bands
    band_width = upper - lower
    if band_width == 0:
        return None
    
    position = (current - lower) / band_width  # 0 to 1
    
    if current <= lower:
        signal = Signal.STRONG_BUY
        reason = f"Price at lower BB ({current:.2f} <= {lower:.2f})"
        confidence = 0.85
    elif current >= upper:
        signal = Signal.STRONG_SELL
        reason = f"Price at upper BB ({current:.2f} >= {upper:.2f})"
        confidence = 0.85
    elif position < 0.3:
        signal = Signal.BUY
        reason = f"Price near lower BB (pos: {position:.2f})"
        confidence = 0.65
    elif position > 0.7:
        signal = Signal.SELL
        reason = f"Price near upper BB (pos: {position:.2f})"
        confidence = 0.65
    else:
        signal = Signal.HOLD
        reason = "Price in middle BB range"
        confidence = 0.5
    
    return {
        'signal': signal,
        'reason': reason,
        'confidence': confidence
    }


def combined_strategy(indicators: Dict) -> Optional[Dict]:
    """
    Combined strategy using multiple indicators
    Weights different signals and produces a consensus
    """
    strategies = {
        'sma': sma_crossover_strategy(indicators),
        'rsi': rsi_strategy(indicators),
        'macd': macd_strategy(indicators),
        'bollinger': bollinger_strategy(indicators)
    }
    
    # Filter out None values
    valid_strategies = {k: v for k, v in strategies.items() if v is not None}
    
    if not valid_strategies:
        return None
    
    # Calculate weighted score
    signal_scores = {
        Signal.STRONG_BUY: 2,
        Signal.BUY: 1,
        Signal.HOLD: 0,
        Signal.SELL: -1,
        Signal.STRONG_SELL: -2
    }
    
    total_score = 0
    total_weight = 0
    reasons = []
    
    for strategy_name, result in valid_strategies.items():
        signal = result['signal']
        confidence = result['confidence']
        score = signal_scores.get(signal, 0)
        
        total_score += score * confidence
        total_weight += confidence
        reasons.append(f"{strategy_name}: {signal} ({result['reason']})")
    
    if total_weight == 0:
        return None
    
    avg_score = total_score / total_weight
    
    # Determine final signal based on average score
    if avg_score >= 1.5:
        final_signal = Signal.STRONG_BUY
    elif avg_score >= 0.5:
        final_signal = Signal.BUY
    elif avg_score <= -1.5:
        final_signal = Signal.STRONG_SELL
    elif avg_score <= -0.5:
        final_signal = Signal.SELL
    else:
        final_signal = Signal.HOLD
    
    return {
        'signal': final_signal,
        'reason': f"Combined score: {avg_score:.2f}",
        'confidence': min(total_weight / len(valid_strategies), 1.0),
        'details': reasons,
        'score': avg_score
    }


def analyze_symbol(symbol: str, strategy: str = 'combined', n_candles: int = 200) -> Optional[Dict]:
    """
    Analyze a symbol and generate trading signal
    
    Args:
        symbol: Stock symbol to analyze
        strategy: 'sma', 'rsi', 'macd', 'bollinger', or 'combined'
        n_candles: Number of historical candles to fetch
    
    Returns:
        Dict with signal, reason, confidence, and indicators
    """
    try:
        candles = fetch_last_n(symbol, n_candles)
        
        if not candles or len(candles) < 50:
            logger.warning(f"Insufficient data for {symbol}: {len(candles) if candles else 0} candles")
            return None
        
        indicators = get_all_indicators(candles, symbol)
        
        if not indicators:
            logger.warning(f"Could not calculate indicators for {symbol}")
            return None
        
        # Select strategy
        strategy_map = {
            'sma': sma_crossover_strategy,
            'rsi': rsi_strategy,
            'macd': macd_strategy,
            'bollinger': bollinger_strategy,
            'combined': combined_strategy
        }
        
        strategy_func = strategy_map.get(strategy, combined_strategy)
        result = strategy_func(indicators)
        
        if result:
            result['symbol'] = symbol
            result['indicators'] = indicators
            result['strategy_used'] = strategy
        
        return result
        
    except Exception as e:
        logger.exception(f"Error analyzing {symbol}: {e}")
        return None

