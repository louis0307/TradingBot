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
                if prev_row["signal"] == 0 and row["signal"] != 0:
                    position += 0
                else:
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
    pv_list = []  # Store individual asset dataframes
    all_timestamps = set()  # To collect all unique timestamps

    for asset in ASSET_LIST:
        pv_asset = calc_pv(asset)  # Get portfolio value for asset
        df = pd.DataFrame(pv_asset)
        df["timestamp"] = df["timestamp"].dt.ceil("T")  # Round to nearest minute

        pv_list.append(df)
        all_timestamps.update(df["timestamp"])  # Collect all timestamps

    # Create a full timestamp index
    all_timestamps = sorted(all_timestamps)  # Ensure order
    full_index = pd.DataFrame({"timestamp": all_timestamps})

    # Merge all asset dataframes on the full timestamp index
    pv = pd.concat(pv_list, ignore_index=True)
    pv = full_index.merge(pv, on="timestamp", how="left")  # Ensure all timestamps exist

    # Forward-fill missing portfolio values
    pv["portfolio_value"] = pv["portfolio_value"].fillna(method="ffill")

    #logger.info(f"pv: {pv}")
    pv.to_sql('PV', stream, if_exists='replace', index=True)

    # Group by timestamp and sum the portfolio values
    df_total = pv.groupby("timestamp", as_index=False)["portfolio_value"].sum()

    return df_total
