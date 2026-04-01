# Order execution logic - PRODUCTION READY

from src.logger import log_event
from src.position_manager import PositionManager
import time

class OrderManager:
    """Manages order placement and execution with Kite Connect - Production Ready."""
    
    def __init__(self, kite):
        self.kite = kite
        self.position_manager = PositionManager()
        self.orders = {}  # Track order IDs per symbol
        self.symbol_orders = {}  # Symbol -> [order_ids] mapping
        log_event('OrderManager initialized - PRODUCTION MODE')
    
    def place_buy_order(self, symbol, quantity, order_type='MARKET', price=0):
        """Place a buy order with confirmation."""
        try:
            order_args = {
                'variety': 'regular',
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': 'BUY',
                'order_type': order_type,
                'quantity': quantity,
                'price': price if order_type == 'LIMIT' else 0,
            }
            order_id = self.kite.place_order(**order_args)
            
            if order_id:
                self._track_order(symbol, order_id, 'BUY', quantity)
                log_event(f'BUY Order placed: {symbol}, Qty: {quantity}, Order ID: {order_id}')
            
            return order_id
        except Exception as e:
            log_event(f'Error placing buy order for {symbol}: {str(e)}')
            return None
    
    def place_sell_order(self, symbol, quantity, order_type='MARKET', price=0):
        """Place a sell order with confirmation."""
        try:
            order_args = {
                'variety': 'regular',
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': 'SELL',
                'order_type': order_type,
                'quantity': quantity,
                'price': price if order_type == 'LIMIT' else 0,
            }
            order_id = self.kite.place_order(**order_args)
            
            if order_id:
                self._track_order(symbol, order_id, 'SELL', quantity)
                log_event(f'SELL Order placed: {symbol}, Qty: {quantity}, Order ID: {order_id}')
            
            return order_id
        except Exception as e:
            log_event(f'Error placing sell order for {symbol}: {str(e)}')
            return None
    
    def place_stop_loss(self, symbol, quantity, trigger_price, limit_price, transaction_type='SELL'):
        """Place a stop-loss order."""
        try:
            order_args = {
                'variety': 'regular',
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': transaction_type,
                'order_type': 'STOPLOSS',
                'quantity': quantity,
                'price': limit_price,
                'trigger_price': trigger_price,
            }
            order_id = self.kite.place_order(**order_args)
            
            if order_id:
                self._track_order(symbol, order_id, f'SL_{transaction_type}', quantity)
                log_event(f'Stop-Loss placed: {symbol}, Trigger: {trigger_price}, Limit: {limit_price}, Order ID: {order_id}')
            
            return order_id
        except Exception as e:
            log_event(f'Error placing stop-loss for {symbol}: {str(e)}')
            return None
    
    def place_target_order(self, symbol, quantity, target_price, transaction_type='SELL'):
        """Place a target/profit-taking order."""
        try:
            order_args = {
                'variety': 'regular',
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': transaction_type,
                'order_type': 'LIMIT',
                'quantity': quantity,
                'price': target_price,
            }
            order_id = self.kite.place_order(**order_args)
            
            if order_id:
                self._track_order(symbol, order_id, f'TARGET_{transaction_type}', quantity)
                log_event(f'Target order placed: {symbol}, Target Price: {target_price}, Order ID: {order_id}')
            
            return order_id
        except Exception as e:
            log_event(f'Error placing target order for {symbol}: {str(e)}')
            return None
    
    def place_bracket_order(self, symbol, quantity, side, entry_price, stop_loss, target):
        """Place bracket order (entry + SL + target)."""
        try:
            # Place entry order
            if side == 'BUY':
                entry_id = self.place_buy_order(symbol, quantity, 'MARKET')
            else:
                entry_id = self.place_sell_order(symbol, quantity, 'MARKET')
            
            if not entry_id:
                return {'success': False, 'order_id': None}
            
            # Place SL order
            protective_side = 'SELL' if side == 'BUY' else 'BUY'
            sl_id = self.place_stop_loss(symbol, quantity, stop_loss, stop_loss, protective_side)
            if not sl_id:
                self.cancel_order(entry_id)
                return {'success': False, 'order_id': entry_id}
            
            # Place target order (opposite side)
            target_side = 'SELL' if side == 'BUY' else 'BUY'
            target_id = self.place_target_order(symbol, quantity, target, target_side)
            if not target_id:
                self.cancel_order(sl_id)
                self.cancel_order(entry_id)
                return {'success': False, 'order_id': entry_id}
            
            log_event(f'Bracket order completed: Entry={entry_id}, SL={sl_id}, Target={target_id}')
            
            return {
                'success': True,
                'order_id': entry_id,
                'sl_id': sl_id,
                'target_id': target_id
            }
        
        except Exception as e:
            log_event(f'Error placing bracket order for {symbol}: {str(e)}')
            return {'success': False, 'order_id': None}
    
    def get_order_status(self, order_id):
        """Get status of an order."""
        try:
            orders = self.kite.orders()
            for order in orders:
                if order['order_id'] == order_id:
                    return order['status']
            return None
        except Exception as e:
            log_event(f'Error fetching order status: {str(e)}')
            return None
    
    def cancel_order(self, order_id):
        """Cancel an existing order."""
        try:
            self.kite.cancel_order(order_id, variety='regular')
            log_event(f'Order cancelled: {order_id}')
            return True
        except Exception as e:
            log_event(f'Error cancelling order {order_id}: {str(e)}')
            return False
    
    def cancel_orders_for_symbol(self, symbol):
        """Cancel all orders related to a symbol (SL and target orders)."""
        try:
            if symbol in self.symbol_orders:
                for order_id in self.symbol_orders[symbol]:
                    self.cancel_order(order_id)
                del self.symbol_orders[symbol]
            
            log_event(f'All orders cancelled for {symbol}')
            return True
        
        except Exception as e:
            log_event(f'Error cancelling orders for {symbol}: {str(e)}')
            return False
    
    def _track_order(self, symbol, order_id, side, quantity):
        """Track order internally for management."""
        self.orders[order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'timestamp': time.time() if 'time' in globals() else None
        }
        
        if symbol not in self.symbol_orders:
            self.symbol_orders[symbol] = []
        
        self.symbol_orders[symbol].append(order_id)
    
    def check_limits(self, profit, loss, max_profit, max_loss):
        """Check if daily profit/loss limits are breached."""
        if profit >= max_profit:
            log_event('MAX DAILY PROFIT REACHED - Stopping bot')
            return False
        if loss <= -max_loss:
            log_event('MAX DAILY LOSS REACHED - Stopping bot')
            return False
        return True
