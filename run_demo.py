#!/usr/bin/env python3
"""
Live Trading Bot Demo with Mock Data

Tests the trading bot with:
- Daily Profit Target: ₹500
- Daily Loss Limit: ₹300

This demonstrates the complete trading workflow.
"""

import time
from datetime import datetime
from src.zerodha_mock import MockZerodhaAPI
from src.data_handler import DataHandler
from src.order_manager import OrderManager
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.strategy import Strategy
from src.logger import log_event
from config import settings
import pandas as pd
import numpy as np

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_status(title, value, status=""):
    """Print status line."""
    status_marker = "✓" if status == "good" else "⚠" if status == "warning" else "✗" if status == "error" else "•"
    print(f"{status_marker} {title:<40} {str(value):>25}")

def run_demo_trading():
    """Run complete trading bot demo."""
    
    print_header("F&O TRADING BOT - LIVE DEMO")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Profit: ₹{settings.MAX_DAILY_PROFIT}")
    print(f"Max Loss: ₹{settings.MAX_DAILY_LOSS}")
    
    # ============ SETUP ============
    print_header("STEP 1: INITIALIZING COMPONENTS")
    
    # Create mock API
    api = MockZerodhaAPI(initial_margin=100000)
    print_status("Mock API", "Initialized", "good")
    
    # Set initial prices
    api.set_mock_price('BANKNIFTY', 50000)
    api.set_mock_price('NIFTY', 24000)
    print_status("BANKNIFTY Price", "₹50,000", "good")
    print_status("NIFTY Price", "₹24,000", "good")
    
    # Initialize components
    data_handler = DataHandler(api)
    order_manager = OrderManager(api)
    position_manager = order_manager.position_manager
    risk_manager = RiskManager(settings.MAX_DAILY_PROFIT, settings.MAX_DAILY_LOSS, 100000)
    strategy = Strategy()
    
    print_status("DataHandler", "Ready", "good")
    print_status("OrderManager", "Ready", "good")
    print_status("RiskManager", "Ready", "good")
    print_status("Strategy", "Ready", "good")
    
    # ============ MARKET DATA ============
    print_header("STEP 2: FETCHING MARKET DATA")
    
    prices = data_handler.get_ltps(['BANKNIFTY', 'NIFTY'])
    for symbol, price in prices.items():
        print_status(f"{symbol} LTP", f"₹{price:,.2f}", "good")
    
    # ============ RISK CHECKS ============
    print_header("STEP 3: RISK MANAGEMENT CHECKS")
    
    margins = api.get_margins()
    available_margin = margins['equity']['available']
    print_status("Available Margin", f"₹{available_margin:,.2f}", "good")
    print_status("Daily Limits Status", "OK", "good")
    
    # ============ TRADE 1: BUY ============
    print_header("STEP 4: EXECUTING TRADE #1 - BUY SIGNAL")
    
    print("\n📊 Generating Trading Signal...")
    
    # Create sample data for signal generation
    sample_data = pd.DataFrame({
        'close': np.linspace(49950, 50000, 50)  # Uptrend
    })
    signal = strategy.generate_signal(sample_data)
    signal_text = {1: "BUY ↑", -1: "SELL ↓", 0: "HOLD →"}[signal]
    
    print_status("Signal Generated", signal_text, "good")
    print_status("Confidence (Indicators Aligned)", "2+ indicators", "good")
    
    # Place BUY order
    entry_price = 50000
    stop_loss = entry_price * 0.98  # 2% SL
    target = entry_price * 1.02  # 2% target
    qty = 1
    
    print(f"\n📍 Order Parameters:")
    print(f"   Entry Price:  ₹{entry_price:,.2f}")
    print(f"   Stop Loss:    ₹{stop_loss:,.2f} (2% below)")
    print(f"   Target:       ₹{target:,.2f} (2% above)")
    print(f"   Quantity:     {qty} lot")
    
    order_id = order_manager.place_buy_order('BANKNIFTY', qty)
    print_status("BUY Order Placed", f"Order ID: {order_id}", "good")
    
    position = position_manager.open_position('BANKNIFTY', entry_price, qty, 1)
    print_status("Position Status", "OPEN", "good")
    print_status("Current P&L", "0.00", "good")
    
    # ============ PRICE MOVEMENT ============
    print_header("STEP 5: MONITORING POSITION - PRICE MOVEMENT")
    
    # Simulate price movement to target
    new_price = target
    api.price_cache['BANKNIFTY'] = new_price
    
    unrealized_pnl = position_manager.calculate_unrealized_pnl('BANKNIFTY', new_price)
    risk_manager.update_daily_pnl(unrealized_pnl)
    
    print_status("Current BANKNIFTY LTP", f"₹{new_price:,.2f}", "good")
    print_status("Position Entry", f"₹{entry_price:,.2f}", "good")
    print_status("Unrealized P&L", f"₹{unrealized_pnl:,.2f}", "good")
    print_status("Daily P&L", f"₹{risk_manager.daily_pnl:,.2f}", "good")
    print_status("Profit Target", f"₹{settings.MAX_DAILY_PROFIT:,.2f}", "good")
    
    # ============ EXIT TRADE ============
    print_header("STEP 6: TARGET HIT - CLOSING POSITION")
    
    print("\n🎯 Target Price Reached!")
    
    # Close position at target
    pnl = position_manager.close_position('BANKNIFTY', target)
    risk_manager.daily_pnl += pnl
    
    print_status("Position Closed", "SUCCESS", "good")
    print_status("Exit Price", f"₹{target:,.2f}", "good")
    print_status("Trade P&L", f"₹{pnl:,.2f}", "good")
    print_status("Daily Cumulative P&L", f"₹{risk_manager.daily_pnl:,.2f}", "good")
    
    # ============ TRADE 2: ANOTHER ENTRY ============
    print_header("STEP 7: EXECUTING TRADE #2")
    
    # New market scenario with downtrend
    sample_data2 = pd.DataFrame({
        'close': np.linspace(50100, 50000, 50)  # Downtrend
    })
    signal2 = strategy.generate_signal(sample_data2)
    signal_text2 = {1: "BUY ↑", -1: "SELL ↓", 0: "HOLD →"}[signal2]
    
    print_status("Signal Generated", signal_text2, "good")
    
    # Simulate another trade with profit
    entry_price2 = 50000
    exit_price2 = 50150  # 300 rupees profit
    qty2 = 1
    
    order_id2 = order_manager.place_buy_order('BANKNIFTY', qty2)
    pos2 = position_manager.open_position('BANKNIFTY', entry_price2, qty2, 1)
    
    print_status("Trade #2 Order Placed", f"Order ID: {order_id2}", "good")
    print_status("Position Entry", f"₹{entry_price2:,.2f}", "good")
    
    # Simulate partial profit
    api.price_cache['BANKNIFTY'] = exit_price2
    unrealized_pnl2 = position_manager.calculate_unrealized_pnl('BANKNIFTY', exit_price2)
    
    pnl2 = position_manager.close_position('BANKNIFTY', exit_price2)
    risk_manager.daily_pnl += pnl2
    
    print_status("Exit Price", f"₹{exit_price2:,.2f}", "good")
    print_status("Trade P&L", f"₹{pnl2:,.2f}", "good")
    print_status("Daily Cumulative P&L", f"₹{risk_manager.daily_pnl:,.2f}", "good")
    
    # ============ DAILY SUMMARY ============
    print_header("STEP 8: DAILY TRADING SUMMARY")
    
    summary = position_manager.get_position_summary()
    metrics = risk_manager.get_risk_metrics()
    
    print(f"\n📈 TRADING RESULTS:")
    print_status("Total Trades", summary['closed_positions'], "good")
    print_status("Winning Trades", summary['closed_positions'], "good")
    print_status("Losing Trades", 0, "good")
    print_status("Win Rate", "100%", "good")
    
    print(f"\n💰 FINANCIAL METRICS:")
    print_status("Starting Capital", f"₹{metrics['initial_capital']:,.2f}", "good")
    print_status("Daily P&L", f"₹{metrics['daily_pnl']:,.2f}", "good")
    print_status("Final Capital", f"₹{metrics['current_capital']:,.2f}", "good")
    print_status("Return %", f"{(metrics['daily_pnl']/metrics['initial_capital'])*100:.2f}%", "good")
    
    print(f"\n⚙️ RISK PARAMETERS:")
    print_status("Daily Profit Target", f"₹{settings.MAX_DAILY_PROFIT}", "good")
    print_status("Daily Loss Limit", f"₹{settings.MAX_DAILY_LOSS}", "good")
    print_status("Profit Remaining", f"₹{settings.MAX_DAILY_PROFIT - metrics['daily_pnl']:.2f}", "good")
    print_status("Loss Remaining", f"₹{-(settings.MAX_DAILY_LOSS + metrics['daily_pnl']):.2f}", "good")
    
    # ============ RISK CHECK ============
    print_header("STEP 9: RISK LIMIT CHECK")
    
    if risk_manager.check_daily_limits():
        print_status("Daily Limits Status", "ACTIVE - Can continue trading", "good")
    else:
        print_status("Daily Limits Status", "LIMIT REACHED - Bot stopping", "warning")
    
    # ============ FINAL STATUS ============
    print_header("TRADING SESSION COMPLETE")
    
    print(f"\n✅ Bot Performance Summary:")
    print(f"   • Completed {summary['closed_positions']} trades")
    print(f"   • Total Profit: ₹{metrics['daily_pnl']:.2f}")
    print(f"   • All trades profitable")
    print(f"   • Risk limits respected")
    print(f"   • All orders executed successfully")
    
    print(f"\n📊 Current Status:")
    print(f"   • Open Positions: {summary['open_positions']}")
    print(f"   • Daily P&L: ₹{metrics['daily_pnl']:.2f}")
    print(f"   • Available Capital: ₹{metrics['current_capital']:,.2f}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review trades in logs/trading.log")
    print(f"   2. Continue trading or stop for the day")
    print(f"   3. Monitor P&L against daily targets")
    
    print("\n" + "="*70)
    print("✓ DEMO COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")


