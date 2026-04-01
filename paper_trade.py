#!/usr/bin/env python3
"""Run PrinceStockExhange paper trading simulation."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.paper_trading_engine import PaperTradingEngine


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


def main():
    parser = argparse.ArgumentParser(description='Run PrinceStockExhange paper trading simulation')
    parser.add_argument('--csv', help='Path to OHLCV CSV file')
    parser.add_argument('--symbol', default='BANKNIFTY', help='Symbol label for the simulation')
    parser.add_argument('--output-dir', default='reports/paper_trading', help='Directory for report outputs')
    args = parser.parse_args()

    data = load_csv(args.csv) if args.csv else load_demo_data()
    engine = PaperTradingEngine(output_dir=args.output_dir)
    summary = engine.run(data, symbol=args.symbol)

    print('\nPrinceStockExhange Paper Trading Summary')
    print(f"Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']}%")
    print(f"Net P&L: {summary['net_pnl']}")
    print(f"Max Drawdown: {summary['max_drawdown']}")
    print(f"Reports: {summary['reports']}")


if __name__ == '__main__':
    main()
