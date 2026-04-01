#!/usr/bin/env python3
"""Serve the PrinceStockExhange dashboard locally."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Serve the PrinceStockExhange dashboard')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    args = parser.parse_args()

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
