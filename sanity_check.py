#!/usr/bin/env python3
"""Run PrinceStockExhange sanity checks.

This executes the core tests, runs a paper-trading replay, and verifies that
the dashboard report artifacts exist.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def run(command):
    print(f"\n$ {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    print("PrinceStockExhange Sanity Check")
    print("-" * 40)

    run([sys.executable, "-m", "unittest", "tests.test_strategy", "tests.test_paper_trading"])
    run([sys.executable, "paper_trade.py"])

    report_dir = ROOT / "reports" / "paper_trading"
    required = [
        report_dir / "paper_trading_report.html",
        report_dir / "paper_trading_report.json",
        report_dir / "paper_trades.csv",
    ]

    print("\nReport verification:")
    for path in required:
        print(f" - {'OK' if path.exists() else 'MISSING'} {path}")

    if not all(path.exists() for path in required):
        raise SystemExit(1)

    print("\nSanity check complete.")
    print("Open the dashboard with: python serve_dashboard.py")
    print("Then visit: http://127.0.0.1:8000/dashboard/")


if __name__ == "__main__":
    main()
