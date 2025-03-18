import time

from config import INTERVALS, ASSET_LIST
from misc.logger_config import logger
from data.db_connection import stream
from data.preprocessing import dat_preprocess
import datetime
import pandas as pd
import numpy as np
import warnings
import pytz

portfolio_value = []

def calc_pv(asset):
    interval = INTERVALS
    pd.options.mode.chained_assignment = None  # default='warn'
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    query = f'SELECT * FROM "public"."TRADES"'
    trades = pd.read_sql(query, stream)
    trades = trades[trades["symbol"] == asset].copy()
    trades["order_timestamp"] = pd.to_datetime(trades["order_timestamp"])
    trades = trades.sort_values("order_timestamp")

    position = 0
    portfolio_values = []

    #dat = pd.read_sql(asset, stream)
    #dat.set_index('dateTime', inplace=True)
    #dat_hist = dat[dat['Symbol'] == asset + interval]
    #dat_hist = dat_preprocess(dat_hist)

    for i, row in trades.iterrows():
        logger.info(f"trades {i}: {row}")
        if row["side"] == "BUY":
            if i > 0 and trades.iloc[i - 1]["side"] == "SELL":
                position = 0  # Closing short
            position += row["quantity"] * row["price"]
        elif row["side"] == "SELL":
            if i > 0 and trades.iloc[i - 1]["side"] == "BUY":
                position = 0  # Closing long
            position -= row["quantity"] * row["price"]

        portfolio_values.append({
            "timestamp": row["order_timestamp"],
            "portfolio_value": position
        })

    return pd.DataFrame(portfolio_values)