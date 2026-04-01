# Production Deployment Guide - F&O Trading Bot

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Create `.env` file from `.env.example`
- [ ] Set all Zerodha API credentials in environment variables
- [ ] Configure Gmail app password for email alerts
- [ ] Test email configuration

### 2. Configuration Review
- [ ] Review `config/settings.py` for your risk parameters
- [ ] Set appropriate daily profit/loss limits
- [ ] Configure trading symbols and quantities
- [ ] Set market hours for your timezone

### 3. Code Validation
- [ ] Run tests: `pytest tests/test_strategy.py`
- [ ] Verify API connections: `python test_api.py`
- [ ] Run bot in paper trading mode first

### 4. Paper Trading Phase (CRITICAL)
- [ ] Trade in paper mode for at least 1 week
- [ ] Verify all signals generate correctly
- [ ] Test all risk management limits
- [ ] Verify email notifications work
- [ ] Check position sizing calculations
- [ ] Monitor logs for any errors

### 5. Live Trading Preparation
- [ ] Have sufficient capital (recommended ₹100,000+)
- [ ] Understand your risk parameters completely
- [ ] Have a backup internet connection
- [ ] Monitor bot closely first day

## 🔧 Setup Instructions

### Step 1: Create Environment File
```bash
cp config/.env.example config/.env
```

Edit `config/.env`:
```
KITE_API_KEY=your_key
KITE_API_SECRET=your_secret
KITE_ACCESS_TOKEN=your_token
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=alert@youraddress.com
PAPER_TRADING=True  # Start with paper trading!
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Test Zerodha Connection
```bash
python test_api.py
```

### Step 4: Run in Paper Trading Mode
```bash
python run_demo.py
```

### Step 5: Monitor Logs
```bash
tail -f logs/trading.log
```

## 📊 Production Settings

### Risk Parameters (Adjust based on your capital)
```
Initial Capital: ₹100,000
Daily Profit Target: ₹5,000
Daily Loss Limit: ₹2,000
Risk per Trade: 2% of capital
Stop Loss: 2% per position
Target: 5% per position
```

### Trading Hours
- Market Open: 09:15 IST
- Market Close: 15:30 IST
- Trading Days: Monday-Friday

## ⚠️ Critical Production Safety Features

### 1. Session Validation
- Bot validates Zerodha session every hour
- Exits gracefully if session expires
- Notifies you via email

### 2. Circuit Breaker
- Stops after 5 consecutive API failures
- Prevents cascading errors
- Closes all positions on shutdown

### 3. Order Confirmation
- All orders verified after placement
- Retries with exponential backoff (1s→2s→4s)
- Logs all order confirmations

### 4. Data Validation
- Rejects invalid/null prices
- Validates OHLC relationships
- Checks market hours before trading

### 5. Graceful Shutdown
- Ctrl+C safely closes all positions
- Generates final P&L report
- Cleanup on any error

## 🚀 Running the Bot

### Paper Trading (Recommended First)
```bash
export PAPER_TRADING=True
python src/main.py
```

### Live Trading (After extensive testing)
```bash
export PAPER_TRADING=False
python src/main.py
```

## 📝 Monitoring

### Check Bot Status
```bash
tail -f logs/trading.log
```

### Watch for Critical Alerts
- `[ERROR]` - Critical errors
- `[ALERT]` - Limit breaches
- `[TRADE]` - Order executions
- `[CLOSE]` - Position closures

### Email Alerts
You'll receive emails for:
- Trade entries/exits
- Position P&L
- Daily limits reached
- Errors or API failures

## 🛑 Emergency Stop
Press `Ctrl+C` to gracefully shutdown:
1. Closes all open positions
2. Cancels pending SL/Target orders
3. Generates final report
4. Exits cleanly

## 📞 Troubleshooting

### Bot won't start
```
[ERROR] Missing Zerodha credentials
→ Check .env file and environment variables
```

### Orders not placed
```
[ERROR] Circuit breaker triggered: 5 consecutive errors
→ Check internet connection
→ Check Zerodha API status
→ Restart bot
```

### Wrong signals
```
→ Check historical data in logs
→ Verify strategy.py logic
→ Test with more historical data
```

### Bot closes positions unexpectedly
```
→ Check daily loss limit not hit
→ Verify risk_manager.py settings
→ Check logs for explicit stop triggers
```

## 📈 Performance Tracking

All trades are logged in `logs/trading.log`:
```
Entry time    | Symbol    | Entry Price | Stop Loss | Target | Qty
Exit time     | Symbol    | Exit Price  | P&L      | Status
```

Generate daily report:
```bash
grep "Position CLOSED" logs/trading.log | tail -20
```

## 🔐 Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Use app-specific passwords** for email (not main password)
3. **Limit bot internet access** - Use firewall rules
4. **Monitor regularly** - Check logs daily
5. **Backup logs** - Archive logs regularly
6. **Update Zerodha API** - Keep kiteconnect updated

## ✨ Next Steps

1. ✅ Deploy to paper trading
2. ✅ Monitor for 1 week
3. ✅ Verify all features work
4. ✅ Adjust risk parameters as needed
5. ✅ Switch to live trading carefully
6. ✅ Monitor first live day closely

## 📞 Support

For issues:
1. Check `logs/trading.log` for errors
2. Run `test_api.py` to verify API connection
3. Review `config/settings.py` for configuration
4. Check email configuration

Good luck! 🎯

