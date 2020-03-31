# -*- coding: utf-8 -*-
import logging
import logging.handlers
import pathlib
from os import path
import os
#logging.basicConfig(
#        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#        level=logging.DEBUG)

#logger = logging.getLogger(__name__)


LOG_FILENAME = 'feedrebot.log'
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

## Check if log exists and should therefore be rolled
#needRoll = os.path.isfile(LOG_FILENAME)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(path.join(PROJECT_DIR, LOG_FILENAME), backupCount=50, maxBytes=10000000)

logger.addHandler(handler)

BOT_KEY_FILE = '.key_newsbot'
BOT_KEY = path.join(PROJECT_DIR, BOT_KEY_FILE)

# Number of entries in one digest
DIGEST_LIMIT = 10


# Enable/disable debugging
BOT_DEBUG = True
BOT_EXC_TIMEOUT = 20
BOT_TIMEOUT = 2

PYTHON_EXEC = 'python3'

# Database
MONGO_HOST = '185.62.136.246'
MONGO_PORT = 27017

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'

# Interval of requests to resource
THROTTLE_INTERVAL = 2