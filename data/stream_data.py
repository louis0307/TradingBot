from config import ASSET_LIST
from misc.load_data import handle_socket_message
import time
from misc.logger_config import logger
from config import stop_event
from binance import ThreadedWebsocketManager
from misc.login import test_api_key, test_secret_key
import threading

def stream_data():
    logger.info("Starting streaming data cron job.")
    twm = ThreadedWebsocketManager(api_key=test_api_key, api_secret=test_secret_key)
    twm.start()
    for asset in ASSET_LIST:
        twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='15m')
        time.sleep(3)
        twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='1h')
    logger.info("Streaming data initialized.")
    run_duration = 300  # 10 minutes in seconds
    start_time = time.time()

    try:
        while time.time() - start_time < run_duration:
            if stop_event.is_set():
                break
            time.sleep(5)
    finally:
        twm.stop()
        logger.info("Streaming data stopped.")
        logger.info("Streaming data cron job completed.")