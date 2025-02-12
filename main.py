import time

from misc.logger_config import logger
from trading.calc_signal import trade_signal
from data.stream_data import stream_data

import schedule
import threading

trading_thread = None
stop_event = threading.Event()

def start_trading_bot():
    global stop_event
    stop_event.clear()

    stream_thread = threading.Thread(target=stream_data, daemon=True)
    stream_thread.start()
    times = [":00", ":15", ":30", ":45"]
    for t in times:
        schedule.every().hour.at(t).do(trade_signal)
    logger.info("Trading bot initialized.")
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def stop_trading_bot():
    global stop_event
    stop_event.set()
    logger.info("Trading bot stopped.")