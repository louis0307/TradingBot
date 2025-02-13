import sys
import time

from misc.logger_config import logger
from trading.calc_signal import trade_signal
from data.stream_data import stream_data
from config import stop_event

import schedule
import threading

trading_thread = None

def start_trading_bot():
    global stop_event
    stop_event.clear()

    stream_thread = threading.Thread(target=stream_data, daemon=True)
    stream_thread.start()
    logger.info("Trading bot initialized.")
    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        stop_trading_bot()

def stop_trading_bot():
    global stop_event
    stop_event.set()
    logger.info("Trading bot stopped.")
