# Example configuration file - Copy to config/settings.py and fill in your values

# ===================== API CREDENTIALS =====================
# Load securely from environment variables
# Never hardcode credentials in this file

import os

KITE_API_KEY = os.getenv('KITE_API_KEY', '')
KITE_API_SECRET = os.getenv('KITE_API_SECRET', '')
KITE_ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN', '')

# ===================== TRADING PARAMETERS =====================
# Daily profit/loss limits
MAX_DAILY_PROFIT = 1000      # Stop trading when profit reaches ₹1000
MAX_DAILY_LOSS = 500         # Stop trading when loss reaches -₹500

# Trading symbols (NSE)
TRADING_SYMBOLS = ['BANKNIFTY', 'NIFTY']

# Order quantity per trade
ORDER_QUANTITY = 1

# ===================== LOGGING =====================
LOG_FILE = '../logs/trading.log'

# ===================== STRATEGY PARAMETERS =====================
# Risk management
RISK_PER_TRADE = 0.02        # 2% of capital at risk per trade
STOP_LOSS_PERCENT = 0.02     # 2% stop loss
TARGET_PERCENT = 0.05        # 5% target

# Technical indicators
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ===================== EMAIL NOTIFICATIONS =====================
# Optional: Enable email alerts
EMAIL_CONFIG = {
    'enabled': False,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_app_password',  # Use app-specific password for Gmail
    'recipient_email': 'alert_recipient@gmail.com'
}

# ===================== MARKET HOURS =====================
MARKET_OPEN = '09:15'
MARKET_CLOSE = '15:30'
PRE_OPEN = '09:00'

# ===================== DATA FETCH INTERVAL =====================
# Time in seconds between data checks
DATA_CHECK_INTERVAL = 5

# ===================== BACKTESTING =====================
BACKTEST_INITIAL_CAPITAL = 100000
BACKTEST_DATA_FILE = 'historical_data.csv'
BACKTEST_START_DATE = '2024-01-01'
BACKTEST_END_DATE = '2024-03-31'
