import logging
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / 'trading.log'

try:
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )
except OSError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )

def log_event(event):
    logging.info(event)
