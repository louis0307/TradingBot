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
    investment_amt = 1000

    #dat = pd.read_sql(asset, stream)
    #dat.set_index('dateTime', inplace=True)
    #dat_hist = dat[dat['Symbol'] == asset + interval]
    #dat_hist = dat_preprocess(dat_hist)

    # Group by symbol (asset) to avoid mixing rows of different assets
    for _, group in trades.groupby("symbol"):
        #prev_prev_row = None
        prev_row = None  # Initialize the previous row for each asset

        for i, row in group.iterrows():
            # For the first row, we don't need to compare
            if prev_row is not None:
                #if prev_prev_row["signal"] != 0 and prev_row["signal"] != 0 and row["signal"] == 0:
                #    position += row["quantity"] * row["price"] * prev_row["signal"] - 2*investment_amt
                #elif prev_prev_row["signal"] == 0 and prev_row["signal"] != 0 and row["signal"] == 0:
                #    position += row["quantity"] * row["price"] - investment_amt
                #elif prev_row["signal"] != 0 and row["signal"] != 0:
                #    position += row["quantity"] * row["price"] - 2*investment_amt
                #if prev_row["signal"] == 0 and row["signal"] != 0:
                #    position += 0

                position += investment_amt / row["price"] * (row["price"] - prev_row["price"]) * prev_row["signal"]


            # Append portfolio value for this transaction
            portfolio_values.append({
                "timestamp": row["order_timestamp"],
                "portfolio_value": position
            })

            #prev_prev_row = prev_row
            prev_row = row  # Update prev_row for the next iteration

    return pd.DataFrame(portfolio_values)

def calc_pv_total():
    pv = []
    for asset in ASSET_LIST:
        pv_asset = calc_pv(asset)
        df = pd.DataFrame(pv_asset)
        df["timestamp"] = df["timestamp"].dt.ceil("T")
        pv.append(df)

        if not pv:
            return pd.DataFrame(columns=["timestamp", "portfolio_value"])

    df_total = pd.concat(pv)
    df_total = df_total.groupby("timestamp")["portfolio_value"].sum().reset_index()

    return df_total
