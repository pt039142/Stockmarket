# PrinceStockExhange

Backend trading engine for `PrinceStockExhange`, built on Zerodha Kite Connect.

# F&O Trading Bot - Zerodha Kite Connect

A **professional-grade, end-to-end F&O (Futures & Options) trading bot** for NSE using Zerodha Kite Connect API. Built with robust risk management, advanced strategy logic, real-time data handling, and comprehensive logging.

## Features

- **Real-time Market Data**: Fetch LTP, OHLC, and historical data from Kite Connect
- **Advanced Technical Analysis**: 
  - Relative Strength Index (RSI)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Moving Average Crossovers
- **Automated Order Execution**: Buy, Sell, Stop-Loss, and Target orders on Kite Connect
- **Position Management**: Track open positions, calculate P&L (realized & unrealized)
- **Risk Management**: 
  - Daily profit/loss limits
  - Dynamic position sizing based on risk
  - Stop-loss and target calculation
- **Notifications**: Email alerts for trades, positions, and critical alerts
- **Backtesting Framework**: Test strategies against historical data
- **Comprehensive Logging**: Track all bot activity for debugging and audit
- **Error Handling**: Robust exception handling throughout

## Project Structure

```
FNO_TradingBot/
├── src/
│   ├── main.py                 # Main bot orchestrator
│   ├── data_handler.py         # Real-time data acquisition
│   ├── strategy.py             # Technical analysis & signals
│   ├── order_manager.py        # Order execution via Kite Connect
│   ├── position_manager.py     # Position tracking & P&L
│   ├── risk_manager.py         # Risk limits & position sizing
│   ├── notification_manager.py # Email & alert notifications
│   ├── backtester.py           # Backtesting framework
│   ├── logger.py               # Logging setup
│   └── utils.py                # Utility functions
├── config/
│   └── settings.py             # Configuration & API credentials
├── tests/
│   └── test_strategy.py        # Unit tests
├── logs/
│   └── trading.log             # Bot activity logs
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Active Zerodha Kite Connect account with:
  - API Key
  - API Secret
  - Access Token (generated via login)

### Steps

1. **Clone or download the project**:
   ```bash
   cd FNO_TradingBot
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API credentials** (choose one method):

   **Method 1: Environment Variables**
   ```bash
   # Linux/Mac
   export KITE_API_KEY='your_api_key'
   export KITE_API_SECRET='your_api_secret'
   export KITE_ACCESS_TOKEN='your_access_token'
   
   # Windows (PowerShell)
   $env:KITE_API_KEY='your_api_key'
   $env:KITE_API_SECRET='your_api_secret'
   $env:KITE_ACCESS_TOKEN='your_access_token'
   ```

   **Method 2: .env File**
   ```bash
   # Create .env file in project root
   KITE_API_KEY=your_api_key
   KITE_API_SECRET=your_api_secret
   KITE_ACCESS_TOKEN=your_access_token
   ```

5. **Update trading parameters** in `config/settings.py`:
   ```python
   MAX_DAILY_PROFIT = 1000  # Target daily profit
   MAX_DAILY_LOSS = 500     # Maximum daily loss
   TRADING_SYMBOLS = ['BANKNIFTY', 'NIFTY']  # Symbols to trade
   ```

## Usage

### Run Paper Trading Simulation

```bash
python paper_trade.py
```

This replays a deterministic demo session by default and writes:
- `reports/paper_trading/paper_trading_report.html`
- `reports/paper_trading/paper_trading_report.json`
- `reports/paper_trading/paper_trades.csv`

You can also replay your own CSV:

```bash
python paper_trade.py --csv historical_data.csv --symbol BANKNIFTY
```

### Open the Frontend Dashboard

```bash
python serve_dashboard.py
```

Then open:

```text
http://127.0.0.1:8000/dashboard/
```

The dashboard loads the latest paper-trading report automatically and falls back to a demo view if the report is missing.

### Run Full Sanity Check

```bash
python sanity_check.py
```

This runs the test suite, replays paper trading, and verifies the report artifacts before you move toward a longer paper-testing cycle.

### Run the Trading Bot

```bash
python src/main.py
```

### Deploy on Render

This repo includes `render.yaml` for a quick Render web service setup.

1. Push the repo to GitHub.
2. Import it into Render.
3. Let Render detect `render.yaml`.
4. Use the generated web service URL to open the dashboard.

The service starts with:

```bash
python serve_dashboard.py
```

Render will set `PORT`, and the server listens on `0.0.0.0` for public access.

The bot will:
1. Initialize Kite Connect and all components
2. Monitor market prices for configured symbols
3. Generate trading signals based on technical indicators
4. Automatically place orders (BUY/SELL) with stop-loss and targets
5. Track positions and P&L in real-time
6. Stop when daily profit/loss limits are reached
7. Log all activities to `logs/trading.log`

