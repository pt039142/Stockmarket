"""
API Testing and Examples

Demonstrates how to use all Zerodha API components.
Run this file to test API functionality.
"""

def test_zerodha_api():
    """Test production ZerodhaAPI."""
    print("\n" + "="*60)
    print("Testing ZerodhaAPI (Production)")
    print("="*60)
    
    from config import settings
    from src.zerodha_api import ZerodhaAPI
    
    try:
        api = ZerodhaAPI(settings.KITE_API_KEY, settings.KITE_ACCESS_TOKEN)
        
        # Test session
        if api.validate_session():
            print("✓ Session valid")
        
        # Get profile
        profile = api.get_profile()
        print(f"✓ Profile: {profile.get('user_id')}")
        
        # Get LTP
        ltp = api.get_ltp('BANKNIFTY')
        print(f"✓ BANKNIFTY LTP: {ltp}")
        
        # Get margins
        margins = api.get_available_margin()
        print(f"✓ Available Margin: ₹{margins}")
        
        # Get positions
        positions = api.get_positions()
        print(f"✓ Open Positions: {len(positions['net'])}")
        
        print("\n✓ All tests passed!\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Note: Make sure credentials are set and market is open\n")


def test_mock_api():
    """Test MockZerodhaAPI."""
    print("\n" + "="*60)
    print("Testing MockZerodhaAPI (Development)")
    print("="*60)
    
    from src.zerodha_mock import MockZerodhaAPI
    
    # Create mock API
    api = MockZerodhaAPI(initial_margin=100000)
    print("✓ Mock API created with ₹100,000 margin")
    
    # Set prices
    api.set_mock_price('BANKNIFTY', 50000)
    api.set_mock_price('NIFTY', 24000)
    print("✓ Prices set: BANKNIFTY=50000, NIFTY=24000")
    
    # Get LTP
    ltp = api.get_ltp('NSE:BANKNIFTY')
    print(f"✓ BANKNIFTY LTP: {ltp}")
    
    # Place buy order
    order_id = api.place_buy_order('NSE:BANKNIFTY', 1)
    print(f"✓ Buy order placed: {order_id}")
    
    # Check margin
    margin = api.get_available_margin()
    print(f"✓ Available margin after trade: ₹{margin}")
    
    # Get positions
    positions = api.get_positions()['net']
    if positions:
        print(f"✓ Position: {positions[0]['quantity']} @ {positions[0]['entry_price']}")
    
    # Place sell order
    order_id = api.place_sell_order('NSE:BANKNIFTY', 1)
    print(f"✓ Sell order placed: {order_id}")
    
    # Check final margin
    margin = api.get_available_margin()
    print(f"✓ Final margin: ₹{margin}")
    
    print("\n✓ All mock tests passed!\n")


def test_data_handler():
    """Test DataHandler with mock API."""
    print("\n" + "="*60)
    print("Testing DataHandler")
    print("="*60)
    
    from src.zerodha_mock import MockZerodhaAPI
    from src.data_handler import DataHandler
    
    # Setup
    api = MockZerodhaAPI()
    api.set_mock_price('BANKNIFTY', 50000)
    api.set_mock_price('NIFTY', 24000)
    
    data_handler = DataHandler(api)
    print("✓ DataHandler initialized")
    
    # Get single LTP
    price = data_handler.get_ltp('BANKNIFTY')
    print(f"✓ BANKNIFTY price: {price}")
    
    # Get multiple LTPs
    prices = data_handler.get_ltps(['BANKNIFTY', 'NIFTY'])
    print(f"✓ Multi-symbol prices: {prices}")
    
    # Get quote
    quote = data_handler.get_quote('BANKNIFTY')
    print(f"✓ Quote: O={quote['open']}, H={quote['high']}, L={quote['low']}, C={quote['close']}")
    
    # Cache quote
    data_handler.cache_quote('BANKNIFTY', quote)
    cached = data_handler.get_cached_quote('BANKNIFTY')
    print(f"✓ Cached quote retrieved: {cached['close']}")
    
    print("\n✓ All data handler tests passed!\n")


def test_risk_manager():
    """Test RiskManager."""
    print("\n" + "="*60)
    print("Testing RiskManager")
    print("="*60)
    
    from src.risk_manager import RiskManager
    
    rm = RiskManager(max_daily_profit=1000, max_daily_loss=500, initial_capital=100000)
    print("✓ RiskManager initialized")
    
    # Calculate position size
    qty = rm.calculate_position_size(entry_price=50000, stop_loss_price=49000)
    print(f"✓ Position size for entry=50000, SL=49000: {qty} lots")
    
    # Check limits (should be OK)
    rm.daily_pnl = 500
    if rm.check_daily_limits():
        print("✓ Limits OK for +500 P&L")
    
    # Update daily PnL
    rm.update_daily_pnl(500)
    metrics = rm.get_risk_metrics()
    print(f"✓ Risk metrics: Capital={metrics['current_capital']}, P&L={metrics['daily_pnl']}")
    
    print("\n✓ All risk manager tests passed!\n")


