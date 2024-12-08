from misc.logger_config import logger
from trading.calc_signal import trade_signal
from data.stream_data import stream_data

import schedule
import threading

stop_event = threading.Event()

def start_trading_bot():
    stream_data()

    times = ["00:10", "15:10", "30:10", "45:10"]
    for t in times:
        schedule.every().hour.at(t).do(trade_signal)
    logger.info("Trading bot initialized.")
    while not stop_event.is_set():
        schedule.run_pending()

def stop_trading_bot():
    stop_event.set()
    logger.info("Trading bot stopped.")