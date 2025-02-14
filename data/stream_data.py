import main
from config import ASSET_LIST
from misc.load_data import handle_socket_message
import schedule
import time
from misc.logger_config import logger
from config import stop_event
from binance import ThreadedWebsocketManager
import threading

def stream_data():
    twm = ThreadedWebsocketManager()
    twm.start(timeout=5)
    for asset in ASSET_LIST:
        twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='15m')
        time.sleep(2)
        twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='1h')
    logger.info("Streaming data initialized.")
    try:
        time.sleep(1)
        while not stop_event.is_set():
            time.sleep(5)
    finally:
        twm.stop()
        logger.info("Streaming data stopped.")