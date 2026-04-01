# Zerodha API Integration Guide

Complete guide to using the Zerodha API wrapper for the F&O Trading Bot.

## Overview

The trading bot includes a comprehensive Zerodha API wrapper with multiple components:

- **ZerodhaAPI**: Main production API wrapper
- **ZerodhaAuth**: Authentication and session management
- **MockZerodhaAPI**: Testing/development mock API
- **DataHandler**: Simplified data access layer

---

## 1. Using ZerodhaAPI (Production)

### Basic Setup

```python
from config import settings
from src.zerodha_api import ZerodhaAPI

# Initialize API
api = ZerodhaAPI(settings.KITE_API_KEY, settings.KITE_ACCESS_TOKEN)

# Verify connection
if api.validate_session():
    print("✓ Connected to Zerodha")
```

### Market Data

#### Get Last Traded Price (LTP)

```python
# Single symbol
ltp = api.get_ltp('BANKNIFTY')
print(f"BANKNIFTY LTP: {ltp}")

# Multiple symbols
prices = api.get_ltp(['BANKNIFTY', 'NIFTY'])
for symbol, data in prices.items():
    print(f"{symbol}: {data['last_price']}")
```

#### Get Quote Data (OHLC)

```python
# Get OHLC and other quote data
quote = api.get_quote('BANKNIFTY')
print(f"Open: {quote['ohlc']['open']}")
print(f"High: {quote['ohlc']['high']}")
print(f"Low: {quote['ohlc']['low']}")
print(f"Close: {quote['ohlc']['close']}")
```

#### Get Historical Data

```python
import pandas as pd

# Fetch historical data
token = api.get_instrument_token('BANKNIFTY')
historical = api.get_historical_data(
    token, 
    from_date='2024-01-01', 
    to_date='2024-03-31', 
    interval='15minute'
)

# Convert to DataFrame
df = pd.DataFrame(historical)
print(df.head())
```

### Order Management

#### Place Buy Order

```python
# Market order
order_id = api.place_buy_order('BANKNIFTY', quantity=1)
print(f"Order placed: {order_id}")

# Limit order
order_id = api.place_buy_order(
    'BANKNIFTY', 
    quantity=1, 
    order_type='LIMIT', 
    price=50000
)
```

#### Place Sell Order

```python
order_id = api.place_sell_order('BANKNIFTY', quantity=1)
```

#### Place Stop-Loss Order

```python
order_id = api.place_stop_loss(
    'BANKNIFTY',
    quantity=1,
    trigger_price=49000,
    limit_price=48950  # Optional
)
```

#### Cancel Order

```python
success = api.cancel_order(order_id)
if success:
    print("Order cancelled")
```

#### Modify Order

```python
success = api.modify_order(
    order_id, 
    quantity=2,  # New quantity
    price=51000  # New price
)
```

#### Get Order Status

```python
# Get specific order
order = api.get_order_status(order_id)
print(f"Status: {order['status']}")

# Get all orders
all_orders = api.get_order_status()
for order in all_orders:
    print(f"{order['order_id']}: {order['status']}")
```

### Positions & Holdings

#### Get Current Positions

```python
positions = api.get_positions()

# Intraday positions
for pos in positions['net']:
    print(f"{pos['symbol']}: {pos['quantity']} @ {pos['average_price']}")
```

#### Get Holdings

```python
holdings = api.get_holdings()
for holding in holdings:
    print(f"{holding['tradingsymbol']}: {holding['quantity']}")
```

#### Get Executed Trades

```python
trades = api.get_trades()
for trade in trades:
    print(f"{trade['tradingsymbol']}: {trade['quantity']} @ {trade['price']}")
```

### Account Management

#### Get Margins

```python
margins = api.get_margins()

# Available margin
available = margins['equity']['available']
print(f"Available: ₹{available}")

# Used margin
used = margins['equity']['utilised']
print(f"Used: ₹{used}")
```

#### Get Profile

```python
profile = api.get_profile()
print(f"User ID: {profile['user_id']}")
print(f"Email: {profile['email']}")
```

### Market Hours

#### Check Market Status

```python
if api.is_market_open():
    print("Market is open")
else:
    print("Market is closed")
```

#### Wait for Market Open

```python
api.wait_for_market_open()
print("Market opened, starting trading")
```

### Utilities

#### Retry on Failure

```python
def fetch_ltp():
    return api.get_ltp('BANKNIFTY')

# Retry 3 times with 2-second delay
ltp = api.retry_on_failure(fetch_ltp, max_retries=3, delay=2)
```

