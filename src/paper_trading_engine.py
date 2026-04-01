from dataclasses import dataclass
from datetime import time as dt_time
from pathlib import Path

import pandas as pd

from config import settings
from src.logger import log_event
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.strategy import Strategy
from src.trade_journal import TradeJournal


@dataclass
class PaperTradeState:
    symbol: str = ''
    side: int = 0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    target: float = 0.0
    quantity: int = 0
    entry_time: object = None
    regime: str = 'unknown'
    confidence: float = 0.0


class PaperTradingEngine:
    """Replay historical candles and simulate a disciplined trading session."""

    def __init__(
        self,
        strategy=None,
        risk_manager=None,
        journal=None,
        output_dir='reports/paper_trading',
        market_open=dt_time(9, 15),
        market_close=dt_time(15, 30),
        min_confidence=0.35,
    ):
        self.strategy = strategy or Strategy(signal_strength_threshold=settings.SIGNAL_STRENGTH_THRESHOLD)
        self.risk_manager = risk_manager or RiskManager(
            settings.MAX_DAILY_PROFIT,
            settings.MAX_DAILY_LOSS,
            settings.INITIAL_CAPITAL,
            settings.RISK_PER_TRADE,
            settings.MAX_POSITION_SIZE,
        )
        self.journal = journal or TradeJournal()
        self.position_manager = PositionManager()
        self.output_dir = Path(output_dir)
        self.market_open = market_open
        self.market_close = market_close
        self.min_confidence = min_confidence
        self.state = PaperTradeState()
        self.trades_today = 0

    def run(self, data, symbol='BANKNIFTY'):
        """Run the replay on a single symbol dataframe."""
        frame = self._prepare_frame(data)
        if frame.empty:
            raise ValueError('PaperTradingEngine requires non-empty OHLC data with datetime index')

        self.output_dir.mkdir(parents=True, exist_ok=True)
        equity_start = self.risk_manager.current_capital
        session_summaries = []

        for session_date, session_df in frame.groupby(frame.index.date):
            self._reset_session(equity_start)
            session_summary = self._run_session(symbol, session_df)
            session_summary['session_date'] = str(session_date)
            session_summaries.append(session_summary)
            equity_start = self.risk_manager.current_capital

        summary = self.journal.summary()
        summary['sessions'] = len(session_summaries)
        summary['ending_capital'] = round(self.risk_manager.current_capital, 2)
        summary['session_summaries'] = session_summaries

        report_paths = self._export_reports()
        summary['reports'] = {k: str(v) for k, v in report_paths.items()}

        log_event(f'Paper trading completed: {summary}')
        return summary

    def _prepare_frame(self, data):
        frame = data.copy()
        if not isinstance(frame.index, pd.DatetimeIndex):
            if 'date' in frame.columns:
                frame['date'] = pd.to_datetime(frame['date'])
                frame = frame.set_index('date')
            else:
                raise ValueError('Historical data must contain a datetime index or date column')

        frame = frame.sort_index()
        required = {'close', 'high', 'low'}
        if not required.issubset(frame.columns):
            raise ValueError(f'Missing required columns: {required - set(frame.columns)}')

        if 'volume' not in frame.columns:
            frame['volume'] = 0

        return frame.dropna(subset=['close', 'high', 'low']).copy()

    def _reset_session(self, starting_capital):
        self.risk_manager.reset_daily_state(starting_capital=starting_capital)
        self.position_manager.positions.clear()
        self.position_manager.closed_positions = []
        self.position_manager.daily_pnl = 0
        self.state = PaperTradeState()
        self.trades_today = 0
        self.journal.record_event('session_start', 'New paper trading session started', starting_capital=starting_capital)

    def _run_session(self, symbol, session_df):
        for idx in range(1, len(session_df)):
            candle = session_df.iloc[idx]
            candle_time = session_df.index[idx]

            if not self._within_market_hours(candle_time.time()):
                continue

            window = session_df.iloc[: idx + 1]
            market_context = self.strategy.market_analyzer.analyze(window)

            if self._daily_limit_reached():
                self._close_open_position(candle_time, candle['close'], 'DAILY_LIMIT')
                break

            if self.state.side != 0:
                if self._check_exit(candle, candle_time):
                    if self._daily_limit_reached():
                        break
                    continue
                continue

            signal = self.strategy.generate_signal(window)
            if signal == 0:
                continue

            if market_context.get('confidence', 0) < self.min_confidence:
                continue

            self._open_position(symbol, candle, candle_time, signal, market_context)

        if self.state.side != 0:
            last_candle = session_df.iloc[-1]
            last_time = session_df.index[-1]
            self._close_open_position(last_time, last_candle['close'], 'EOD_EXIT')

        session_summary = self._session_summary(symbol, session_df)
        self.journal.record_event('session_end', 'Paper trading session ended', **session_summary)
        return session_summary

    def _within_market_hours(self, session_time):
        return self.market_open <= session_time <= self.market_close

    def _open_position(self, symbol, candle, candle_time, signal, market_context):
        entry_price = float(candle['close'])
        atr = market_context.get('atr') or max(entry_price * 0.0025, 1.0)
        regime = market_context.get('regime', 'unknown')
        confidence = float(market_context.get('confidence', 0.0))

        base_stop = max(entry_price * settings.STOP_LOSS_PERCENT, atr * 1.25)
        reward_multiple = 1.5 if regime == 'ranging' else 2.0 if regime == 'balanced' else 2.5

        if signal == 1:
            stop_loss = entry_price - base_stop
            target = entry_price + base_stop * reward_multiple
        else:
            stop_loss = entry_price + base_stop
            target = entry_price - base_stop * reward_multiple

        quantity = self.risk_manager.calculate_position_size(entry_price, stop_loss)
        if quantity <= 0:
            return

        opened = self.position_manager.open_position(symbol, entry_price, quantity, signal)
        if not opened:
            return

        self.state = PaperTradeState(
            symbol=symbol,
            side=signal,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            quantity=quantity,
            entry_time=candle_time,
            regime=regime,
            confidence=confidence,
        )
        self.trades_today += 1
        self.journal.record_event(
            'entry',
            'Paper trade opened',
            symbol=symbol,
            side='BUY' if signal == 1 else 'SELL',
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            quantity=quantity,
            regime=regime,
            confidence=confidence,
            entry_time=candle_time.isoformat(),
        )
        log_event(f'Paper entry opened: {symbol} @ {entry_price} qty={quantity}')

    def _check_exit(self, candle, candle_time):
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])

        if self.state.side == 1:
            stop_hit = low <= self.state.stop_loss
            target_hit = high >= self.state.target

            if stop_hit and target_hit:
                return self._close_open_position(candle_time, self.state.stop_loss, 'STOP_AND_TARGET_SAME_BAR')
            if stop_hit:
                return self._close_open_position(candle_time, self.state.stop_loss, 'STOP_LOSS')
            if target_hit:
                return self._close_open_position(candle_time, self.state.target, 'TARGET')

            unrealized = self.position_manager.calculate_unrealized_pnl(self.state.symbol, close)
            if unrealized is not None and unrealized <= -abs(self.state.entry_price - self.state.stop_loss) * self.state.quantity:
                return self._close_open_position(candle_time, close, 'HARD_STOP')

        elif self.state.side == -1:
            stop_hit = high >= self.state.stop_loss
            target_hit = low <= self.state.target

            if stop_hit and target_hit:
                return self._close_open_position(candle_time, self.state.stop_loss, 'STOP_AND_TARGET_SAME_BAR')
            if stop_hit:
                return self._close_open_position(candle_time, self.state.stop_loss, 'STOP_LOSS')
            if target_hit:
                return self._close_open_position(candle_time, self.state.target, 'TARGET')

            unrealized = self.position_manager.calculate_unrealized_pnl(self.state.symbol, close)
            if unrealized is not None and unrealized <= -abs(self.state.entry_price - self.state.stop_loss) * self.state.quantity:
                return self._close_open_position(candle_time, close, 'HARD_STOP')

        return False

    def _close_open_position(self, candle_time, exit_price, reason):
        if self.state.side == 0 or not self.state.symbol:
            return False

        pnl = self.position_manager.close_position(self.state.symbol, exit_price)
        self.risk_manager.update_daily_pnl(pnl)
        self.journal.record_trade(
            symbol=self.state.symbol,
            side='BUY' if self.state.side == 1 else 'SELL',
            entry_time=self.state.entry_time,
            exit_time=candle_time,
            entry_price=self.state.entry_price,
            exit_price=exit_price,
            quantity=self.state.quantity,
            pnl=pnl,
            reason=reason,
            regime=self.state.regime,
            confidence=self.state.confidence,
            stop_loss=self.state.stop_loss,
            target=self.state.target,
        )
        self.journal.record_event(
            'exit',
            f'Paper trade closed: {reason}',
            symbol=self.state.symbol,
            exit_price=exit_price,
            pnl=pnl,
            reason=reason,
        )
        log_event(f'Paper exit closed: {self.state.symbol} reason={reason} pnl={pnl:.2f}')
        self.state = PaperTradeState()
        return True

    def _daily_limit_reached(self):
        metrics = self.risk_manager.get_risk_metrics()
        return metrics['profit_target_reached'] or metrics['loss_limit_hit']

    def _session_summary(self, symbol, session_df):
        metrics = self.risk_manager.get_risk_metrics()
        return {
            'symbol': symbol,
            'candles_processed': len(session_df),
            'trades_today': self.trades_today,
            'daily_pnl': metrics['daily_pnl'],
            'current_capital': metrics['current_capital'],
            'profit_target_reached': metrics['profit_target_reached'],
            'loss_limit_hit': metrics['loss_limit_hit'],
        }

    def _export_reports(self):
        json_path = self.output_dir / 'paper_trading_report.json'
        csv_path = self.output_dir / 'paper_trades.csv'
        html_path = self.output_dir / 'paper_trading_report.html'

        self.journal.save_json(json_path)
        self.journal.save_csv(csv_path)
        self.journal.export_html_report(html_path)

        return {
            'json': json_path,
            'csv': csv_path,
            'html': html_path,
        }
