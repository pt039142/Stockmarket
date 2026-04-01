import logging
import os

# Setup logging
log_path = os.path.join(os.path.dirname(__file__), '../logs/trading.log')
logging.basicConfig(filename=log_path, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

def log_event(event):
    logging.info(event)
