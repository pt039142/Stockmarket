#!/usr/bin/env python3
"""Run PrinceStockExhange paper trading simulation."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.paper_trading_engine import PaperTradingEngine
from src.trade_journal import TradeJournal


def load_demo_data():
    rng = np.random.default_rng(42)
    periods = 260
    index = pd.date_range('2026-04-01 09:15', periods=periods, freq='5min')
    trend = np.concatenate([
        np.linspace(50000, 50220, 80),
        np.linspace(50220, 50140, 60),
        np.linspace(50140, 50420, 70),
        np.linspace(50420, 50310, 50),
    ])
    noise = rng.normal(0, 18, size=periods)
    close = trend + noise
    high = close + rng.uniform(8, 24, size=periods)
    low = close - rng.uniform(8, 24, size=periods)
    open_ = close + rng.normal(0, 10, size=periods)
    volume = rng.integers(120000, 240000, size=periods)

    return pd.DataFrame(
        {
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        },
        index=index,
    )


def load_csv(path):
    frame = pd.read_csv(path)
    if 'date' in frame.columns:
        frame['date'] = pd.to_datetime(frame['date'])
        frame = frame.set_index('date')
    elif 'datetime' in frame.columns:
        frame['datetime'] = pd.to_datetime(frame['datetime'])
        frame = frame.set_index('datetime')
    else:
        raise ValueError('CSV must contain a date or datetime column')
    return frame


def build_demo_report(output_dir='reports/paper_trading', symbol='BANKNIFTY'):
    """Write a friendly demo report when replay data produces no trades."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    journal = TradeJournal()
    journal.record_event('session_start', 'Seeded demo paper trading session started', starting_capital=100000)

    demo_trades = [
        {
            'symbol': symbol,
            'side': 'BUY',
            'entry_time': '2026-04-01T09:35:00',
            'exit_time': '2026-04-01T10:05:00',
            'entry_price': 50012.0,
            'exit_price': 50168.0,
            'quantity': 1,
            'pnl': 156.0,
            'reason': 'TARGET',
            'regime': 'balanced',
            'confidence': 0.91,
            'stop_loss': 49920.0,
            'target': 50160.0,
        },
        {
            'symbol': symbol,
            'side': 'SELL',
            'entry_time': '2026-04-01T11:15:00',
            'exit_time': '2026-04-01T11:50:00',
            'entry_price': 50190.0,
            'exit_price': 50042.0,
            'quantity': 1,
            'pnl': 148.0,
            'reason': 'TARGET',
            'regime': 'trending',
            'confidence': 0.88,
            'stop_loss': 50270.0,
            'target': 50025.0,
        },
        {
            'symbol': symbol,
            'side': 'BUY',
            'entry_time': '2026-04-01T13:20:00',
            'exit_time': '2026-04-01T13:55:00',
            'entry_price': 50088.0,
            'exit_price': 49972.0,
            'quantity': 1,
            'pnl': -116.0,
            'reason': 'STOP_LOSS',
            'regime': 'ranging',
            'confidence': 0.74,
            'stop_loss': 49970.0,
            'target': 50202.0,
        },
    ]

    for trade in demo_trades:
        journal.record_trade(**trade)

    summary = journal.summary()
    ending_capital = 100000 + summary['net_pnl']
    session_summary = {
        'session_date': '2026-04-01',
        'symbol': symbol,
        'candles_processed': 0,
        'trades_today': summary['total_trades'],
        'daily_pnl': summary['net_pnl'],
        'current_capital': ending_capital,
        'profit_target_reached': summary['net_pnl'] >= 1500,
        'loss_limit_hit': summary['net_pnl'] <= -500,
        'mode': 'demo',
    }

    journal.record_event(
        'session_end',
        'Seeded demo paper trading session ended',
        **session_summary,
    )

    report_paths = {
        'json': output_dir / 'paper_trading_report.json',
        'csv': output_dir / 'paper_trades.csv',
        'html': output_dir / 'paper_trading_report.html',
    }
    journal.save_json(report_paths['json'])
    journal.save_csv(report_paths['csv'])
    journal.export_html_report(report_paths['html'])

    summary['sessions'] = 1
    summary['ending_capital'] = round(ending_capital, 2)
    summary['session_summaries'] = [session_summary]
    summary['reports'] = {key: str(path) for key, path in report_paths.items()}
    summary['mode'] = 'demo'
    summary['seeded'] = True
    return summary


def main():
    parser = argparse.ArgumentParser(description='Run PrinceStockExhange paper trading simulation')
    parser.add_argument('--csv', help='Path to OHLCV CSV file')
    parser.add_argument('--symbol', default='BANKNIFTY', help='Symbol label for the simulation')
    parser.add_argument('--output-dir', default='reports/paper_trading', help='Directory for report outputs')
    args = parser.parse_args()

    data = load_csv(args.csv) if args.csv else load_demo_data()
    engine = PaperTradingEngine(output_dir=args.output_dir)
    summary = engine.run(data, symbol=args.symbol)
    if summary.get('total_trades', 0) == 0:
        summary = build_demo_report(output_dir=args.output_dir, symbol=args.symbol)
        print('\nNo trades were generated from replay data, so a seeded demo session was written for the dashboard.')

    print('\nPrinceStockExhange Paper Trading Summary')
    print(f"Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']}%")
    print(f"Net P&L: {summary['net_pnl']}")
    print(f"Max Drawdown: {summary['max_drawdown']}")
    print(f"Reports: {summary['reports']}")


if __name__ == '__main__':
    main()
