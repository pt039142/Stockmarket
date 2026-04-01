# Trading Strategy Guide

## Strategy Overview

The F&O Trading Bot uses a **multi-indicator confirmation strategy** that generates signals based on 4 technical indicators working together:

1. **Moving Average Crossover** (Trend identification)
2. **RSI** (Momentum/Overbought-Oversold)
3. **MACD** (Trend confirmation)
4. **Bollinger Bands** (Support/Resistance)

A trade is triggered only when **2 or more indicators align**, reducing false signals.

---

## Indicators Explained

### 1. Moving Average Crossover

**What it does**: Identifies trend direction

**Logic**:
- If Short MA (5-period) > Long MA (20-period) → **BULLISH**
- If Short MA < Long MA → **BEARISH**

**Example**:
```
Price Chart:
─────────────────────
      S M (5)
───────────────── 
      L M (20)
     
When S > L = Buy signal (uptrend)
When S < L = Sell signal (downtrend)
```

---

### 2. RSI (Relative Strength Index)

**What it does**: Measures momentum and overbought/oversold conditions

**Values**:
- RSI < 30: **Oversold** (Buy signal) 📉
- 30-70: Neutral range
- RSI > 70: **Overbought** (Sell signal) 📈

**Example**:
```
RSI over time:
100 |─────────────┐
 70 |─────────────┤ Overbought (Sell)
    |    ╱╲      │
 50 |───╱  ╲─────┤ Neutral
    |      │      │
 30 |──────┘─────┤ Oversold (Buy)
  0 |             │
```

---

### 3. MACD (Moving Average Convergence Divergence)

**What it does**: Shows momentum and trend changes

**Components**:
- **MACD Line**: Fast EMA (12) - Slow EMA (26)
- **Signal Line**: 9-period EMA of MACD
- **Histogram**: MACD - Signal (momentum strength)

**Logic**:
- MACD > Signal & Histogram > 0: **BULLISH** 📈
- MACD < Signal & Histogram < 0: **BEARISH** 📉

**Example**:
```
     MACD Line ───────
     Signal ──────────
     Histogram (bars) ▇▇▇

When MACD crosses above Signal = Buy
When MACD crosses below Signal = Sell
```

---

### 4. Bollinger Bands

**What it does**: Identifies support/resistance and volatility

**Components**:
- Upper Band: SMA(20) + 2×StdDev
- Middle Band: SMA(20)
- Lower Band: SMA(20) - 2×StdDev

**Logic**:
- Price < Lower Band: **Oversold** (Buy) 📉
- Price > Upper Band: **Overbought** (Sell) 📈
- Price touches bands: Mean reversion play

**Example**:
```
     Upper Band ═══════════════
     Price ═══════╲           
     Middle ───────╲─────────
     Price ────────╱╲
     Lower Band ═══╱═══════════

Price bounces off bands - reversal zone
```

---

## Signal Generation Logic

### Buy Signal (LONG)
**Triggered when ≥2 indicators align for upside:**
- ✓ Short MA > Long MA (uptrend)
- ✓ RSI < 30 (oversold)
- ✓ MACD > Signal (bullish crossover)
- ✓ Price < Lower Bollinger Band (bouncing up)

### Sell Signal (SHORT)
**Triggered when ≥2 indicators align for downside:**
- ✓ Short MA < Long MA (downtrend)
- ✓ RSI > 70 (overbought)
- ✓ MACD < Signal (bearish crossover)
- ✓ Price > Upper Bollinger Band (reversing down)

### No Signal (HOLD)
- Only 1 indicator aligned: Not enough confirmation
- Mixed signals: Conflicting indicators
- Value = 0 → Hold position

---

## Trading Rules

### Entry Rules
1. **Wait for signal**: ≥2 indicators align
2. **Confirm trend**: Price direction matches signal
3. **Position sizing**: Based on risk (2% of capital)
4. **Stop loss**: 2% below entry (long) / 2% above entry (short)
5. **Target**: 5% above entry (long) / 5% below entry (short)

### Exit Rules
1. **Target reached**: Sell at target price automatically
2. **Stop loss hit**: Sell at SL automatically
3. **Counter signal**: Opposite signal generated (exit & reverse)
4. **Manual exit**: Force close if needed
5. **Time exit**: Close after 5 bars if no clear direction

### Position Management
- **Max 1 position per symbol**
- **Position size**: Calculated based on risk
- **Daily profit limit**: Stop when ₹1000 profit reached
- **Daily loss limit**: Stop when -₹500 loss reached

---

## Example Trade Scenario

### BANKNIFTY Buy Trade

**Setup** (9:30 AM):
```
Current Price: 50,000
Short MA (5): 50,050 ✓ > Long MA (20): 49,900
RSI: 25 ✓ (Oversold)
MACD: Positive histogram ✓
Price: Below lower BB ✓

Signal Count: 3 ≥ 2 → BUY ✓
```

**Order Placement**:
```
Entry: 50,000
Stop Loss: 50,000 × (1 - 0.02) = 49,000
Target: 50,000 × (1 + 0.05) = 52,500
Quantity: Based on risk (e.g., 1 lot)
```

**Position Monitoring** (9:45 AM):
```
Current: 50,500 → P&L = +500 ✓ (No action)
```

**Exit** (10:00 AM):
```
Target hit: Price reaches 52,500
Position closed: +2,500 profit ✓
```