### Run Unit Tests

```bash
python -m unittest tests/test_strategy.py
```

### Backtest a Strategy

```python
from src.backtester import Backtester
from src.strategy import Strategy
import pandas as pd

# Load historical data
data = pd.read_csv('historical_data.csv')

# Run backtest
backtest = Backtester(Strategy())
results = backtest.run_backtest(data)
backtest.print_results()
```

## Configuration

Edit `config/settings.py` to customize:

- **API Credentials**: KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN
- **Daily Limits**: MAX_DAILY_PROFIT, MAX_DAILY_LOSS
- **Trading Symbols**: TRADING_SYMBOLS (e.g., BANKNIFTY, NIFTY, FINNIFTY)
- **Log File**: LOG_FILE path

Edit `src/main.py` to customize:

- **Stop-Loss %**: stop_loss_percent (default: 2%)
- **Target %**: target_percent (default: 5%)
- **Data Update Interval**: time.sleep(5) - check interval in seconds

## Strategy Signals

The bot generates signals based on:

1. **Moving Average Crossover**: Short MA > Long MA = Buy, else Sell
2. **RSI**: RSI < 30 = Buy signal, RSI > 70 = Sell signal
3. **MACD**: MACD > Signal & Histogram > 0 = Buy, else Sell
4. **Bollinger Bands**: Price < Lower Band = Buy, Price > Upper Band = Sell

**Signal Logic**: A trade is triggered when ≥2 indicators align.

## Risk Management

- **Daily Profit Limit**: Bot stops when daily profit reaches ₹1000
- **Daily Loss Limit**: Bot stops when daily loss reaches -₹500
- **Dynamic Position Sizing**: Quantity calculated based on entry price, stop-loss, and 2% risk per trade
- **Stop-Loss Placement**: Automatic SL placed 2% below entry (long) / above entry (short)
- **Target Placement**: Automatic target placed 5% above entry (long) / below entry (short)

## Logging

All activities are logged to `logs/trading.log`:
- Bot initialization
- Data fetches
- Signal generation
- Order placements
- Position closures
- P&L updates
- Risk alerts
- Errors

View logs:
```bash
tail -f logs/trading.log
```

## Notifications

Configure email notifications in your code:

```python
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_app_password',  # Use app-specific password for Gmail
    'recipient_email': 'alert_recipient@gmail.com'
}

notification_manager = NotificationManager(email_config)
```

Notifications sent for:
- Order placements (BUY/SELL)
- Position closures (with P&L)
- Daily limit breaches
- Critical errors

## Performance Metrics (Backtesting)

- Total Trades
- Win Rate %
- Profit Factor
- Max Profit / Max Loss
- Total Return %
- Sharpe Ratio (risk-adjusted returns)

## Important Warnings ⚠️

1. **No Guaranteed Profit**: This bot does NOT guarantee profits. Markets are unpredictable.
2. **Risk Capital Only**: Trade only with capital you can afford to lose.
3. **Paper Trading First**: Test extensively on paper trading before live trading.
4. **Monitor Regularly**: Never run the bot unattended for extended periods.
5. **API Rate Limits**: Kite Connect has rate limits; adjust sleep intervals accordingly.
6. **Market Risks**: Gap risks, slippage, liquidity issues, and black swan events can occur.
7. **Regulatory Compliance**: Ensure you comply with all applicable trading regulations.

## Troubleshooting

### API Connection Error
```
Error: Connection refused
```
- Check internet connection
- Verify API credentials
- Ensure Kite Connect is accessible

### No Orders Placed
- Check if signals are generated: Review logs
- Verify market is open (NSE: 9:15 AM - 3:30 PM)
- Check position limits in Zerodha account

### High Slippage
- Increase target/SL values
- Use LIMIT orders instead of MARKET orders
- Trade liquid symbols (BANKNIFTY, NIFTY)

## Next Steps & Enhancements

- [ ] Implement WebSocket for real-time data streaming
- [ ] Add more technical indicators (Stochastic, ATR, Volume)
- [ ] ML-based signal generation (Random Forest, LSTM)
- [ ] Portfolio optimization & multi-symbol correlation
- [ ] Advanced order types (OCO, Bracket)
- [ ] Database storage for historical trades
- [ ] Web dashboard for monitoring
- [ ] Telegram bot integration for alerts

## Support & Resources

- [Kite Connect API Docs](https://kite.trade/)
- [Zerodha Community Forum](https://tradingqna.com/)
- [Technical Analysis Guides](https://www.investopedia.com/)

## Disclaimer

Trading in derivatives carries substantial risk. This bot is provided AS-IS for educational purposes. The developer assumes no responsibility for financial losses. Always do your own research and consult a financial advisor before trading.

---

**Happy Trading! 📈**
