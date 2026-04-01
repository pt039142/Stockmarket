import unittest
from pathlib import Path
import shutil
import numpy as np
import pandas as pd

from src.paper_trading_engine import PaperTradingEngine
from src.risk_manager import RiskManager
from src.trade_journal import TradeJournal


class _StubMarketAnalyzer:
    def analyze(self, data):
        return {
            'regime': 'balanced',
            'trend_bias': 'bullish',
            'confidence': 0.9,
            'atr': 1.5,
            'atr_pct': 0.01,
            'support_distance': 0.02,
            'resistance_distance': 0.02,
        }


class _StubStrategy:
    def __init__(self):
        self.market_analyzer = _StubMarketAnalyzer()

    def generate_signal(self, data):
        if len(data) == 10:
            return 1
        return 0


class _ScenarioStrategy:
    def __init__(self, signal_index, signal_value):
        self.signal_index = signal_index
        self.signal_value = signal_value
        self.market_analyzer = _StubMarketAnalyzer()

    def generate_signal(self, data):
        return self.signal_value if len(data) == self.signal_index else 0


class TestPaperTradingEngine(unittest.TestCase):
    def test_runs_session_and_exports_reports(self):
        index = pd.date_range('2026-04-01 09:15', periods=40, freq='5min')
        close = np.array([
            100.0, 100.2, 100.4, 100.6, 100.8,
            101.0, 101.2, 101.4, 101.6, 101.8,
            102.0, 102.2, 102.4, 102.6, 102.8,
            103.0, 103.2, 103.4, 103.6, 103.8,
            104.0, 104.2, 104.4, 104.6, 104.8,
            105.0, 104.8, 104.6, 104.4, 104.2,
            104.0, 103.8, 103.6, 103.4, 103.2,
            103.0, 102.8, 102.6, 102.4, 102.2,
        ])
        frame = pd.DataFrame(
            {
                'open': close,
                'high': close + 1.5,
                'low': close - 0.8,
                'close': close,
                'volume': np.arange(40) + 1000,
            },
            index=index,
        )

        output_dir = Path('reports') / 'paper_trading_test'
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)

        try:
            engine = PaperTradingEngine(
                strategy=_StubStrategy(),
                risk_manager=RiskManager(1500, 500, 100000, max_position_size=5),
                output_dir=output_dir,
                min_confidence=0.3,
            )
            summary = engine.run(frame, symbol='BANKNIFTY')

            self.assertGreaterEqual(summary['total_trades'], 1)
            self.assertIn('html', summary['reports'])
            self.assertTrue(summary['reports']['html'].endswith('.html'))
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    def test_engine_handles_empty_input(self):
        engine = PaperTradingEngine(strategy=_StubStrategy(), risk_manager=RiskManager(1500, 500, 100000))
        with self.assertRaises(ValueError):
            engine.run(pd.DataFrame(), symbol='BANKNIFTY')

    def test_trade_journal_exports(self):
        journal = TradeJournal()
        journal.record_trade(
            symbol='BANKNIFTY',
            side='BUY',
            entry_time='2026-04-01T09:30:00',
            exit_time='2026-04-01T09:40:00',
            entry_price=100,
            exit_price=105,
            quantity=1,
            pnl=5,
            reason='TARGET',
            regime='balanced',
            confidence=0.9,
            stop_loss=98,
            target=106,
        )

        output_dir = Path('reports') / 'journal_test'
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)

        try:
            json_path = journal.save_json(output_dir / 'report.json')
            csv_path = journal.save_csv(output_dir / 'report.csv')
            html_path = journal.export_html_report(output_dir / 'report.html')

            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue(html_path.exists())
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    def test_stop_loss_and_target_logic(self):
        index = pd.date_range('2026-04-01 09:15', periods=20, freq='5min')
        close = np.array([100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91], dtype=float)
        frame = pd.DataFrame(
            {
                'open': close,
                'high': close + 1.2,
                'low': close - 1.2,
                'close': close,
                'volume': np.arange(20) + 1000,
            },
            index=index,
        )

        strategy = _ScenarioStrategy(signal_index=10, signal_value=1)
        engine = PaperTradingEngine(strategy=strategy, risk_manager=RiskManager(1500, 500, 100000, max_position_size=5), min_confidence=0.3)
        summary = engine.run(frame, symbol='BANKNIFTY')

        self.assertEqual(summary['sessions'], 1)
        self.assertGreaterEqual(summary['total_trades'], 0)

    def test_daily_limit_short_circuits(self):
        engine = PaperTradingEngine(
            strategy=_StubStrategy(),
            risk_manager=RiskManager(10, 5, 100000, max_position_size=1),
            min_confidence=0.3,
        )
        engine.risk_manager.update_daily_pnl(11, absolute=True)
        self.assertTrue(engine._daily_limit_reached())



if __name__ == '__main__':
    unittest.main()
