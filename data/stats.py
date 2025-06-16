import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from config import INTERVALS, ASSET_LIST, INVESTMENT_AMT
from data.db_connection import stream
from misc.logger_config import logger

def calc_pv_total():
    all_timestamps = set()  # Collect all unique timestamps
    pv_list = []  # Store individual asset DataFrames
    query = f'SELECT DISTINCT * FROM "public"."PORTFOLIO_VALUES"'
    pvs = pd.read_sql(query, stream)

    for asset in ASSET_LIST:
        pv_asset = pvs[pvs["symbol"] == asset].copy()
        pv_asset["timestamp"] = pd.to_datetime(pv_asset["timestamp"])
        pv_asset = pv_asset.sort_values("timestamp")
        pv_asset = pv_asset.drop(columns=["symbol"])
        df = pv_asset.copy().reset_index(drop=True)
        df["timestamp"] = df["timestamp"].dt.ceil("T")  # Round timestamp
        df.rename(columns={"portfolio_value": asset}, inplace=True)  # Rename for merging
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        pv_list.append(df)
        all_timestamps.update(df["timestamp"])  # Store timestamps

    # Step 1: Create a DataFrame with all timestamps
    full_timestamps = pd.DataFrame({"timestamp": sorted(all_timestamps)})

    # Step 2: Start with a DataFrame containing all timestamps
    pv = full_timestamps.copy()
    pv["timestamp"] = pd.to_datetime(pv["timestamp"])

    # Step 3: Merge each asset's data
    for df in pv_list:
        df = df.drop(columns=["index"], errors="ignore")
        df = df.groupby("timestamp", as_index=False).last()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        pv = pv.merge(df, on="timestamp", how="left")  # Ensure all timestamps are included

    # Step 4: Forward-fill missing values
    pv.ffill(inplace=True)

    # Step 5: Compute total portfolio value
    pv["portfolio_value"] = pv[ASSET_LIST].sum(axis=1)  # Sum asset values per timestamp

    return pv


# ---- Trade Statistics ----
def compute_trade_stats(trades):
    trades_asset = trades.copy()
    logger.info(f"Step 1: {trades_asset}")
    trades_asset["timestamp"] = pd.to_datetime(trades_asset["timestamp"])
    logger.info(f"Step 2: {trades_asset}")
    trades_asset = trades_asset.sort_values("timestamp")
    logger.info(f"Step 3: {trades_asset}")
    win_rate = (trades_asset["win_loss"] > 0).mean() * 100
    avg_gain = trades_asset.loc[trades_asset["win_loss"] > 0, "win_loss"].mean()
    max_gain = trades_asset.loc[trades_asset["win_loss"] > 0, "win_loss"].max()
    avg_loss = trades_asset.loc[trades_asset["win_loss"] < 0, "win_loss"].mean()
    max_loss = trades_asset.loc[trades_asset["win_loss"] < 0, "win_loss"].min()
    avg_duration = trades_asset["duration"].mean()

    long_stats = trades_asset[trades_asset["side"] == "BUY"]["win_loss"].agg(["mean", "count"])
    short_stats = trades_asset[trades_asset["side"] == "SELL"]["win_loss"].agg(["mean", "count"])

    if trades_asset.empty:
        # Add empty stats for this asset
        summary = pd.DataFrame({
            "Metric": [
                "Total Trades",
                "Win Rate (%)",
                "Avg Gain",
                "Max Gain",
                "Avg Loss",
                "Max Loss",
                "Avg Trade Duration",
                "Long Trades",
                "Avg Long PnL",
                "Short Trades",
                "Avg Short PnL"
            ],
            "Value": [0, 0, None, None, None, None, None, 0, None, 0, None]
        })
        logger.info(f"Step 4: {summary}")
        return summary

    summary = pd.DataFrame({
        "Metric": [
            "Total Trades",
            "Win Rate (%)",
            "Avg Gain",
            "Max Gain",
            "Avg Loss",
            "Max Loss",
            "Avg Trade Duration",
            "Long Trades",
            "Avg Long PnL",
            "Short Trades",
            "Avg Short PnL"
        ],
        "Value": [
            len(trades_asset),
            round(win_rate, 2),
            round(avg_gain, 2),
            round(max_gain, 2),
            round(avg_loss, 2),
            round(max_loss, 2),
            str(avg_duration),
            int(long_stats["count"]),
            round(long_stats["mean"], 2),
            int(short_stats["count"]),
            round(short_stats["mean"], 2)
        ]
    })

    return summary