---

## Customizing the Strategy

### 1. Change Indicator Periods

Edit `src/strategy.py`:
```python
class Strategy:
    def __init__(self):
        self.rsi_period = 14      # Change to 7 or 21
        self.macd_fast = 12       # Change to 9
        self.macd_slow = 26       # Change to 30
```

### 2. Adjust Entry Thresholds

```python
# Modify signal counting logic
if signal_count >= 3:  # Require 3 instead of 2
    return 1  # Buy
```

### 3. Change Stop Loss & Target

Edit `src/main.py`:
```python
self.stop_loss_percent = 0.03   # 3% instead of 2%
self.target_percent = 0.10      # 10% instead of 5%
```

### 4. Add More Indicators

Example: Add Stochastic oscillator
```python
def calculate_stochastic(self, data, period=14):
    """Calculate Stochastic indicator"""
    low = data['low'].rolling(window=period).min()
    high = data['high'].rolling(window=period).max()
    k = 100 * ((data['close'] - low) / (high - low))
    return k

# Add to signal generation
if stoch_k > 80:
    signal_count -= 1  # Overbought
elif stoch_k < 20:
    signal_count += 1  # Oversold
```

---

## Backtesting Your Strategy

### Run Backtest

```python
from src.backtester import Backtester
from src.strategy import Strategy
import pandas as pd

# Load historical data
data = pd.read_csv('BANKNIFTY_2024_data.csv')

# Run backtest
backtester = Backtester(Strategy(), initial_capital=100000)
results = backtester.run_backtest(data, entry_quantity=1)
backtester.print_results()
```

### Interpret Results

```
==================================================
BACKTEST RESULTS
==================================================
total_trades: 25
winning_trades: 17
losing_trades: 8
win_rate: 68.00              ← Good win rate
total_pnl: 15000.00          ← Net profit
avg_pnl: 600.00              ← Average per trade
max_profit: 2500.00          ← Biggest win
max_loss: -800.00            ← Biggest loss
profit_factor: 2.35          ← Wins/Losses ratio (>2 is good)
final_capital: 115000.00
total_return: 15.00%         ← Return %
==================================================
```

**Good Metrics** (to optimize towards):
- Win Rate > 55%
- Profit Factor > 1.5
- Avg Win > Avg Loss
- Drawdown < 20%

---

## Risk Management Rules

### Daily Limits
- **Max Profit**: ₹1000 → Bot stops
- **Max Loss**: -₹500 → Bot stops
- **Reason**: Emotion control, prevent overtrading

### Position Sizing
- **Risk per trade**: 2% of capital
- **Calculation**: (Capital × 0.02) / (Entry - SL)
- **Example**: (100,000 × 0.02) / (50,000 - 49,000) = **2 lots** wait actually, let me think again...
  - Risk amount = 100,000 × 0.02 = ₹2,000
  - Price difference = 50,000 - 49,000 = ₹1,000
  - Quantity = 2,000 / 1,000 = **2 lots**

### Stop Loss Placement
- **Always mandatory** for every trade
- **Conservative**: 2% loss acceptable
- **Tight SL**: May exit on noise (false stops)
- **Wide SL**: Risk more, less likely hit

---

## Trading Psychology Tips

1. **Follow the rules**: Never override bot signals
2. **Avoid overtrading**: Let daily limits prevent burnout
3. **Trust the backtest**: If backtested well, trust the strategy
4. **Monitor, don't interference**: Bot needs autonomy
5. **Review regularly**: Analyze trades weekly
6. **Track emotions**: Note how you feel during losses
7. **Accept losses**: Not every trade will win
8. **Celebrate wins**: But stay humble and disciplined

---

## Common Mistakes to Avoid

❌ **Change strategy mid-day** → Stick to one strategy per day
❌ **Override stop loss** → Increases losses
❌ **Trade with emotions** → Use logical rules
❌ **Risk too much per trade** → Stick to 2% risk rule
❌ **Ignore daily limits** → Prevents overtrading
❌ **No backtesting** → Always backtest first
❌ **Switch strategies constantly** → Give each time to work
❌ **Trade when tired** → Rest when needed

---

## Performance Monitoring

### Weekly Review Checklist

- [ ] Total trades executed?
- [ ] Win rate % (target > 55%)?
- [ ] Average profit per trade?
- [ ] Biggest loss taken?
- [ ] Daily limits hit how many days?
- [ ] Any unusual slippage?
- [ ] Any system errors?

### Metrics to Track

```python
metrics = {
    'total_days_traded': 5,
    'total_trades': 12,
    'wins': 8,
    'losses': 4,
    'win_rate': 66.67,
    'total_pnl': 6000,
    'profit_per_day': 1200,
    'max_drawdown': -500,
    'sharpe_ratio': 1.8
}
```

---

## Next Strategy Ideas

1. **Mean Reversion**: Trade bounces from support/resistance
2. **Trend Following**: Buy dips in uptrend, sell rallies in downtrend
3. **Volatility Breakout**: Trade breakouts from consolidation
4. **Machine Learning**: Use LSTM/Random Forest for signals
5. **Multi-timeframe**: Combine 5-min, 15-min, 1-hour signals
6. **Sector Rotation**: Trade sector-specific instruments

---

Remember: **The best strategy is the one you can execute consistently!**
