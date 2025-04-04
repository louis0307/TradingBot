from config import ASSET_LIST_DATA
from misc.load_data import handle_socket_message
import time
from misc.logger_config import logger
from config import stop_event
from binance import ThreadedWebsocketManager
from misc.login import test_api_key, test_secret_key
import threading

def stream_data():
    logger.info("Starting streaming data cron job.")

    try:
        twm = ThreadedWebsocketManager(api_key=test_api_key, api_secret=test_secret_key)
        twm.start()
        logger.info("Binance WebSocket Manager started.")

        for asset in ASSET_LIST_DATA:
            #logger.info(f"Subscribing to {asset} 15m and 1h Kline data.")
            twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='15m')
            time.sleep(1)
            twm.start_kline_socket(callback=handle_socket_message, symbol=asset.lower(), interval='1h')

        logger.info("Streaming data initialized.")

        # Run for 3 minutes
        run_duration = 120
        start_time = time.time()

        while time.time() - start_time < run_duration:
            time.sleep(2)

    except Exception as e:
        logger.error(f"Error in stream_data: {e}")

    finally:
        twm.stop()
        logger.info("Streaming data stopped.")
        logger.info("Streaming data cron job completed.")

if __name__ == "__main__":
    stream_data()
