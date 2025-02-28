import sys
import time
from misc.logger_config import logger
from data.stream_data import stream_data
from config import stop_event
from trading.calc_signal import trade_signal

import schedule
import threading

trading_thread = None

def run_trade():
    if stop_event.is_set():
        return
    trade_signal()

def run_trade_thread():
    trade_thread = threading.Thread(target=run_trade, daemon=True)
    trade_thread.start()

def start_trading_bot():
    global stop_event
    stop_event.clear()

    schedule.every(15).minutes.at(":30").do(run_trade_thread)

    stream_thread = threading.Thread(target=stream_data, daemon=True)
    stream_thread.start()
    logger.info("Trading bot initialized.")
    try:
        while not stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    finally:
        stop_trading_bot()

def stop_trading_bot():
    global stop_event
    stop_event.set()
    logger.info("Trading bot stopped.")