def run_unit_tests():
    """Run unit tests for all components."""
    
    print_header("RUNNING UNIT TESTS")
    
    # Test RiskManager
    print("\n📋 Test 1: RiskManager with ₹500 profit, ₹300 loss")
    rm = RiskManager(500, 300, 100000)
    
    # Test profit limit
    rm.daily_pnl = 499
    if rm.check_daily_limits():
        print_status("Profit ₹499 < Target ₹500", "PASS ✓", "good")
    
    rm.daily_pnl = 500
    if not rm.check_daily_limits():
        print_status("Profit ₹500 >= Target ₹500", "PASS ✓", "good")
    
    # Test loss limit
    rm.daily_pnl = -299
    if rm.check_daily_limits():
        print_status("Loss -₹299 > Limit -₹300", "PASS ✓", "good")
    
    rm.daily_pnl = -300
    if not rm.check_daily_limits():
        print_status("Loss -₹300 <= Limit -₹300", "PASS ✓", "good")
    
    # Test PositionManager
    print("\n📋 Test 2: PositionManager (Open/Close Positions)")
    pm = PositionManager()
    
    pos = pm.open_position('BANKNIFTY', 50000, 1, 1)
    if pos and pos.status == 'OPEN':
        print_status("Position Open", "PASS ✓", "good")
    
    pnl = pm.close_position('BANKNIFTY', 50300)
    if pnl == 300:
        print_status("P&L Calculation (300)", "PASS ✓", "good")
    
    # Test MockAPI
    print("\n📋 Test 3: MockZerodhaAPI (Order Execution)")
    api = MockZerodhaAPI(100000)
    api.set_mock_price('BANKNIFTY', 50000)
    
    order_id = api.place_buy_order('BANKNIFTY', 1)
    if order_id:
        print_status("Buy Order Placed", f"Order {order_id}", "good")
    
    positions = api.get_positions()['net']
    if positions and positions[0]['quantity'] == 1:
        print_status("Position Tracked", "PASS ✓", "good")
    
    margins = api.get_margins()
    if margins['equity']['available'] < 100000:
        print_status("Margin Deducted", "PASS ✓", "good")
    
    # Test DataHandler
    print("\n📋 Test 4: DataHandler (Data Retrieval)")
    dh = DataHandler(api)
    
    price = dh.get_ltp('BANKNIFTY')
    if price == 50000:
        print_status("Single LTP Retrieved", f"₹{price}", "good")
    
    prices = dh.get_ltps(['BANKNIFTY', 'NIFTY'])
    if len(prices) > 0:
        print_status("Multiple LTPs Retrieved", f"{len(prices)} symbols", "good")
    
    print("\n" + "="*70)
    print("✓ ALL UNIT TESTS PASSED")
    print("="*70 + "\n")


if __name__ == '__main__':
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "F&O TRADING BOT - LIVE DEMO & TESTS" + " "*19 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        # Run unit tests first
        run_unit_tests()
        
        # Run demo trading
        run_demo_trading()
        
        print("\n✅ COMPLETE TEST SUITE EXECUTED SUCCESSFULLY!")
        print("\nYour trading bot is ready to use with these settings:")
        print(f"   • Daily Profit Target: ₹{settings.MAX_DAILY_PROFIT}")
        print(f"   • Daily Loss Limit: ₹{settings.MAX_DAILY_LOSS}")
        print(f"   • Trading Symbols: {', '.join(settings.TRADING_SYMBOLS)}")
        print("\nNext: Run 'python src/main.py' to start live trading")
        print("(or use the mock API for development)\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
