# Trading Bot Configuration - PRODUCTION READY
import os

# ==================== API CREDENTIALS ====================
# Load from environment variables for security
KITE_API_KEY = os.getenv('KITE_API_KEY', '')
KITE_API_SECRET = os.getenv('KITE_API_SECRET', '')
KITE_ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN', '')

if not all([KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN]):
    print('[ERROR] Missing Zerodha credentials in environment variables')
    print('[HELP] Set: KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN')

# ==================== PRODUCT IDENTITY ====================
APP_NAME = 'PrinceStockExhange'

# ==================== RISK MANAGEMENT ====================
# WARNING: These are guardrails, not profit guarantees.
MAX_DAILY_PROFIT = 1500  # Stop trading after ₹1500 profit
MAX_DAILY_LOSS = 500     # Stop trading after ₹500 loss
INITIAL_CAPITAL = 100000  # Initial trading capital

# Position sizing limits
STOP_LOSS_PERCENT = 0.02  # 2% stop loss per position
TARGET_PERCENT = 0.05     # 5% target per position
RISK_PER_TRADE = 0.02     # Risk 2% of capital per trade
MAX_POSITION_SIZE = 5     # Max quantity per order
MAX_CONCURRENT_POSITIONS = 3  # Max open positions at once
MAX_TRADES_PER_DAY = 6    # Hard cap on number of entries per day

# ==================== TRADING PARAMETERS ====================
TRADING_SYMBOLS = ['BANKNIFTY', 'NIFTY']
ORDER_QUANTITY = 1

# Data and strategy parameters
DATA_CHECK_INTERVAL = 5   # Check market every 5 seconds
HISTORICAL_DATA_DAYS = 30 # Use 30 days for signal generation
SIGNAL_STRENGTH_THRESHOLD = 2  # Min 2 indicators for signal

# ==================== MARKET HOURS ====================
# IST timezone (Mumbai)
MARKET_OPEN = '09:15'
MARKET_CLOSE = '15:30'
TRADING_DAYS = [0, 1, 2, 3, 4]  # Mon-Fri (0-4)

# ==================== EMAIL NOTIFICATIONS ====================
# For live trading alerts
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'sender_email': os.getenv('SENDER_EMAIL', ''),
    'sender_password': os.getenv('SENDER_PASSWORD', ''),  # Use app-specific password for Gmail
    'recipient_email': os.getenv('RECIPIENT_EMAIL', ''),
}

# ==================== LOGGING ====================
LOG_FILE = '../logs/trading.log'
LOG_LEVEL = 'INFO'

# ==================== API RETRY CONFIGURATION ====================
MAX_API_RETRIES = 3
INITIAL_BACKOFF = 1  # seconds
MAX_BACKOFF = 30    # seconds
BACKOFF_MULTIPLIER = 2

# ==================== CIRCUIT BREAKER ====================
MAX_CONSECUTIVE_ERRORS = 5  # Stop after 5 consecutive API failures

# ==================== PAPER TRADING MODE ====================
# Set to True for testing, False for live trading
PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'

if PAPER_TRADING:
    print('[INFO] PAPER TRADING MODE ENABLED - No real orders will be placed')
else:
    print('[WARNING] LIVE TRADING MODE - Real money at risk!')
