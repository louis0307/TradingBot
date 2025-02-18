from data.db_connection import stream
from misc.logger_config import logger
from trading.calc_signal import trade_signal
import pandas as pd
import numpy as np


def handle_socket_message(msg):
    try:
        if not msg['k']['x']:  # Check if the candle is closed
            return

        asset = msg['s']  # Symbol
        interval = msg['k']['i']  # Intervall
        latest_candle = [[
            msg['k']['t'],  # open time
            msg['k']['o'],  # open
            msg['k']['h'],  # high
            msg['k']['l'],  # low
            msg['k']['c'],  # close
            msg['k']['v'],  # volume
            msg['k']['T'],  # close time
            msg['k']['q'],  # quote asset volume
            msg['k']['n'],  # number of trades
            msg['k']['V'],  # taker buy base asset volume
            msg['k']['Q'],  # taker buy quote asset volume
            msg['k']['B']  # ignore
        ]]

        coin_df = pd.DataFrame(latest_candle,
                               columns=["dateTime", "open", "high", "low", "close", "volume", "closeTime",
                                        "quoteAssetVolume", "numberOfTrades", "takerBuyBaseVol", "takerBuyQuoteVol",
                                        "ignore"])
        coin_df.dateTime = pd.to_datetime(coin_df.dateTime, unit='ms')
        coin_df.closeTime = pd.to_datetime(coin_df.closeTime, unit='ms')
        coin_df["Symbol"] = asset + interval
        coin_df = coin_df.astype(
            {"open": np.float64, "high": np.float64, "low": np.float64, "close": np.float64, "volume": np.float64})

        coin_df.to_sql(asset, stream, if_exists='append', index=False)
        # logger.info(f"Data for {asset} stored successfully.")
        trade_signal()
    except Exception as e:
        logger.error(f"Error processing {asset}: {e}")