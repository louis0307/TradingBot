import time

from config import INTERVALS, ASSET_LIST, INVESTMENT_AMT
from misc.logger_config import logger
from data.db_connection import stream
from data.preprocessing import dat_preprocess
import datetime
import pandas as pd
import numpy as np
import warnings
import pytz
from sqlalchemy import text


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
        #prev_prev_row = None
        prev_row = None  # Initialize the previous row for each asset

        for i, row in group.iterrows():
            # For the first row, we don't need to compare
            if prev_row is not None:
                #if prev_prev_row["signal"] != 0 and prev_row["signal"] != 0 and row["signal"] == 0:
                #    position += row["quantity"] * row["price"] * prev_row["signal"] - 2*INVESTMENT_AMT
                #elif prev_prev_row["signal"] == 0 and prev_row["signal"] != 0 and row["signal"] == 0:
                #    position += row["quantity"] * row["price"] - INVESTMENT_AMT
                #elif prev_row["signal"] != 0 and row["signal"] != 0:
                #    position += row["quantity"] * row["price"] - 2*INVESTMENT_AMT
                if prev_row["signal"] == 0 and row["signal"] != 0:
                    position += 0
                else:
                    position += INVESTMENT_AMT / row["price"] * (row["price"] - prev_row["price"]) * prev_row["signal"]


            # Append portfolio value for this transaction
            portfolio_values.append({
                "timestamp": row["order_timestamp"],
                "portfolio_value": position
            })

            #prev_prev_row = prev_row
            prev_row = row  # Update prev_row for the next iteration

    return pd.DataFrame(portfolio_values)


def calc_pv_total():
    all_timestamps = set()  # Collect all unique timestamps
    pv_list = []  # Store individual asset DataFrames

    for asset in ASSET_LIST:
        pv_asset = calc_pv(asset)  # Get portfolio value for asset
        df = pd.DataFrame(pv_asset)
        df["timestamp"] = df["timestamp"].dt.ceil("T")  # Round timestamp
        df.rename(columns={"portfolio_value": asset}, inplace=True)  # Rename for merging
        pv_list.append(df)
        all_timestamps.update(df["timestamp"])  # Store timestamps

    # Step 1: Create a DataFrame with all timestamps
    full_timestamps = pd.DataFrame({"timestamp": sorted(all_timestamps)})

    # Step 2: Start with a DataFrame containing all timestamps
    pv = full_timestamps.copy()

    # Step 3: Merge each asset's data
    for df in pv_list:
        pv = pv.merge(df, on="timestamp", how="left")  # Ensure all timestamps are included

    # Step 4: Forward-fill missing values
    pv.fillna(method="ffill", inplace=True)

    # Step 5: Compute total portfolio value
    pv["portfolio_value"] = pv[ASSET_LIST].sum(axis=1)  # Sum asset values per timestamp

    return pv
