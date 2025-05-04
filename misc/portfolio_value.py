import time

from config import INTERVALS, INVESTMENT_AMT
from data.db_connection import stream
import pandas as pd
import warnings
from sqlalchemy import text

from misc.logger_config import logger
from config import stop_event, ASSET_LIST


def calc_pv():
    logger.info("Initialization.")
    if stop_event.is_set():
        logger.info("Trading Bot is not running. No PV calculations.")
        return

    query = f'SELECT * FROM "public"."TRADES"'
    trades_all = pd.read_sql(query, stream)

    for asset in ASSET_LIST:
        pd.options.mode.chained_assignment = None  # default='warn'
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        trades = trades_all[trades_all["symbol"] == asset].copy()
        trades["order_timestamp"] = pd.to_datetime(trades["order_timestamp"])
        trades = trades.sort_values("order_timestamp")

        win_loss = 0
        wins_losses = []
        position = 0
        portfolio_values = []

        if trades.empty:
            now = pd.Timestamp.now()
            rounded = now.replace(minute=45, second=0, microsecond=0)
            portfolio_values.append({
                "timestamp": rounded,
                "portfolio_value": position
            })
            return pd.DataFrame(portfolio_values)

        prev_row = None  # Initialize the previous row for each asset

        for i, row in trades.iterrows():
            # For the first row, we don't need to compare
            if prev_row is not None:
                if prev_row["signal"] == 0 and row["signal"] != 0:
                    position += 0
                else:
                    win_loss = INVESTMENT_AMT / row["price"] * (row["price"] - prev_row["price"]) * prev_row["signal"]
                    position += win_loss

            wins_losses.append({
                "symbol": asset,
                "timestamp": row["order_timestamp"],
                "win_loss": win_loss
            })

            # Append portfolio value for this transaction
            portfolio_values.append({
                "symbol": asset,
                "timestamp": row["order_timestamp"],
                "portfolio_value": position
            })

            prev_row = row  # Update prev_row for the next iteration

        with stream.connect() as conn:
            # Use parameterized query for safety
            conn.execute(text('DELETE FROM public."WINS_LOSSES" WHERE "symbol" = :symbol'), {"symbol": asset})
            conn.commit()  # Commit deletion
        pd.DataFrame(wins_losses).to_sql('WINS_LOSSES', stream, if_exists='append', index=True)

        with stream.connect() as conn:
            # Use parameterized query for safety
            conn.execute(text('DELETE FROM public."PORTFOLIO_VALUES" WHERE "symbol" = :symbol'), {"symbol": asset})
            conn.commit()  # Commit deletion
        pd.DataFrame(portfolio_values).to_sql('PORTFOLIO_VALUES', stream, if_exists='append', index=True)

    logger.info("Job completed.")

if __name__ == "__main__":
    calc_pv()