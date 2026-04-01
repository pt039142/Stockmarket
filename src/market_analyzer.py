import numpy as np
import pandas as pd


class MarketAnalyzer:
    """Builds a compact market context from OHLCV data."""

    def __init__(self, atr_period=14, trend_period=20, volume_period=20):
        self.atr_period = atr_period
        self.trend_period = trend_period
        self.volume_period = volume_period

    def _atr(self, data):
        high_low = data["high"] - data["low"]
        high_close = (data["high"] - data["close"].shift()).abs()
        low_close = (data["low"] - data["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(self.atr_period).mean()

    def _adx_like(self, data):
        up_move = data["high"].diff()
        down_move = -data["low"].diff()

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        atr = self._atr(data)
        plus_di = 100 * pd.Series(plus_dm, index=data.index).rolling(self.trend_period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=data.index).rolling(self.trend_period).mean() / atr
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        return dx.rolling(self.trend_period).mean(), plus_di, minus_di

    def _slope(self, series, window=20):
        if len(series) < window:
            return 0.0
        values = series.tail(window).dropna().values
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return float(slope)

    def analyze(self, data):
        """Return a dictionary with regime, support/resistance, and confidence."""
        if data is None or len(data) < max(self.atr_period, self.trend_period, self.volume_period) + 5:
            return {
                "regime": "unknown",
                "trend_bias": "neutral",
                "confidence": 0.0,
                "supports": [],
                "resistances": [],
                "atr": None,
                "volume_ratio": None,
            }

        frame = data.copy().dropna(subset=["close", "high", "low"])
        if "volume" not in frame.columns:
            frame["volume"] = np.nan

        close = frame["close"]
        current_price = close.iloc[-1]
        atr = self._atr(frame).iloc[-1]
        adx, plus_di, minus_di = self._adx_like(frame)
        adx_val = adx.iloc[-1]
        plus_di_val = plus_di.iloc[-1]
        minus_di_val = minus_di.iloc[-1]
        volume_ma = frame["volume"].rolling(self.volume_period).mean().iloc[-1]
        volume_ratio = None
        if pd.notna(volume_ma) and volume_ma > 0 and pd.notna(frame["volume"].iloc[-1]):
            volume_ratio = float(frame["volume"].iloc[-1] / volume_ma)

        short_ma = close.rolling(5).mean().iloc[-1]
        long_ma = close.rolling(20).mean().iloc[-1]
        long_slope = self._slope(close.rolling(20).mean(), 20)
        price_slope = self._slope(close, 20)

        trend_score = 0.0
        if pd.notna(short_ma) and pd.notna(long_ma):
            trend_score += 1.0 if short_ma > long_ma else -1.0
        if price_slope > 0:
            trend_score += 0.5
        elif price_slope < 0:
            trend_score -= 0.5
        if long_slope > 0:
            trend_score += 0.5
        elif long_slope < 0:
            trend_score -= 0.5
        if pd.notna(adx_val):
            if adx_val >= 25:
                trend_score += 0.5 if plus_di_val > minus_di_val else -0.5
            elif adx_val < 15:
                trend_score *= 0.5

        atr_pct = float(atr / current_price) if pd.notna(atr) and current_price else None
        regime = "unknown"
        if pd.notna(adx_val) and atr_pct is not None:
            if adx_val >= 25 and atr_pct >= 0.004:
                regime = "trending"
            elif adx_val < 18 and atr_pct < 0.008:
                regime = "ranging"
            elif atr_pct >= 0.01:
                regime = "volatile"
            else:
                regime = "balanced"

        trend_bias = "neutral"
        if trend_score >= 1.0:
            trend_bias = "bullish"
        elif trend_score <= -1.0:
            trend_bias = "bearish"

        recent = frame.tail(max(self.trend_period, self.volume_period))
        support = float(recent["low"].min())
        resistance = float(recent["high"].max())
        support_distance = (current_price - support) / current_price if current_price else None
        resistance_distance = (resistance - current_price) / current_price if current_price else None

        confidence = 0.0
        confidence += min(abs(trend_score) / 3.0, 1.0) * 0.45
        if pd.notna(adx_val):
            confidence += min(adx_val / 50.0, 1.0) * 0.25
        if volume_ratio is not None:
            confidence += min(volume_ratio / 2.0, 1.0) * 0.15
        if atr_pct is not None:
            confidence += 0.15 if 0.002 <= atr_pct <= 0.02 else 0.0

        return {
            "regime": regime,
            "trend_bias": trend_bias,
            "confidence": round(float(confidence), 3),
            "trend_score": round(float(trend_score), 3),
            "adx": None if pd.isna(adx_val) else round(float(adx_val), 3),
            "atr": None if pd.isna(atr) else round(float(atr), 3),
            "atr_pct": None if atr_pct is None else round(float(atr_pct), 4),
            "volume_ratio": None if volume_ratio is None else round(float(volume_ratio), 3),
            "support": support,
            "resistance": resistance,
            "support_distance": None if support_distance is None else round(float(support_distance), 4),
            "resistance_distance": None if resistance_distance is None else round(float(resistance_distance), 4),
        }