#### Clear Cache

```python
api.clear_cache()  # Clear instruments cache
```

---

## 2. Using ZerodhaAuth (Authentication)

### Get Login URL

```python
from src.zerodha_auth import ZerodhaAuth

auth = ZerodhaAuth(api_key, api_secret)
login_url = auth.get_login_url()
print(f"Visit: {login_url}")
```

### Generate Access Token

```python
# After login, you get a request token
request_token = "your_request_token"

access_token = auth.generate_access_token(request_token)
print(f"Access Token: {access_token}")
```

### Session Management

```python
from src.zerodha_auth import SessionManager

session = SessionManager(api_key, api_secret, access_token)

# Get valid token (loads from file or uses provided)
token = session.get_valid_access_token()

# Check if token is still valid
if session.refresh_session():
    print("Session is valid")
```

---

## 3. Using MockZerodhaAPI (Testing)

Mock API is perfect for development and backtesting without real API calls.

### Setup Mock API

```python
from src.zerodha_mock import MockZerodhaAPI

# Create mock API with initial margin
mock_api = MockZerodhaAPI(initial_margin=100000)

# Set mock prices
mock_api.set_mock_price('BANKNIFTY', 50000)
mock_api.set_mock_price('NIFTY', 24000)
```

### Testing Orders

```python
# Place mock buy order
order_id = mock_api.place_buy_order('BANKNIFTY', quantity=1)
print(f"Order ID: {order_id}")

# Check positions
positions = mock_api.get_positions()
print(f"Positions: {positions}")

# Check margins
margins = mock_api.get_margins()
print(f"Available: {margins['equity']['available']}")
```

### Simulate Price Changes

```python
# Simulate 5% price increase
mock_api.simulate_price_movement('BANKNIFTY', 5)

# Get new price
ltp = mock_api.get_ltp('NSE:BANKNIFTY')
print(f"New LTP: {ltp}")
```

### Reset Mock API

```python
mock_api.reset()  # Reset to initial state
```

---

## 4. Using DataHandler

### Setup DataHandler

```python
from src.data_handler import DataHandler
from src.zerodha_api import ZerodhaAPI

api = ZerodhaAPI(api_key, access_token)
data_handler = DataHandler(api)
```

### Get Prices

```python
# Single symbol
price = data_handler.get_ltp('BANKNIFTY')

# Multiple symbols
prices = data_handler.get_ltps(['BANKNIFTY', 'NIFTY'])
```

### Get Quote Data

```python
quote = data_handler.get_quote('BANKNIFTY')
print(f"OHLC: {quote['ohlc']}")
```

### Get Historical Data

```python
# Fetch for backtesting
df = data_handler.get_historical_data(
    'BANKNIFTY',
    '2024-01-01',
    '2024-03-31',
    interval='15minute'
)

print(df)
```

### Caching

```python
# Cache quote
data_handler.cache_quote('BANKNIFTY', quote_data)

# Get cached quote (if < 60 seconds old)
cached = data_handler.get_cached_quote('BANKNIFTY', max_age=60)
```

### Data Streaming

```python
def on_price_update(prices):
    for symbol, price in prices.items():
        print(f"{symbol}: {price}")

# Stream prices with 1-second interval
data_handler.stream_data(['BANKNIFTY', 'NIFTY'], on_price_update, interval=1)
```

---

## 5. Integration with Trading Bot

### Using in Main Bot

```python
from config import settings
from src.zerodha_api import ZerodhaAPI
from src.data_handler import DataHandler
from src.order_manager import OrderManager

# Initialize API
api = ZerodhaAPI(settings.KITE_API_KEY, settings.KITE_ACCESS_TOKEN)

# Initialize data handler
data_handler = DataHandler(api)

# Initialize order manager
order_manager = OrderManager(api)

# Get prices
prices = data_handler.get_ltps(['BANKNIFTY', 'NIFTY'])

# Place order
order_id = order_manager.place_buy_order('BANKNIFTY', 1)
```

### Using Mock API for Testing

```python
from src.zerodha_mock import MockZerodhaAPI
from src.data_handler import DataHandler

# Use mock API instead
mock_api = MockZerodhaAPI()
data_handler = DataHandler(mock_api)

# Works exactly like production API
prices = data_handler.get_ltps(['BANKNIFTY'])
```

---

## 6. Error Handling

### Try-Catch Pattern

