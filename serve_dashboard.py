#!/usr/bin/env python3
"""Serve the PrinceStockExhange dashboard locally."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from paper_trade import build_demo_report


REPORT_PATH = Path(__file__).parent / 'reports' / 'paper_trading' / 'paper_trading_report.json'


def ensure_dashboard_report():
    """Guarantee the dashboard has usable paper-trading data on startup."""
    if not REPORT_PATH.exists():
        build_demo_report(output_dir=REPORT_PATH.parent)
        return

    try:
        payload = json.loads(REPORT_PATH.read_text(encoding='utf-8'))
    except Exception:
        build_demo_report(output_dir=REPORT_PATH.parent)
        return

    if not payload.get('trades'):
        build_demo_report(output_dir=REPORT_PATH.parent)


def main():
    parser = argparse.ArgumentParser(description='Serve the PrinceStockExhange dashboard')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    args = parser.parse_args()

    ensure_dashboard_report()

    root = Path(__file__).parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    import os
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', str(args.port)))
    server = ThreadingHTTPServer((host, port), handler)

    print(f'PrinceStockExhange dashboard serving at http://{host}:{port}/dashboard/')
    print('Press Ctrl+C to stop.')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down dashboard server...')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
