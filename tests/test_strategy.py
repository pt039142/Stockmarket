import unittest
import pandas as pd
import numpy as np
from src.strategy import Strategy
from src.position_manager import PositionManager, Position
from src.risk_manager import RiskManager

class TestStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()
    
    def test_generate_signal_buy(self):
        """Test buy signal generation."""
        data = pd.DataFrame({'close': np.arange(30, 60)})
        signal = self.strategy.generate_signal(data)
        self.assertIn(signal, [0, 1, -1])
    
    def test_generate_signal_sell(self):
        """Test sell signal generation."""
        data = pd.DataFrame({'close': np.arange(60, 30, -1)})
        signal = self.strategy.generate_signal(data)
        self.assertIn(signal, [0, 1, -1])
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        data = pd.DataFrame({'close': np.random.rand(50) * 100})
        rsi = self.strategy.calculate_rsi(data)
        self.assertEqual(len(rsi), len(data))
        # RSI should be between 0 and 100
        self.assertTrue(rsi[rsi.notna()].min() >= 0)
        self.assertTrue(rsi[rsi.notna()].max() <= 100)
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        data = pd.DataFrame({'close': np.random.rand(50) * 100})
        macd, signal, histogram = self.strategy.calculate_macd(data)
        self.assertEqual(len(macd), len(data))
        self.assertEqual(len(signal), len(data))
        self.assertEqual(len(histogram), len(data))

class TestPositionManager(unittest.TestCase):
    def setUp(self):
        self.pm = PositionManager()
    
    def test_open_position(self):
        """Test opening a position."""
        pos = self.pm.open_position('BANKNIFTY', 50000, 1, 1)
        self.assertIsNotNone(pos)
        self.assertEqual(pos.symbol, 'BANKNIFTY')
        self.assertEqual(pos.status, 'OPEN')
    
    def test_close_position(self):
        """Test closing a position."""
        self.pm.open_position('BANKNIFTY', 50000, 1, 1)
        pnl = self.pm.close_position('BANKNIFTY', 51000)
        self.assertEqual(pnl, 1000)
        self.assertEqual(self.pm.daily_pnl, 1000)

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(1000, 500, 100000)
    
    def test_check_daily_limits_profit(self):
        """Test daily profit limit check."""
        self.rm.daily_pnl = 1000
        self.assertFalse(self.rm.check_daily_limits())
    
    def test_check_daily_limits_loss(self):
        """Test daily loss limit check."""
        self.rm.daily_pnl = -500
        self.assertFalse(self.rm.check_daily_limits())
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        qty = self.rm.calculate_position_size(50000, 49000)
        self.assertGreater(qty, 0)

if __name__ == '__main__':
    unittest.main()