```python
try:
    order_id = api.place_buy_order('BANKNIFTY', 1)
    if order_id:
        print(f"Order placed: {order_id}")
    else:
        print("Order placement failed")
except Exception as e:
    print(f"Error: {e}")
    log_event(f"Order placement error: {str(e)}")
```

### Validate Before Trading

```python
# Check market hours
if not api.is_market_open():
    print("Market is closed")
    exit()

# Check session validity
if not api.validate_session():
    print("Session expired")
    exit()

# Check available margin
margin = api.get_available_margin()
if margin < 10000:
    print("Insufficient margin")
    exit()
```

---

## 7. Using Retry Logic

```python
# Automatic retry on failure
def fetch_ltp():
    return api.get_ltp('BANKNIFTY')

# Retry 5 times with 3-second delay
ltp = api.retry_on_failure(fetch_ltp, max_retries=5, delay=3)
```

---

## 8. Common Use Cases

### Complete Trade Flow

```python
from config import settings
from src.zerodha_api import ZerodhaAPI
from src.data_handler import DataHandler
from src.risk_manager import RiskManager

# Setup
api = ZerodhaAPI(settings.KITE_API_KEY, settings.KITE_ACCESS_TOKEN)
data_handler = DataHandler(api)
risk_manager = RiskManager(1000, 500, 100000)

# Get current price
price = data_handler.get_ltp('BANKNIFTY')
print(f"Current price: {price}")

# Calculate position size
entry = price
sl = price * 0.98  # 2% SL
qty = risk_manager.calculate_position_size(entry, sl)

# Place order
order_id = api.place_buy_order('BANKNIFTY', qty)

# Place stop-loss
sl_order = api.place_stop_loss('BANKNIFTY', qty, sl)

# Place target
target = price * 1.05
target_order = api.place_order('BANKNIFTY', 'SELL', qty, 'LIMIT', target)

print(f"Trade executed: Entry={entry}, SL={sl}, Target={target}")
```

### Monitor Open Positions

```python
# Get all positions
positions = api.get_positions()

for pos in positions['net']:
    symbol = pos['symbol']
    current_price = data_handler.get_ltp(symbol.replace('NSE:', ''))
    entry_price = pos['average_price']
    pnl = (current_price - entry_price) * pos['quantity']
    
    print(f"{symbol}: {pos['quantity']} @ {entry_price}, Current: {current_price}, P&L: {pnl}")
```

### Backtest with Historical Data

```python
from src.backtester import Backtester
from src.strategy import Strategy

# Get historical data
df = data_handler.get_historical_data('BANKNIFTY', '2024-01-01', '2024-03-31')

# Backtest
strategy = Strategy()
backtester = Backtester(strategy)
results = backtester.run_backtest(df)

print(results)
```

---

## 9. Troubleshooting

### Connection Error

```
Error: Connection refused
```

**Solution:**
```python
# Check internet connection
api.validate_session()

# Verify credentials
if not api.validate_session():
    print("Invalid credentials or session expired")
```

### Market Closed

```python
# Check market hours
if not api.is_market_open():
    print("Market is closed. Hours: 9:15 AM - 3:30 PM")
```

### Insufficient Margin

```python
# Check available margin
margin = api.get_available_margin()
required = price * quantity

if margin < required:
    print(f"Insufficient margin. Available: {margin}, Required: {required}")
```

### Rate Limiting

```python
# Use retry logic with delays
api.retry_on_failure(fetch_ltp, max_retries=3, delay=2)
```

---

## 10. Best Practices

1. **Always validate session before trading**
   ```python
   if not api.validate_session():
       exit("Session invalid")
   ```

2. **Use try-catch for all API calls**
   ```python
   try:
       result = api.get_ltp('BANKNIFTY')
   except Exception as e:
       log_event(f"Error: {e}")
   ```

3. **Check market hours**
   ```python
   if not api.is_market_open():
       wait_for_market_open()
   ```

4. **Use mock API for testing**
   ```python
   from src.zerodha_mock import MockZerodhaAPI
   api = MockZerodhaAPI()  # Development
   ```

5. **Log all API calls**
   ```python
   from src.logger import log_event
   log_event(f"Placed order: {order_id}")
   ```

6. **Cache frequently accessed data**
   ```python
   data_handler.cache_quote('BANKNIFTY', quote)
   cached = data_handler.get_cached_quote('BANKNIFTY')
   ```

7. **Always use risk management**
   ```python
   risk_mgr.check_daily_limits()  # Before placing orders
   ```

---

For more details, see README.md and STRATEGY_GUIDE.md
