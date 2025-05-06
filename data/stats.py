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
    pv.fillna(method="ffill", inplace=True)

    # Step 5: Compute total portfolio value
    pv["portfolio_value"] = pv[ASSET_LIST].sum(axis=1)  # Sum asset values per timestamp

    return pv


def reconstruct_trades(trades):
    trades = trades.sort_values("order_timestamp").copy()
    trades["order_timestamp"] = pd.to_datetime(trades["order_timestamp"])

    open_trade = None
    trade_list = []

    for _, row in trades.iterrows():
        signal = row["signal"]

        if signal != 0 and open_trade is None:
            # Open a new trade
            open_trade = {
                "symbol": row["symbol"],
                "side": "long" if signal == 1 else "short",
                "entry_time": row["order_timestamp"],
                "entry_price": row["price"],
                "quantity": row["quantity"]
            }

        elif signal == 0 and open_trade is not None:
            # Close trade
            open_trade["exit_time"] = row["order_timestamp"]
            open_trade["exit_price"] = row["price"]
            trade_list.append(open_trade)
            open_trade = None

    return pd.DataFrame(trade_list)


# ---- Trade Statistics ----
def compute_trade_stats(trades):
    trades = trades.copy()

    # Calculate PnL
    trades["pnl_pct"] = np.where(
        trades["side"] == "long",
        (trades["exit_price"] - trades["entry_price"]) / trades["entry_price"],
        (trades["entry_price"] - trades["exit_price"]) / trades["entry_price"]
    ) * 100

    trades["duration"] = pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])

    win_rate = (trades["pnl_pct"] > 0).mean() * 100
    avg_gain = trades.loc[trades["pnl_pct"] > 0, "pnl_pct"].mean()
    avg_loss = trades.loc[trades["pnl_pct"] < 0, "pnl_pct"].mean()
    avg_duration = trades["duration"].mean()

    long_stats = trades[trades["side"] == "long"]["pnl_pct"].agg(["mean", "count"])
    short_stats = trades[trades["side"] == "short"]["pnl_pct"].agg(["mean", "count"])

    summary = pd.DataFrame({
        "Metric": [
            "Total Trades",
            "Win Rate (%)",
            "Avg Gain (%)",
            "Avg Loss (%)",
            "Avg Trade Duration",
            "Long Trades",
            "Avg Long PnL (%)",
            "Short Trades",
            "Avg Short PnL (%)"
        ],
        "Value": [
            len(trades),
            round(win_rate, 2),
            round(avg_gain, 2),
            round(avg_loss, 2),
            str(avg_duration),
            int(long_stats["count"]),
            round(long_stats["mean"], 2),
            int(short_stats["count"]),
            round(short_stats["mean"], 2)
        ]
    })

    return summary

# ---- Drawdown Analysis ----
def compute_drawdown(portfolio_df):
    portfolio_df = portfolio_df.copy()
    portfolio_df["timestamp"] = pd.to_datetime(portfolio_df["timestamp"])
    portfolio_df.set_index("timestamp", inplace=True)

    portfolio_df["cummax"] = portfolio_df["portfolio_value"].cummax()
    portfolio_df["drawdown"] = portfolio_df["portfolio_value"] / portfolio_df["cummax"] - 1

    max_dd = portfolio_df["drawdown"].min()

    print("\nDRAWDOWN STATS")
    print(f"Max Drawdown: {max_dd:.2%}")

    # Plot
    plt.figure(figsize=(10, 4))
    plt.plot(portfolio_df.index, portfolio_df["drawdown"], label="Drawdown", color='red')
    plt.fill_between(portfolio_df.index, portfolio_df["drawdown"], 0, alpha=0.3, color='red')
    plt.title("Portfolio Drawdown Over Time")
    plt.ylabel("Drawdown")
    plt.grid()
    plt.tight_layout()
    plt.legend()
    plt.show()

    return portfolio_df

