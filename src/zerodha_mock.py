"""
Mock Zerodha API for Testing and Development

Simulates Zerodha API responses without making real API calls.
Useful for testing, backtesting, and development.
"""

import random
from datetime import datetime, timedelta
import pandas as pd
from src.logger import log_event

class MockZerodhaAPI:
    """Mock Zerodha API for testing."""
    
    def __init__(self, initial_margin=100000):
        """
        Initialize mock API.
        
        Args:
            initial_margin (float): Starting margin balance
        """
        self.margin = initial_margin
        self.initial_margin = initial_margin
        self.orders = {}
        self.positions = {}
        self.trades = []
        self.order_counter = 1000
        self.price_cache = {}
        
        log_event('MockZerodhaAPI initialized for testing')
    
    def set_mock_price(self, symbol, price):
        """Set mock price for a symbol."""
        self.price_cache[symbol] = price
    
    def get_ltp(self, symbols):
        """
        Mock LTP fetch.
        
        Args:
            symbols (list or str): Symbols to fetch
        
        Returns:
            dict: Mock LTP data
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        ltp_data = {}
        for symbol in symbols:
            clean_symbol = symbol.replace('NSE:', '')
            if clean_symbol in self.price_cache:
                price = self.price_cache[clean_symbol]
            else:
                # Generate random price if not set
                price = random.uniform(40000, 60000)
            
            ltp_data[symbol] = {
                'last_price': price,
                'timestamp': datetime.now().timestamp()
            }
        
        return ltp_data
    
    def get_quote(self, symbols):
        """Mock quote data."""
        if isinstance(symbols, str):
            symbols = [symbols]
        
        quote_data = {}
        for symbol in symbols:
            clean_symbol = symbol.replace('NSE:', '')
            ltp = self.price_cache.get(clean_symbol, 50000)
            
            quote_data[symbol] = {
                'open': ltp * 0.99,
                'high': ltp * 1.02,
                'low': ltp * 0.98,
                'close': ltp,
                'volume': random.randint(1000000, 5000000),
                'last_price': ltp
            }
        
        return quote_data
    
    def place_order(self, symbol, side, quantity, order_type='MARKET', price=0):
        """
        Mock order placement.
        
        Returns:
            str: Mock order ID
        """
        order_id = str(self.order_counter)
        self.order_counter += 1
        
        clean_symbol = symbol.replace('NSE:', '')
        current_price = self.price_cache.get(clean_symbol, 50000)
        
        if order_type == 'LIMIT':
            current_price = price
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': current_price,
            'order_type': order_type,
            'status': 'COMPLETE',
            'timestamp': datetime.now()
        }
        
        self.orders[order_id] = order
        
        # Simulate trade execution
        if side == 'BUY':
            cost = current_price * quantity
            self.margin -= cost
            
            if symbol not in self.positions:
                self.positions[symbol] = {'quantity': 0, 'entry_price': 0, 'side': 'BUY'}
            
            self.positions[symbol]['quantity'] += quantity
            self.positions[symbol]['entry_price'] = current_price
        
        elif side == 'SELL':
            proceeds = current_price * quantity
            self.margin += proceeds
            
            if symbol in self.positions:
                self.positions[symbol]['quantity'] -= quantity
                if self.positions[symbol]['quantity'] == 0:
                    del self.positions[symbol]
        
        log_event(f'Mock order placed: {order_id} - {side} {quantity} {symbol} @ {current_price}')
        return order_id
    
    def place_buy_order(self, symbol, quantity, order_type='MARKET', price=0):
        """Place mock buy order."""
        return self.place_order(symbol, 'BUY', quantity, order_type, price)
    
    def place_sell_order(self, symbol, quantity, order_type='MARKET', price=0):
        """Place mock sell order."""
        return self.place_order(symbol, 'SELL', quantity, order_type, price)
    
    def cancel_order(self, order_id):
        """Mock order cancellation."""
        if order_id in self.orders:
            del self.orders[order_id]
            log_event(f'Mock order cancelled: {order_id}')
            return True
        return False
    
    def get_order_status(self, order_id=None):
        """Get mock order status."""
        if order_id:
            return self.orders.get(order_id)
        return list(self.orders.values())
    
    def get_positions(self):
        """Get mock positions."""
        return {
            'net': list(self.positions.values()),
            'day': list(self.positions.values())
        }
    
    def get_margins(self):
        """Get mock margin data."""
        return {
            'equity': {
                'available': self.margin,
                'utilised': self.initial_margin - self.margin,
                'balance': self.margin
            }
        }
    
    def get_available_margin(self):
        """Get mock available margin."""
        return self.margin
    
    def get_profile(self):
        """Get mock profile."""
        return {
            'user_id': 'MOCK_USER',
            'email': 'mock@example.com',
            'broker': 'Zerodha',
            'exchanges': ['NSE']
        }
    
    def validate_session(self):
        """Validate mock session."""
        return True
    
    def is_market_open(self):
        """Check if market is open."""
        from datetime import time
        now = datetime.now().time()
        return time(9, 15) <= now <= time(15, 30)
    
    def simulate_price_movement(self, symbol, change_percent):
        """Simulate price movement."""
        clean_symbol = symbol.replace('NSE:', '')
        current_price = self.price_cache.get(clean_symbol, 50000)
        new_price = current_price * (1 + change_percent / 100)
        self.price_cache[clean_symbol] = new_price
    
    def reset(self):
        """Reset mock API to initial state."""
        self.margin = self.initial_margin
        self.orders = {}
        self.positions = {}
        self.trades = []
        self.order_counter = 1000
        log_event('Mock API reset to initial state')
