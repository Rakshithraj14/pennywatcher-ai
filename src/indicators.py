import numpy as np
import pandas as pd
from typing import Dict, List, Optional


def calculate_sma(prices: np.ndarray, period: int) -> float:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return prices[-period:].mean()


def calculate_ema(prices: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    df = pd.DataFrame({'price': prices})
    ema = df['price'].ewm(span=period, adjust=False).mean()
    return ema.iloc[-1]


def calculate_rsi(prices: np.ndarray, period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = gains[-period:].mean()
    avg_loss = losses[-period:].mean()
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
    """Calculate MACD, signal line, and histogram"""
    if len(prices) < slow + signal:
        return None
    
    df = pd.DataFrame({'price': prices})
    
    ema_fast = df['price'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['price'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }


def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Optional[Dict]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return None
    
    recent_prices = prices[-period:]
    sma = recent_prices.mean()
    std = recent_prices.std()
    
    return {
        'upper': sma + (std_dev * std),
        'middle': sma,
        'lower': sma - (std_dev * std),
        'current': prices[-1]
    }


def calculate_volatility(prices: np.ndarray, period: int = 20) -> Optional[float]:
    """Calculate historical volatility (standard deviation)"""
    if len(prices) < period:
        return None
    
    returns = np.diff(prices[-period:]) / prices[-period:-1]
    return returns.std() * np.sqrt(252)  # Annualized


def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
    """Calculate Average True Range"""
    if len(highs) < period + 1:
        return None
    
    high_low = highs[1:] - lows[1:]
    high_close = np.abs(highs[1:] - closes[:-1])
    low_close = np.abs(lows[1:] - closes[:-1])
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range[-period:].mean()
    
    return atr


def get_all_indicators(candles: List[Dict], symbol: str) -> Dict:
    """
    Calculate all indicators for given candles
    Returns a comprehensive dict with all technical indicators
    """
    if not candles or len(candles) < 50:
        return None
    
    closes = np.array([c['c'] for c in candles], dtype=float)
    highs = np.array([c['h'] for c in candles], dtype=float)
    lows = np.array([c['l'] for c in candles], dtype=float)
    volumes = np.array([c['v'] for c in candles], dtype=float)
    
    indicators = {
        'symbol': symbol,
        'current_price': closes[-1],
        'sma_20': calculate_sma(closes, 20),
        'sma_50': calculate_sma(closes, 50),
        'sma_200': calculate_sma(closes, 200),
        'ema_12': calculate_ema(closes, 12),
        'ema_26': calculate_ema(closes, 26),
        'rsi': calculate_rsi(closes, 14),
        'macd': calculate_macd(closes),
        'bollinger': calculate_bollinger_bands(closes),
        'volatility': calculate_volatility(closes),
        'atr': calculate_atr(highs, lows, closes),
        'volume_avg': volumes[-20:].mean() if len(volumes) >= 20 else None
    }
    
    return indicators

