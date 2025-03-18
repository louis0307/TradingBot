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

    # Group by symbol (asset) to avoid mixing rows of different assets
    for _, group in trades.groupby("symbol"):
        prev_row = None  # Initialize the previous row for each asset

        for i, row in group.iterrows():
            # For the first row, we don't need to compare
            if prev_row is not None:
                if prev_row["side"] == "SELL" and row["side"] == "BUY":
                    position = 0  # Closing short
                elif prev_row["side"] == "BUY" and row["side"] == "SELL":
                    position = 0  # Closing long

            # Update position based on side
            if row["side"] == "BUY":
                position += row["quantity"] * row["price"]
            elif row["side"] == "SELL":
                position -= row["quantity"] * row["price"]

            # Append portfolio value for this transaction
            portfolio_values.append({
                "timestamp": row["order_timestamp"],
                "portfolio_value": position
            })

            prev_row = row  # Update prev_row for the next iteration

    return pd.DataFrame(portfolio_values)