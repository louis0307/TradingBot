import main
from config import ASSET_LIST
from misc.load_data import handle_socket_message
import schedule
import time
from misc.logger_config import logger
from config import stop_event
from binance.streams import ThreadedWebsocketManager
import threading

def stream_data():
    twm = ThreadedWebsocketManager()
    twm.start()
    for asset in ASSET_LIST:
        twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='15m')
    logger.info("Streaming data initialized.")
    try:
        while not stop_event.is_set():
            time.sleep(5)
    finally:
        twm.stop()
        logger.info("Streaming data stopped.")