import pandas as pd
from datetime import datetime
from src.logger import log_event
from threading import Lock

class Position:
    """Represents a single trading position."""
    
    def __init__(self, symbol, entry_price, quantity, signal):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.signal = signal  # 1 for long, -1 for short
        self.entry_time = datetime.now()
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0
        self.status = 'OPEN'
    
    def close(self, exit_price):
        """Close position and calculate P&L."""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'CLOSED'
        
        if self.signal == 1:  # Long position
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:  # Short position
            self.pnl = (self.entry_price - exit_price) * self.quantity
        
        return self.pnl

class PositionManager:
    """Manages trading positions and P&L tracking - THREAD SAFE."""
    
    def __init__(self):
        self.positions = {}
        self.closed_positions = []
        self.daily_pnl = 0
        self.lock = Lock()  # Thread safety lock
        log_event('PositionManager initialized - THREAD SAFE MODE')
    
    def open_position(self, symbol, entry_price, quantity, signal):
        """Open a new position with thread safety."""
        try:
            with self.lock:
                # Validate inputs
                if entry_price <= 0 or quantity <= 0:
                    log_event(f'Invalid position parameters: price={entry_price}, qty={quantity}')
                    return None
                
                # Check for duplicate position
                if symbol in self.positions:
                    log_event(f'Position already exists for {symbol}')
                    return None
                
                position = Position(symbol, entry_price, quantity, signal)
                self.positions[symbol] = position
                
                log_event(f'Position OPEN: {symbol}, Price: {entry_price}, Qty: {quantity}, '
                         f'Signal: {"BUY" if signal == 1 else "SELL"}')
                return position
        
        except Exception as e:
            log_event(f'Error opening position for {symbol}: {str(e)}')
            return None
    
    def close_position(self, symbol, exit_price):
        """Close an existing position with thread safety."""
        try:
            with self.lock:
                if symbol not in self.positions:
                    log_event(f'No position found for {symbol}')
                    return 0
                
                # Validate exit price
                if exit_price <= 0:
                    log_event(f'Invalid exit price for {symbol}: {exit_price}')
                    return 0
                
                position = self.positions[symbol]
                pnl = position.close(exit_price)
                self.daily_pnl += pnl
                self.closed_positions.append(position)
                del self.positions[symbol]
                
                log_event(f'Position CLOSED: {symbol}, P&L: ₹{pnl:.2f}, '
                         f'Daily P&L: ₹{self.daily_pnl:.2f}')
                return pnl
        
        except Exception as e:
            log_event(f'Error closing position for {symbol}: {str(e)}')
            return 0
    
    def calculate_unrealized_pnl(self, symbol, current_price):
        """Calculate unrealized P&L for open position - THREAD SAFE."""
        try:
            with self.lock:
                if symbol not in self.positions:
                    return 0
                
                # Validate price
                if current_price is None or current_price <= 0:
                    return None
                
                position = self.positions[symbol]
                
                if position.signal == 1:  # Long
                    unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:  # Short
                    unrealized_pnl = (position.entry_price - current_price) * position.quantity
                
                return unrealized_pnl
        
        except Exception as e:
            log_event(f'Error calculating unrealized P&L for {symbol}: {str(e)}')
            return None
    
    def get_total_pnl(self, current_prices):
        """Get total P&L (realized + unrealized) - THREAD SAFE."""
        try:
            with self.lock:
                realized_pnl = self.daily_pnl
                
                unrealized_pnl = 0
                for symbol in list(self.positions.keys()):
                    price = current_prices.get(symbol)
                    if price and price > 0:
                        position = self.positions[symbol]
                        if position.signal == 1:  # Long
                            unrealized_pnl += (price - position.entry_price) * position.quantity
                        else:  # Short
                            unrealized_pnl += (position.entry_price - price) * position.quantity
                
                return realized_pnl + unrealized_pnl
        
        except Exception as e:
            log_event(f'Error calculating total P&L: {str(e)}')
            return self.daily_pnl
    
    def get_open_positions(self):
        """Get all open positions - THREAD SAFE."""
        with self.lock:
            return dict(self.positions)
    
    def get_position_summary(self):
        """Get summary of positions - THREAD SAFE."""
        with self.lock:
            summary = {
                'open_positions': len(self.positions),
                'closed_positions': len(self.closed_positions),
                'daily_realized_pnl': self.daily_pnl
            }
            return summary


