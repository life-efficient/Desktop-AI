import logging
import os

# Ensure the logs directory exists
LOGDIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOGDIR, exist_ok=True)
LOGFILE = os.path.join(LOGDIR, 'main.log')
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'

# Only configure logging once
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGFILE),
        logging.StreamHandler()
    ]
)

def get_logger(name=None):
    return logging.getLogger(name) 