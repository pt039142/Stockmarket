import pandas as pd
import numpy as np
from datetime import datetime
from src.logger import log_event
from src.strategy import Strategy

class Backtester:
    """Backtests trading strategies against historical data."""
    
    def __init__(self, strategy, initial_capital=100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.results = {}
        log_event('Backtester initialized')
    
    def run_backtest(self, data, entry_quantity=1, entry_signal_threshold=1):
        """Run backtest on historical data."""
        try:
            log_event('Starting backtest...')
            position = None
            entry_price = None
            
            for idx in range(len(data)):
                current_data = data.iloc[:idx+1]
                signal = self.strategy.generate_signal(current_data)
                current_price = data['close'].iloc[idx]
                
                # Entry logic
                if position is None and signal == 1:
                    position = 'LONG'
                    entry_price = current_price
                    entry_idx = idx
                
                elif position is None and signal == -1:
                    position = 'SHORT'
                    entry_price = current_price
                    entry_idx = idx
                
                # Exit logic (simple: next signal or after 5 bars)
                elif position == 'LONG' and (signal == -1 or idx - entry_idx >= 5):
                    pnl = (current_price - entry_price) * entry_quantity
                    self.current_capital += pnl
                    self.trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'return': (pnl / entry_price) * 100
                    })
                    position = None
                    if signal == 1:
                        position = 'LONG'
                        entry_price = current_price
                
                elif position == 'SHORT' and (signal == 1 or idx - entry_idx >= 5):
                    pnl = (entry_price - current_price) * entry_quantity
                    self.current_capital += pnl
                    self.trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'return': (pnl / entry_price) * 100
                    })
                    position = None
                    if signal == -1:
                        position = 'SHORT'
                        entry_price = current_price
            
            self._calculate_results()
            return self.results
        
        except Exception as e:
            log_event(f'Error in backtest: {str(e)}')
            return {}
    
    def _calculate_results(self):
        """Calculate backtest results."""
        if not self.trades:
            self.results = {'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
            return
        
        trades_df = pd.DataFrame(self.trades)
        total_pnl = trades_df['pnl'].sum()
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        total_trades = len(trades_df)
        
        self.results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': (winning_trades / total_trades) * 100 if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl': trades_df['pnl'].mean(),
            'max_profit': trades_df['pnl'].max(),
            'max_loss': trades_df['pnl'].min(),
            'profit_factor': abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0,
            'final_capital': self.current_capital,
            'total_return': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        }
        
        log_event(f'Backtest complete: {self.results}')
    
    def print_results(self):
        """Print backtest results in readable format."""
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        for key, value in self.results.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        print("="*50 + "\n")
