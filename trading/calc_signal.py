import time
import datetime
import pandas as pd
import numpy as np
import warnings
import pytz
from sqlalchemy import text
from decimal import Decimal

from config import INTERVALS, ASSET_LIST, INVESTMENT_AMT
from data.db_connection import stream
from data.preprocessing import dat_preprocess
from trading.indicators import macd_trade
from misc.login import client
from misc.logger_config import logger


def trade_signal():
    interval = INTERVALS
    assets = ASSET_LIST
    pd.options.mode.chained_assignment = None  # default='warn'
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    query = f'SELECT * FROM "public"."TRADES" ORDER BY "order_timestamp" ASC'
    query2 = f'SELECT * FROM public."PRECISION_INFO"'
    query3 = f'SELECT * FROM public."POSITION_AMOUNTS"'
    trades_1 = pd.read_sql(query, stream)
    precision_info = pd.read_sql(query2, stream)
    pos_amts = pd.read_sql(query3, stream)
    latest_idx = trades_1.groupby('symbol')['order_timestamp'].idxmax()
    last_trades = trades_1.loc[latest_idx]

    for asset in assets:
        # print(asset)
        quant = 0
        hit = ""
        dat = pd.read_sql(asset, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == asset + interval]
        dat_hist = dat_hist.sort_index()
        dat_hist = dat_preprocess(dat_hist)
        dat_hist1h_temp = dat[dat['Symbol'] == asset + '1h']
        dat_hist1h = dat_hist1h_temp.sort_index()
        dat_hist1h = dat_preprocess(dat_hist1h)
        dat_hist1h_store = dat_hist1h[['Symbol', 'volume', 'log_returns', 'volume_change', 'ema_50',
                                       'ema_200', 'rsi_14', 'volatility', 'MACD', 'MACD_Signal', 'MACD_Hist',
                                       'KDJ_cross', 'K', 'D', 'J']]

        asset_symbol = asset + '1h'  # Ensure correct asset format
        with stream.connect() as conn:
            # Use parameterized query for safety
            conn.execute(text('DELETE FROM public."INDICATORS" WHERE "Symbol" = :symbol'), {"symbol": asset_symbol})
            conn.commit()  # Commit deletion

        dat_hist1h_store.to_sql('INDICATORS', stream, if_exists='append', index=True)
        filtered_trades = last_trades[last_trades['symbol'] == asset]['signal']
        if not filtered_trades.empty:
            signal_1 = int(filtered_trades.iloc[0])
        else:
            signal_1 = 0
        # ind = math.floor((i+1)/4)
        # logger.info(f"asset: {asset} {dat_hist1h}")
        dat_1 = dat_hist1h.iloc[-1]
        dat_2 = dat_hist1h.iloc[-2]
        dat15m_1 = dat_hist.iloc[-1]
        dat15m_2 = dat_hist.iloc[-2]
        dat15m_3 = dat_hist.iloc[-3]
        signal, hit = macd_trade(dat_1, dat_2, dat15m_1, dat15m_2, dat15m_3, signal_1)
        #symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == asset), None)

        quant_precision = int(precision_info.loc[precision_info['symbol'] == asset, 'quantityPrecision'].values[0])

        #if symbol_info:
        #    for f in symbol_info['filters']:
        #        if f['filterType'] == 'LOT_SIZE':
        #            step_size = f['stepSize']
        #            quant_precision = abs(Decimal(step_size).as_tuple().exponent)
        #            #logger.info(f"Quantity precision for {asset}: {quant_precision}")
        #else:
        #    print(f"Symbol {asset} not found in exchange info.")

        pos_amts_temp = pos_amts.loc[pos_amts['symbol'] == asset, 'positionAmt']

        if not pos_amts_temp.empty:
            pos_amt = float(pos_amts_temp.values[0])
        else:
            pos_amt = 0.0

        if signal == 0:
            if signal_1 > 0:
                signal_side = 'SELL'
                quant = abs(pos_amt)
            elif signal_1 < 0:
                signal_side = 'BUY'
                quant = abs(pos_amt)
            else:
                continue
        elif signal == 1:
            if signal_1 > 0:
                continue
            elif signal_1 < 0:
                signal_side = 'BUY'
                quant = 2 * abs(pos_amt)
            elif signal_1 == 0:
                signal_side = 'BUY'
                quant = round(INVESTMENT_AMT / dat15m_1.close, quant_precision)
        elif signal == -1:
            if signal_1 > 0:
                signal_side = 'SELL'
                quant = 2 * abs(pos_amt)
            elif signal_1 < 0:
                continue
            elif signal_1 == 0:
                signal_side = 'SELL'
                quant = round(INVESTMENT_AMT / dat15m_1.close, quant_precision)

        quant = float(np.array(quant).item()) if isinstance(quant, (list, np.ndarray)) and len(quant) == 1 else float(quant)
        #quant = Decimal(str(quant))
        logger.info(f"Asset: {asset} Signal: {signal} Previous Signal: {signal_1} Amount: {quant} Pos Amount: {pos_amt}")
        try:
        #if lower_limit <= current_price <= upper_limit:
            order = client.futures_create_order(
                #isIsolated=True,
                positionSide='BOTH',
                quantity=quant,
                side=signal_side,
                symbol=asset,
                type='MARKET')

            kdj_cross_signal = 1 if dat_1['KDJ_cross'] == 1 else 0
            trades = pd.DataFrame(
                np.array([[asset, quant, dat15m_1.close, signal_side, signal, datetime.datetime.now(),
                           dat_1['MACD_Signal'], dat_1['MACD'], kdj_cross_signal, hit, quant_precision]]),
                columns=['symbol', 'quantity', 'price', 'side', 'signal', 'order_timestamp',
                         'MACD_Signal', 'MACD', 'KDJ_cross', 'signal_reason', 'quant_precision'])
            trades.to_sql('TRADES', stream, if_exists='append', index=False)
        except Exception as e:
            logger.info(f"Couldn't trade asset: {asset} with error {e}")

