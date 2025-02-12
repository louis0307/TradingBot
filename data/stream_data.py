import main
from misc.load_data import job
import schedule
import time
from misc.logger_config import logger
from main import stop_event

def stream_data():
    times = [":00", ":15", ":30", ":45"]
    for t in times:
        schedule.every().hour.at(t).do(lambda: job('15m'))
    schedule.every().hour.at(":00").do(lambda: job('1h'))
    logger.info("Streaming data initialized.")
    while not stop_event.is_set():
        time.sleep(5)
        schedule.run_pending()
    logger.info("Streaming data stopped.")