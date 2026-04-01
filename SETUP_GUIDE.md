# Setup Guide - F&O Trading Bot

## Quick Start (5 Minutes)

### 1. Get Zerodha API Credentials

1. Visit [Zerodha Console](https://console.zerodha.com/)
2. Log in with your trading account
3. Go to **API Console** → **Create new app**
4. Fill in details and create
5. Copy your:
   - API Key (in API Console)
   - API Secret (shown once, save it securely)
   - Generate Access Token (via Kite app or terminal)

### 2. Setup Environment

```bash
# Clone/download project
cd FNO_TradingBot

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials

**Option A: Environment Variables (Recommended - More Secure)**

Windows (PowerShell):
```powershell
$env:KITE_API_KEY = "your_api_key_here"
$env:KITE_API_SECRET = "your_api_secret_here"
$env:KITE_ACCESS_TOKEN = "your_access_token_here"
```

Windows (Command Prompt):
```cmd
set KITE_API_KEY=your_api_key_here
set KITE_API_SECRET=your_api_secret_here
set KITE_ACCESS_TOKEN=your_access_token_here
```

Linux/Mac:
```bash
export KITE_API_KEY="your_api_key_here"
export KITE_API_SECRET="your_api_secret_here"
export KITE_ACCESS_TOKEN="your_access_token_here"
```

**Option B: .env File**

Create `.env` file in project root:
```
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here
```

Then load it:
```python
from src.utils import Utils
Utils.load_env_file()
```

### 4. Configure Trading Parameters

Edit `config/settings.py`:

```python
MAX_DAILY_PROFIT = 1000      # Your target daily profit
MAX_DAILY_LOSS = 500         # Your max daily loss
TRADING_SYMBOLS = ['BANKNIFTY', 'NIFTY']  # Symbols to trade
```

### 5. Run the Bot

```bash
python src/main.py
```

You should see:
```
[INFO] F&O Trading Bot - Zerodha Kite Connect
[INFO] Starting bot...
[INFO] Trading Bot initialized
[INFO] Bot started - monitoring markets
```

---

## Detailed Setup Instructions

### Getting Zerodha Access Token

**Method 1: Using Zerodha Console (Recommended)**

1. Login to [Zerodha Console](https://console.zerodha.com/)
2. Navigate to **API Console**
3. Under "Your Apps", select your app
4. Click **Generate Tokens**
5. Enter your credentials
6. Copy the **Access Token** shown

**Method 2: Using Kite API Terminal**

```bash
pip install requests

python -c "
from kiteconnect import KiteConnect
kite = KiteConnect(api_key='your_api_key')
print('Login URL:', kite.login_url())
"
```

Then follow the printed URL to get your request token and access token.

### Verifying Setup

Run a test to verify your credentials work:

```python
from config import settings
from kiteconnect import KiteConnect

kite = KiteConnect(api_key=settings.KITE_API_KEY)
kite.set_access_token(settings.KITE_ACCESS_TOKEN)

try:
    data = kite.ltp('NSE:BANKNIFTY')
    print("✓ Connection successful!")
    print(f"BANKNIFTY LTP: {data}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### Security Best Practices

1. **Never commit credentials** to code/git
2. **Use environment variables** instead of hardcoding
3. **Keep API Secret safe** - change after exposure
4. **Rotate tokens** periodically
5. **Use .env file** only for local development (add to .gitignore)
6. **On production**, use secure credential management

### Troubleshooting

**"API connection failed"**
- Verify internet connection
- Check credentials are correct
- Ensure market is open (9:15 AM - 3:30 PM)
- Restart the bot

**"ModuleNotFoundError: No module named 'kiteconnect'"**
```bash
pip install --upgrade -r requirements.txt
```

**"Access Token expired"**
- Generate a new access token from Zerodha Console
- Update environment variable/settings.py
- Restart the bot

**"No signals generated"**
- Check market is open
- Review logs: `tail -f logs/trading.log`
- Backtest your strategy first

### Next Steps

1. **Backtest Strategy**: Test on historical data first
   ```bash
   python -c "
   from src.backtester import Backtester
   from src.strategy import Strategy
   import pandas as pd
   
   # Load historical data
   data = pd.read_csv('historical_data.csv')
   
   # Backtest
   bt = Backtester(Strategy())
   results = bt.run_backtest(data)
   bt.print_results()
   "
   ```

2. **Paper Trade**: Test on Zerodha's paper trading account
   - Go to Zerodha Console
   - Enable Paper Trading
   - Use same bot code (no changes needed)

3. **Monitor Closely**: First live trades
   - Don't leave bot unattended
   - Check logs regularly
   - Monitor positions in Zerodha web

4. **Optimize Over Time**:
   - Track performance
   - Backtest new strategies
   - Adjust risk parameters
   - Add more symbols gradually

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check internet, verify API key/token |
| "Invalid request" | Ensure market is open (9:15 AM - 3:30 PM) |
| No orders placed | Check position limits, verify signals |
| High slippage | Use LIMIT orders, trade liquid symbols |
| Bot crashes | Check logs, review error message, restart |

---

## Support

For issues with:
- **Kite Connect API**: [Kite API Docs](https://kite.trade/)
- **Trading Questions**: [Zerodha Community](https://tradingqna.com/)
- **Python Issues**: Check logs at `logs/trading.log`

**Always backtest strategies BEFORE live trading!**
