import pandas as pd
import numpy as np
from src.logger import log_event
from src.market_analyzer import MarketAnalyzer

class Strategy:
    """Advanced trading strategy with multiple technical indicators."""
    
    def __init__(self, signal_strength_threshold=2, min_candles=50):
        log_event('Strategy initialized')
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.signal_strength_threshold = signal_strength_threshold
        self.min_candles = min_candles
        self.market_analyzer = MarketAnalyzer()
    
    def calculate_rsi(self, data, period=14):
        """Calculate Relative Strength Index."""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data):
        """Calculate MACD (Moving Average Convergence Divergence)."""
        exp1 = data['close'].ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = data['close'].ewm(span=self.macd_slow, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def calculate_bollinger_bands(self, data, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return sma, upper_band, lower_band
    
    def calculate_moving_averages(self, data, short=5, long=20):
        """Calculate simple moving averages."""
        short_ma = data['close'].rolling(window=short).mean()
        long_ma = data['close'].rolling(window=long).mean()
        return short_ma, long_ma

    def _has_valid_market_data(self, data):
        """Validate that the input data is usable for signal generation."""
        required_cols = {'close', 'high', 'low'}
        if not required_cols.issubset(set(data.columns)):
            return False

        if len(data) < self.min_candles:
            return False

        latest = data[['close', 'high', 'low']].tail(self.min_candles)
        return not latest.isna().any().any()
    
    def generate_signal(self, data):
        """Generate trading signal based on multiple indicators."""
        if not self._has_valid_market_data(data):
            return 0  # Not enough data
        
        try:
            data = data.copy()
            data = data.dropna(subset=['close', 'high', 'low'])
            if len(data) < self.min_candles:
                return 0

            # Calculate indicators
            short_ma, long_ma = self.calculate_moving_averages(data)
            rsi = self.calculate_rsi(data)
            macd, signal, histogram = self.calculate_macd(data)
            sma, upper_bb, lower_bb = self.calculate_bollinger_bands(data)
            market_context = self.market_analyzer.analyze(data)
            
            # Get latest values
            current_price = data['close'].iloc[-1]
            previous_price = data['close'].iloc[-2]
            rsi_val = rsi.iloc[-1]
            previous_rsi = rsi.iloc[-2]
            macd_val = macd.iloc[-1]
            signal_val = signal.iloc[-1]
            hist_val = histogram.iloc[-1]
            short_ma_val = short_ma.iloc[-1]
            long_ma_val = long_ma.iloc[-1]
            short_ma_prev = short_ma.iloc[-2]
            long_ma_prev = long_ma.iloc[-2]
            up_bb = upper_bb.iloc[-1]
            low_bb = lower_bb.iloc[-1]
            bb_mid = sma.iloc[-1]
            atr = (data['high'] - data['low']).rolling(window=14).mean().iloc[-1]
            
            if pd.isna(short_ma_val) or pd.isna(long_ma_val) or pd.isna(rsi_val) or pd.isna(macd_val):
                return 0

            if pd.isna(up_bb) or pd.isna(low_bb) or pd.isna(bb_mid) or pd.isna(atr):
                return 0

            if market_context["confidence"] < 0.35:
                return 0

            signal_score = 0

            # MA crossover signal
            if short_ma_val > long_ma_val:
                signal_score += 1
            else:
                signal_score -= 1

            # Trend confirmation: reward fresh cross in the same direction
            if short_ma_val > long_ma_val and short_ma_prev <= long_ma_prev:
                signal_score += 1
            elif short_ma_val < long_ma_val and short_ma_prev >= long_ma_prev:
                signal_score -= 1
            
            # RSI signal (oversold/overbought)
            if rsi_val < 30:
                signal_score += 1  # Oversold, buy signal
            elif rsi_val > 70:
                signal_score -= 1  # Overbought, sell signal

            # RSI momentum confirmation
            if rsi_val > previous_rsi and current_price > previous_price:
                signal_score += 1
            elif rsi_val < previous_rsi and current_price < previous_price:
                signal_score -= 1
            
            # MACD signal
            if macd_val > signal_val and hist_val > 0:
                signal_score += 1  # Bullish
            elif macd_val < signal_val and hist_val < 0:
                signal_score -= 1  # Bearish
            
            # Bollinger Bands signal
            if current_price < low_bb:
                signal_score += 1  # Price below lower band, buy
            elif current_price > up_bb:
                signal_score -= 1  # Price above upper band, sell

            # Mean reversion guard: prefer longs below the mid-band only if momentum is improving
            if current_price > bb_mid and short_ma_val > long_ma_val:
                signal_score += 1
            elif current_price < bb_mid and short_ma_val < long_ma_val:
                signal_score -= 1
            
            # Volatility guard: avoid extremely thin/noisy candles
            if atr <= 0 or (current_price / atr) > 1000:
                return 0

            # Market regime filter
            if market_context["regime"] == "volatile":
                signal_score *= 0.5
            elif market_context["regime"] == "ranging":
                if abs(signal_score) < self.signal_strength_threshold + 1:
                    return 0

            # Align with broader market context
            if market_context["trend_bias"] == "bullish":
                signal_score += 1 if signal_score > 0 else 0
            elif market_context["trend_bias"] == "bearish":
                signal_score -= 1 if signal_score < 0 else 0

            if market_context["support_distance"] is not None and market_context["support_distance"] < 0.004:
                signal_score += 1
            if market_context["resistance_distance"] is not None and market_context["resistance_distance"] < 0.004:
                signal_score -= 1
            
            # Determine final signal
            if signal_score >= self.signal_strength_threshold:
                return 1  # Buy
            elif signal_score <= -self.signal_strength_threshold:
                return -1  # Sell
            else:
                return 0  # Hold
        
        except Exception as e:
            log_event(f'Error in signal generation: {str(e)}')
            return 0
