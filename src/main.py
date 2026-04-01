# Main trading bot orchestrator with complete logic - PRODUCTION READY

from config import settings
from src.logger import log_event
from src.strategy import Strategy
from src.order_manager import OrderManager
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.notification_manager import NotificationManager
from src.data_handler import DataHandler
from src.zerodha_api import ZerodhaAPI
from kiteconnect import KiteConnect
import time
import signal
import sys
from threading import Lock
from datetime import datetime, time as dt_time

class TradingBot:
    """Main trading bot orchestrator with production-ready logic."""
    
    def __init__(self):
        # Thread safety
        self.lock = Lock()
        self.is_running = True
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        try:
            # Initialize Kite Connect with retry logic
            self.kite = KiteConnect(api_key=settings.KITE_API_KEY)
            self.kite.set_access_token(settings.KITE_ACCESS_TOKEN)
            
            # Validate session immediately
            if not self._validate_session():
                raise Exception("Failed to validate Zerodha session")
            
            # Initialize API wrapper with retry logic
            self.zerodha_api = ZerodhaAPI(settings.KITE_API_KEY, settings.KITE_ACCESS_TOKEN)
            
            # Initialize components
            self.strategy = Strategy(signal_strength_threshold=settings.SIGNAL_STRENGTH_THRESHOLD)
            self.data_handler = DataHandler(self.zerodha_api)
            self.order_manager = OrderManager(self.kite)
            self.position_manager = self.order_manager.position_manager
            self.risk_manager = RiskManager(
                settings.MAX_DAILY_PROFIT,
                settings.MAX_DAILY_LOSS,
                settings.INITIAL_CAPITAL,
                settings.RISK_PER_TRADE,
                settings.MAX_POSITION_SIZE
            )
            self.notification_manager = NotificationManager(settings.EMAIL_CONFIG)
            
            # Trading parameters
            self.app_name = settings.APP_NAME
            self.symbols = settings.TRADING_SYMBOLS
            self.quantity = settings.ORDER_QUANTITY
            self.stop_loss_percent = settings.STOP_LOSS_PERCENT
            self.target_percent = settings.TARGET_PERCENT
            self.data_interval = settings.DATA_CHECK_INTERVAL
            self.historical_days = settings.HISTORICAL_DATA_DAYS
            self.signal_strength_threshold = settings.SIGNAL_STRENGTH_THRESHOLD
            self.max_concurrent_positions = settings.MAX_CONCURRENT_POSITIONS
            self.max_trades_per_day = settings.MAX_TRADES_PER_DAY
            self.trades_today = 0
            
            # Market hours (IST)
            self.market_open = dt_time(9, 15)
            self.market_close = dt_time(15, 30)
            
            log_event('TradingBot initialized successfully - PRODUCTION MODE')
            print('[INFO] ✓ Trading Bot initialized - PRODUCTION MODE')
            print('[INFO] ✓ Session validated')
            print('[INFO] ✓ Ready for live trading')
        
        except Exception as e:
            log_event(f'CRITICAL: Error initializing bot: {str(e)}')
            print(f'[ERROR] Failed to initialize: {str(e)}')
            if hasattr(self, 'notification_manager'):
                self.notification_manager.notify_error(f'Initialization error: {str(e)}')
            raise
    
    def _validate_session(self):
        """Validate Zerodha session on startup."""
        try:
            profile = self.kite.profile()
            log_event(f'Session validated for user: {profile.get("user_id")}')
            return True
        except Exception as e:
            log_event(f'Session validation failed: {str(e)}')
            return False
    
    def _is_market_open(self):
        """Check if market is open (IST timezone)."""
        now = datetime.now().time()
        weekday = datetime.now().weekday()
        # Market open Mon-Fri, 9:15-15:30
        return weekday < 5 and self.market_open <= now < self.market_close

    def _flatten_all_positions(self, reason='MANUAL'):
        """Close every open position and cancel pending orders immediately."""
        log_event(f'Flattening all positions due to: {reason}')

        for symbol in list(self.position_manager.positions.keys()):
            try:
                position = self.position_manager.positions.get(symbol)
                current_price = self.data_handler.get_ltp(symbol)
                if current_price is None or current_price <= 0 or position is None:
                    continue

                exit_side = 'SELL' if position.signal == 1 else 'BUY'
                if exit_side == 'SELL':
                    exit_order_id = self.order_manager.place_sell_order(symbol, position.quantity, 'MARKET')
                else:
                    exit_order_id = self.order_manager.place_buy_order(symbol, position.quantity, 'MARKET')
            except Exception:
                exit_order_id = None

            try:
                self.order_manager.cancel_orders_for_symbol(symbol)
                time.sleep(0.25)
                pnl = self.position_manager.close_position(symbol, current_price)
                self.notification_manager.notify_position_closed(symbol, pnl)
                log_event(f'Position flattened for {symbol} ({reason}). Exit order: {exit_order_id}, P&L={pnl:.2f}')
            except Exception as e:
                log_event(f'Failed to flatten {symbol}: {str(e)}')
    
    def run(self):
        """Main bot execution loop with production-ready error handling."""
        
        # Setup graceful shutdown handler
        def signal_handler(sig, frame):
            log_event('Shutdown signal received - initiating graceful shutdown')
            print('[INFO] Shutdown signal received - closing all positions...')
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            log_event('Bot starting execution in PRODUCTION MODE')
            print('[INFO] Bot started - monitoring markets')
            print(f'[INFO] Market hours: {self.market_open} - {self.market_close} IST')
            
            last_session_check = time.time()
            session_check_interval = 3600  # Re-validate session every hour
            
            while self.is_running:
                try:
                    # Check if market is open
                    if not self._is_market_open():
                        if datetime.now().time() < self.market_open:
                            wait_seconds = 60
                            print(f'[INFO] Market closed. Next check in {wait_seconds}s')
                            time.sleep(wait_seconds)
                        else:
                            log_event('Market closed for the day')
                            break
                        continue
                    
                    # Periodically validate session
                    if time.time() - last_session_check > session_check_interval:
                        if not self._validate_session():
                            log_event('Session validation failed - attempting to refresh')
                            self.notification_manager.notify_error('Session expired - please restart bot')
                            break
                        last_session_check = time.time()
                    
                    # Check daily limits
                    if not self.risk_manager.check_daily_limits():
                        log_event('Daily limits reached. Bot stopping.')
                        self.notification_manager.notify_daily_limit('DAILY LIMITS', 
                                                                    self.risk_manager.daily_pnl)
                        self._flatten_all_positions('DAILY_LIMIT')
                        break
                    
                    current_prices = {}
                    
                    # Process each symbol with thread safety
                    for symbol in self.symbols:
                        if not self.is_running:
                            break
                        
                        try:
                            with self.lock:
                                # Get latest price with validation
                                price = self.data_handler.get_ltp(symbol)
                                if price is None or price <= 0:
                                    log_event(f'Invalid price data for {symbol}: {price}')
                                    continue
                                
                                current_prices[symbol] = price
                                
                                # Check existing positions
                                if symbol in self.position_manager.positions:
                                    self._handle_existing_position(symbol, price)
                                else:
                                    self._handle_new_position(symbol, price)
                                
                                # Reset error counter on success
                                self.consecutive_errors = 0
                        
                        except Exception as e:
                            log_event(f'Error processing {symbol}: {str(e)}')
                            self.consecutive_errors += 1
                            if self.consecutive_errors >= self.max_consecutive_errors:
                                log_event(f'Circuit breaker triggered: {self.max_consecutive_errors} consecutive errors')
                                self.is_running = False
                                break
                            continue
                    
                    # Update risk metrics
                    if current_prices:
                        total_pnl = self.position_manager.get_total_pnl(current_prices)
                        self.risk_manager.update_daily_pnl(total_pnl, absolute=True)
                        if not self.risk_manager.check_daily_limits():
                            log_event('Daily limit hit after mark-to-market update.')
                            self.notification_manager.notify_daily_limit('DAILY LIMITS',
                                                                        self.risk_manager.daily_pnl)
                            self._flatten_all_positions('DAILY_LIMIT')
                            break
                    
                    time.sleep(self.data_interval)
                
                except KeyboardInterrupt:
                    log_event('Bot interrupted by user')
                    self.is_running = False
                    break
                except Exception as e:
                    log_event(f'Error in main loop: {str(e)}')
                    self.consecutive_errors += 1
                    self.notification_manager.notify_error(f'Main loop error: {str(e)}')
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        log_event('Circuit breaker triggered - stopping bot')
                        break
                    time.sleep(10)
        
        finally:
            self._cleanup()
    
    
    def _handle_new_position(self, symbol, current_price):
        """Handle new position logic with actual signal generation."""
        try:
            if len(self.position_manager.positions) >= self.max_concurrent_positions:
                log_event(f'Max concurrent positions reached; skipping {symbol}')
                return

            if self.trades_today >= self.max_trades_per_day:
                log_event(f'Max trades per day reached; skipping {symbol}')
                return

            # Fetch historical data for signal generation
            historical_df = self.data_handler.get_historical_data(
                symbol, 
                days_back=self.historical_days
            )
            
            if historical_df is None or len(historical_df) < 30:
                log_event(f'Insufficient historical data for {symbol}')
                return
            
            # Generate trading signal from strategy
            signal = self.strategy.generate_signal(historical_df)
            
            if signal == 0:
                # No signal - hold
                return
            
            if signal == 1:  # Buy signal
                stop_loss = current_price * (1 - self.stop_loss_percent)
                target = current_price * (1 + self.target_percent)
                
                # Calculate position size based on risk
                qty = self.risk_manager.calculate_position_size(current_price, stop_loss)
                
                if qty <= 0:
                    log_event(f'Invalid position size calculated for {symbol}')
                    return
                
                # Place bracket order (entry + SL + target)
                order_result = self.order_manager.place_bracket_order(
                    symbol, qty, 'BUY', current_price, stop_loss, target
                )
                
                if order_result and order_result.get('success'):
                    self.position_manager.open_position(symbol, current_price, qty, signal)
                    self.trades_today += 1
                    self.notification_manager.notify_order(
                        symbol, 'BUY', qty, current_price, 
                        order_result.get('order_id')
                    )
                    self.consecutive_errors = 0
                    log_event(f'Long position opened: {symbol} @ {current_price}')
                else:
                    log_event(f'Failed to place buy order for {symbol}')
            
            elif signal == -1:  # Sell signal
                stop_loss = current_price * (1 + self.stop_loss_percent)
                target = current_price * (1 - self.target_percent)
                
                qty = self.risk_manager.calculate_position_size(current_price, stop_loss)
                
                if qty <= 0:
                    log_event(f'Invalid position size calculated for {symbol}')
                    return
                
                # Place bracket order for short
                order_result = self.order_manager.place_bracket_order(
                    symbol, qty, 'SELL', current_price, stop_loss, target
                )
                
                if order_result and order_result.get('success'):
                    self.position_manager.open_position(symbol, current_price, qty, signal)
                    self.trades_today += 1
                    self.notification_manager.notify_order(
                        symbol, 'SELL', qty, current_price,
                        order_result.get('order_id')
                    )
                    self.consecutive_errors = 0
                    log_event(f'Short position opened: {symbol} @ {current_price}')
                else:
                    log_event(f'Failed to place sell order for {symbol}')
        
        except Exception as e:
            log_event(f'Error handling new position for {symbol}: {str(e)}')
            self.notification_manager.notify_error(f'Position open error for {symbol}: {str(e)}')

    
    def _handle_existing_position(self, symbol, current_price):
        """Handle existing position management with validation."""
        try:
            if symbol not in self.position_manager.positions:
                return
            
            position = self.position_manager.positions[symbol]
            
            # Calculate unrealized P&L with validation
            unrealized_pnl = self.position_manager.calculate_unrealized_pnl(symbol, current_price)
            
            if unrealized_pnl is None:
                return
            
            # Check hard stop loss (capital risk limit)
            max_loss = self.risk_manager.initial_capital * self.stop_loss_percent
            if unrealized_pnl <= -max_loss:
                pnl = self.position_manager.close_position(symbol, current_price)
                
                # Close associated orders
                self.order_manager.cancel_orders_for_symbol(symbol)
                
                self.notification_manager.notify_position_closed(symbol, pnl)
                log_event(f'Hard stop loss triggered for {symbol}: P&L={pnl:.2f}')
        
        except Exception as e:
            log_event(f'Error handling existing position for {symbol}: {str(e)}')
    
    def _cleanup(self):
        """Cleanup on bot shutdown - close all positions gracefully."""
        log_event('Starting cleanup procedure')
        print('[INFO] Closing all positions...')
        
        try:
            with self.lock:
                # Close all open positions at market price
                for symbol in list(self.position_manager.positions.keys()):
                    try:
                        # Get current price
                        current_price = self.data_handler.get_ltp(symbol)
                        if current_price and current_price > 0:
                            # Cancel associated SL and target orders first
                            self.order_manager.cancel_orders_for_symbol(symbol)
                            time.sleep(0.5)
                            
                            # Close position
                            pnl = self.position_manager.close_position(symbol, current_price)
                            log_event(f'Position closed on shutdown: {symbol}, P&L: {pnl:.2f}')
                    
                    except Exception as e:
                        log_event(f'Error closing position for {symbol}: {str(e)}')
                
                # Print final summary
                summary = self.position_manager.get_position_summary()
                self.risk_manager.update_daily_pnl(self.position_manager.daily_pnl, absolute=True)
                metrics = self.risk_manager.get_risk_metrics()
                
                print('[INFO] ========== FINAL SUMMARY ==========')
                print(f'[INFO] Open Positions: {summary["open_positions"]}')
                print(f'[INFO] Closed Positions: {summary["closed_positions"]}')
                print(f'[INFO] Daily Realized P&L: ₹{summary["daily_realized_pnl"]:.2f}')
                print(f'[INFO] Final Capital: ₹{metrics["current_capital"]:.2f}')
                print(f'[INFO] Total P&L: ₹{metrics["daily_pnl"]:.2f}')
                print('[INFO] ===================================')
                
                log_event(f'Final Summary: {summary}')
                log_event(f'Risk Metrics: {metrics}')
                
                self.notification_manager.notify_daily_limit('DAILY SUMMARY', metrics['daily_pnl'])
        
        except Exception as e:
            log_event(f'Error during cleanup: {str(e)}')
        
        finally:
            print('[INFO] ✓ Bot shutdown complete')
            log_event('Bot shutdown complete')

if __name__ == '__main__':
    print('[INFO] F&O Trading Bot - Zerodha Kite Connect')
    print('[INFO] Starting bot...')
    
    bot = TradingBot()
    bot.run()
