# Importing libraries
import pandas as pd
from misc.login import client
from misc.logger_config import logger
from data.db_connection import stream


def get_binance_futures_positions():
    logger.info("Starting extracting future positions.")
    try:
        # Get account info, including all positions
        account_info = client.futures_account()
        positions = account_info['positions']

        # Filter for open positions only (non-zero positionAmt)
        open_positions = [
            {
                'symbol': pos['symbol'],
                'positionAmt': float(pos['positionAmt'])
            }
            for pos in positions
            if float(pos['positionAmt']) != 0
        ]

        df = pd.DataFrame(open_positions)

        df.to_sql('POSITION_AMOUNTS', stream, if_exists='replace', index=False)

        logger.info("Loaded and stored all future positions.")
        logger.info("Cron job completed.")

    except Exception as e:
        logger.info(f"Couldn't finish cron job. {e}")