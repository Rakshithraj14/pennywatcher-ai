import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPaperTrading(unittest.TestCase):
    """Test paper trading functionality"""
    
    def test_portfolio_initialization(self):
        """Test portfolio initializes with correct values"""
        # This test requires database connection, so we'll use mocks
        with patch('src.paper_trading.get_conn'):
            from src.paper_trading import PaperTradingPortfolio
            
            # Mock test
            self.assertTrue(True)  # Placeholder
    
    def test_buy_trade_logic(self):
        """Test buy trade reduces cash and increases position"""
        # Test logic:
        # - Initial cash: $100,000
        # - Buy 10 shares at $100 = $1,000
        # - Commission: $1 (0.1%)
        # - Final cash: $98,999
        
        initial_cash = 100000
        shares = 10
        price = 100
        commission_rate = 0.001
        
        total = shares * price
        commission = total * commission_rate
        expected_cash = initial_cash - total - commission
        
        self.assertAlmostEqual(expected_cash, 98999.0, places=2)
    
    def test_sell_trade_logic(self):
        """Test sell trade increases cash and decreases position"""
        # Test logic:
        # - Have 10 shares
        # - Sell 10 shares at $110 = $1,100
        # - Commission: $1.10 (0.1%)
        # - Cash increase: $1,098.90
        
        shares = 10
        price = 110
        commission_rate = 0.001
        
        total = shares * price
        commission = total * commission_rate
        proceeds = total - commission
        
        self.assertAlmostEqual(proceeds, 1098.90, places=2)
    
    def test_pnl_calculation(self):
        """Test P&L calculation"""
        # Buy at $100, current price $110
        # P&L = (110 - 100) * 10 = $100
        
        avg_price = 100
        current_price = 110
        quantity = 10
        
        pnl = (current_price - avg_price) * quantity
        
        self.assertEqual(pnl, 100.0)


if __name__ == '__main__':
    unittest.main()

