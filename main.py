import sys
import time
from misc.logger_config import logger
from config import stop_event
from trading.calc_signal import trade_signal

import schedule
import threading

trade_thread = None

def run_trade():
    if stop_event.is_set():
        return
    for _ in range(30):  # Check stop_event periodically to avoid delay issues
        if stop_event.is_set():
            return
        time.sleep(1)
    trade_signal()
    logger.info("Trade signal generated.")

def run_trade_thread():
    global trade_thread
    if trade_thread and trade_thread.is_alive():
        logger.info("Trading thread is already running.")
        return

    trade_thread = threading.Thread(target=run_trade, daemon=True)
    trade_thread.start()

def start_trading_bot():
    stop_event.clear()
    schedule.every().hour.at(":00").do(run_trade_thread)
    schedule.every().hour.at(":15").do(run_trade_thread)
    schedule.every().hour.at(":30").do(run_trade_thread)
    schedule.every().hour.at(":45").do(run_trade_thread)
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
    global trade_thread
    stop_event.set()
    logger.info("Trading bot stopped.")
