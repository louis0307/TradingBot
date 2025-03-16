import sys
import time
from misc.logger_config import logger
from misc.global_state import trading_thread
from config import stop_event
from trading.calc_signal import trade_signal

import schedule
import threading

def run_trade():
    if stop_event.is_set():
        return
    for _ in range(30):  # Check stop_event periodically to avoid delay issues
        if stop_event.is_set():
            return
        time.sleep(1)
    trade_signal()

def run_trade_thread():
    trade_thread = threading.Thread(target=run_trade, daemon=True)
    trade_thread.start()

def start_trading_bot():
    stop_event.clear()
    schedule.every(15).minutes.do(run_trade_thread)
    logger.info("Trading bot initialized.")
    try:
        while not stop_event.is_set():
            time.sleep(20)
            schedule.run_pending()
            time.sleep(1)
        logger.info("Trading bot shutting down...")
    finally:
        stop_trading_bot()

def stop_trading_bot():
    stop_event.set()
    logger.info("Trading bot stopped.")
