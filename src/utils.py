import os
import json
from datetime import datetime

class Utils:
    """Utility functions for trading bot."""
    
    @staticmethod
    def create_env_file(api_key, api_secret, access_token):
        """Create .env file with credentials."""
        env_content = f"""KITE_API_KEY={api_key}
KITE_API_SECRET={api_secret}
KITE_ACCESS_TOKEN={access_token}
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print('[INFO] .env file created successfully')
    
    @staticmethod
    def load_env_file():
        """Load credentials from .env file."""
        if not os.path.exists('.env'):
            return False
        
        with open('.env', 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                os.environ[key] = value
        
        return True
    
    @staticmethod
    def format_currency(amount):
        """Format amount as Indian currency."""
        return f"₹{amount:,.2f}"
    
    @staticmethod
    def get_market_hours():
        """Get NSE market hours."""
        return {
            'open': '09:15',
            'close': '15:30',
            'pre_open': '09:00'
        }
    
    @staticmethod
    def is_market_open():
        """Check if market is open."""
        from datetime import datetime, time
        now = datetime.now().time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        return market_open <= now <= market_close
    
    @staticmethod
    def save_trade_log(trades, filename='trade_log.json'):
        """Save trades to JSON file."""
        with open(filename, 'w') as f:
            json.dump(trades, f, indent=4, default=str)
    
    @staticmethod
    def load_trade_log(filename='trade_log.json'):
        """Load trades from JSON file."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
        """Calculate Sharpe ratio."""
        import numpy as np
        excess_returns = returns - (risk_free_rate / 252)
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