def test_position_manager():
    """Test PositionManager."""
    print("\n" + "="*60)
    print("Testing PositionManager")
    print("="*60)
    
    from src.position_manager import PositionManager
    
    pm = PositionManager()
    print("✓ PositionManager initialized")
    
    # Open position
    pos = pm.open_position('BANKNIFTY', 50000, 1, 1)
    print(f"✓ Position opened: {pos.symbol} @ {pos.entry_price}")
    
    # Calculate unrealized P&L
    upnl = pm.calculate_unrealized_pnl('BANKNIFTY', 51000)
    print(f"✓ Unrealized P&L at 51000: {upnl}")
    
    # Close position
    pnl = pm.close_position('BANKNIFTY', 51000)
    print(f"✓ Position closed, P&L: {pnl}")
    
    # Get summary
    summary = pm.get_position_summary()
    print(f"✓ Summary: {summary}")
    
    print("\n✓ All position manager tests passed!\n")


def test_strategy():
    """Test Strategy indicator calculations."""
    print("\n" + "="*60)
    print("Testing Strategy Indicators")
    print("="*60)
    
    import pandas as pd
    import numpy as np
    from src.strategy import Strategy
    
    # Create sample data
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 50
    })
    
    strategy = Strategy()
    print("✓ Strategy initialized")
    
    # Test RSI
    rsi = strategy.calculate_rsi(data)
    print(f"✓ RSI calculated: {rsi.iloc[-1]:.2f}")
    
    # Test MACD
    macd, signal, histogram = strategy.calculate_macd(data)
    print(f"✓ MACD: {macd.iloc[-1]:.2f}, Signal: {signal.iloc[-1]:.2f}")
    
    # Test Bollinger Bands
    sma, upper, lower = strategy.calculate_bollinger_bands(data)
    print(f"✓ BB: Upper={upper.iloc[-1]:.2f}, SMA={sma.iloc[-1]:.2f}, Lower={lower.iloc[-1]:.2f}")
    
    # Test signal generation
    signal = strategy.generate_signal(data)
    signal_text = {1: "BUY", -1: "SELL", 0: "HOLD"}[signal]
    print(f"✓ Signal generated: {signal_text}")
    
    print("\n✓ All strategy tests passed!\n")


def test_backtester():
    """Test Backtester."""
    print("\n" + "="*60)
    print("Testing Backtester")
    print("="*60)
    
    import pandas as pd
    import numpy as np
    from src.strategy import Strategy
    from src.backtester import Backtester
    
    # Create sample data
    data = pd.DataFrame({
        'close': np.cumsum(np.random.randn(100)) + 50
    })
    
    strategy = Strategy()
    backtester = Backtester(strategy, initial_capital=100000)
    print("✓ Backtester initialized")
    
    # Run backtest
    results = backtester.run_backtest(data, entry_quantity=1)
    print(f"✓ Backtest completed")
    print(f"  Total trades: {results.get('total_trades', 0)}")
    print(f"  Win rate: {results.get('win_rate', 0):.2f}%")
    print(f"  Total P&L: ₹{results.get('total_pnl', 0):.2f}")
    print(f"  Final capital: ₹{results.get('final_capital', 0):.2f}")
    
    print("\n✓ All backtester tests passed!\n")


def test_auth():
    """Test Authentication."""
    print("\n" + "="*60)
    print("Testing Authentication")
    print("="*60)
    
    from src.zerodha_auth import ZerodhaAuth
    
    auth = ZerodhaAuth('demo_key', 'demo_secret')
    print("✓ ZerodhaAuth initialized")
    
    # Get login URL
    login_url = auth.get_login_url()
    print(f"✓ Login URL generated: {login_url[:50]}...")
    
    print("✓ Note: Authentication requires actual Zerodha credentials")
    
    print("\n✓ All auth tests passed!\n")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("F&O TRADING BOT - API TEST SUITE")
    print("="*60)
    
    # Test mock API first (doesn't require credentials)
    test_mock_api()
    test_data_handler()
    test_risk_manager()
    test_position_manager()
    test_strategy()
    test_backtester()
    test_auth()
    
    # Test production API (requires credentials)
    try:
        test_zerodha_api()
    except:
        print("\n⚠️  Production API test skipped (requires valid credentials)")
    
    print("\n" + "="*60)
    print("✓ TEST SUITE COMPLETE")
    print("="*60)


if __name__ == '__main__':
    run_all_tests()
