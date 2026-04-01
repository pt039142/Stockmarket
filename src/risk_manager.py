from src.logger import log_event
from threading import Lock

class RiskManager:
    """Manages risk parameters and position sizing - THREAD SAFE."""
    
    def __init__(self, max_daily_profit, max_daily_loss, initial_capital=100000,
                 risk_per_trade=0.02, max_position_size=10):
        self.max_daily_profit = max_daily_profit
        self.max_daily_loss = max_daily_loss
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_pnl = 0.0
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.lock = Lock()  # Thread safety lock
        
        log_event(f'RiskManager initialized - THREAD SAFE MODE')
        log_event(f'Risk Limits: Profit={max_daily_profit}, Loss={max_daily_loss}, Capital={initial_capital}')
    
    def update_daily_pnl(self, pnl, absolute=False):
        """Update daily P&L with thread safety."""
        with self.lock:
            if absolute:
                self.daily_pnl = float(pnl)
            else:
                self.daily_pnl += float(pnl)
            self.current_capital = self.initial_capital + self.daily_pnl
    
    def check_daily_limits(self):
        """Check if daily limits are breached - THREAD SAFE."""
        with self.lock:
            if self.daily_pnl >= self.max_daily_profit:
                log_event(f'⚠️ MAX DAILY PROFIT REACHED: ₹{self.daily_pnl:.2f}')
                return False
            
            if self.daily_pnl <= -self.max_daily_loss:
                log_event(f'⚠️ MAX DAILY LOSS REACHED: ₹{self.daily_pnl:.2f}')
                return False
            
            return True
    
    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size based on risk management."""
        try:
            with self.lock:
                if entry_price <= 0 or stop_loss_price <= 0:
                    return 0

                risk_amount = self.current_capital * self.risk_per_trade
                price_difference = abs(entry_price - stop_loss_price)
                
                if price_difference == 0:
                    return 0
                
                # Calculate position size
                position_size = int(risk_amount / price_difference)
                
                # Ensure reasonable limits
                position_size = max(1, min(position_size, self.max_position_size))
                
                log_event(f'Position size calculated: {position_size} '
                         f'(Risk: ₹{risk_amount:.2f}, Price diff: ₹{price_difference:.2f})')
                
                return position_size
        
        except Exception as e:
            log_event(f'Error calculating position size: {str(e)}')
            return 1
    
    def get_risk_metrics(self):
        """Get current risk metrics - THREAD SAFE."""
        with self.lock:
            profit_remaining = self.max_daily_profit - self.daily_pnl
            loss_remaining = self.max_daily_loss + self.daily_pnl  # Note: daily_pnl is negative for losses
            
            metrics = {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'daily_pnl': self.daily_pnl,
                'profit_remaining': profit_remaining,
                'loss_remaining': loss_remaining,
                'capital_utilization': 0 if self.initial_capital == 0 else \
                                      max(0, (self.initial_capital - self.current_capital) / self.initial_capital),
                'profit_target_reached': self.daily_pnl >= self.max_daily_profit,
                'loss_limit_hit': self.daily_pnl <= -self.max_daily_loss,
            }
            return metrics

    def reset_daily_state(self, starting_capital=None):
        """Reset the daily counters for a fresh session."""
        with self.lock:
            self.daily_pnl = 0.0
            if starting_capital is not None:
                self.initial_capital = float(starting_capital)
                self.current_capital = float(starting_capital)
            else:
                self.current_capital = self.initial_capital
