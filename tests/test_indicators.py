import unittest
import numpy as np
from src.indicators import (
    calculate_sma, calculate_ema, calculate_rsi,
    calculate_macd, calculate_bollinger_bands
)


class TestIndicators(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Generate sample price data
        self.prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                                110, 108, 111, 113, 112, 115, 117, 116, 118, 120,
                                119, 121, 123, 122, 124, 126, 125, 127, 129, 128])
    
    def test_calculate_sma(self):
        """Test SMA calculation"""
        sma = calculate_sma(self.prices, 10)
        self.assertIsNotNone(sma)
        self.assertGreater(sma, 0)
        self.assertIsInstance(sma, (int, float, np.floating))
    
    def test_calculate_sma_insufficient_data(self):
        """Test SMA with insufficient data"""
        short_prices = np.array([100, 102, 101])
        sma = calculate_sma(short_prices, 10)
        self.assertIsNone(sma)
    
    def test_calculate_ema(self):
        """Test EMA calculation"""
        ema = calculate_ema(self.prices, 10)
        self.assertIsNotNone(ema)
        self.assertGreater(ema, 0)
    
    def test_calculate_rsi(self):
        """Test RSI calculation"""
        rsi = calculate_rsi(self.prices, 14)
        self.assertIsNotNone(rsi)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
    
    def test_calculate_macd(self):
        """Test MACD calculation"""
        long_prices = np.concatenate([self.prices, self.prices, self.prices])
        macd = calculate_macd(long_prices)
        self.assertIsNotNone(macd)
        self.assertIn('macd', macd)
        self.assertIn('signal', macd)
        self.assertIn('histogram', macd)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        bb = calculate_bollinger_bands(self.prices, 20)
        self.assertIsNotNone(bb)
        self.assertIn('upper', bb)
        self.assertIn('middle', bb)
        self.assertIn('lower', bb)
        
        # Upper should be greater than middle, middle greater than lower
        self.assertGreater(bb['upper'], bb['middle'])
        self.assertGreater(bb['middle'], bb['lower'])


class TestSignalLogic(unittest.TestCase):
    """Test signal generation logic"""
    
    def test_rsi_oversold(self):
        """Test RSI oversold condition"""
        # Prices declining = RSI should be low
        declining_prices = np.array([120, 118, 116, 114, 112, 110, 108, 106, 
                                     104, 102, 100, 98, 96, 94, 92, 90])
        rsi = calculate_rsi(declining_prices, 14)
        self.assertIsNotNone(rsi)
        self.assertLess(rsi, 50)  # Should indicate selling pressure
    
    def test_rsi_overbought(self):
        """Test RSI overbought condition"""
        # Prices rising = RSI should be high
        rising_prices = np.array([90, 92, 94, 96, 98, 100, 102, 104, 106, 
                                  108, 110, 112, 114, 116, 118, 120])
        rsi = calculate_rsi(rising_prices, 14)
        self.assertIsNotNone(rsi)
        self.assertGreater(rsi, 50)  # Should indicate buying pressure


if __name__ == '__main__':
    unittest.main()

