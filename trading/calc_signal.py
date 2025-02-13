import time

from config import INTERVALS, ASSET_LIST
from data.db_connection import stream
from data.preprocessing import dat_preprocess
from trading.indicators import macd_trade
from misc.login import client
import datetime
import pandas as pd
import numpy as np
import warnings



def trade_signal():
    interval = INTERVALS
    assets = ASSET_LIST
    pd.options.mode.chained_assignment = None  # default='warn'
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    query = f'SELECT * FROM "public"."TRADES"'
    trades_1 = pd.read_sql(query, stream)
    latest_idx = trades_1.groupby('symbol')['order_timestamp'].idxmax()
    last_trades = trades_1.loc[latest_idx]
    for asset in assets:
        # print(asset)
        quant = 0
        hit = 0
        dat = pd.read_sql(asset, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == asset + interval]
        dat_hist = dat_preprocess(dat_hist)
        dat_hist1h = dat_preprocess(dat[dat['Symbol'] == asset + '1h'])
        filtered_trades = last_trades[last_trades['symbol'] == asset]['signal']
        if not filtered_trades.empty:
            signal_1 = int(filtered_trades.iloc[0])
        else:
            signal_1 = 0
        # ind = math.floor((i+1)/4)
        dat_1 = dat_hist1h.iloc[-1]
        dat_2 = dat_hist1h.iloc[-2]
        dat15m_1 = dat_hist.iloc[-1]
        dat15m_2 = dat_hist.iloc[-2]
        dat15m_3 = dat_hist.iloc[-3]
        signal, hit = macd_trade(dat_1, dat_2, dat15m_1, dat15m_2, dat15m_3, signal_1)
        # exchange_info = client.futures_exchange_info()
        # asset_info = next(symbol for symbol in exchange_info['symbols'] if symbol['symbol'] == asset)
        asset_info = client.get_symbol_info(symbol=asset)
        pos_info = last_trades[last_trades['symbol'] == asset]
        if 'quantity' in pos_info and not pos_info['quantity'].empty:
            pos_amt = np.float32(pos_info['quantity'])
        else:
            pos_amt = 0
        quant_precision = int(asset_info['quotePrecision'])

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
                quant = round(1000 / dat15m_1.close, quant_precision)
        elif signal == -1:
            if signal_1 > 0:
                signal_side = 'SELL'
                quant = 2 * abs(pos_amt)
            elif signal_1 < 0:
                continue
            elif signal_1 == 0:
                signal_side = 'SELL'
                quant = round(1000 / dat15m_1.close, quant_precision)

        quant = float(np.array(quant).item()) if isinstance(quant, (list, np.ndarray)) and len(quant) == 1 else float(
            quant)
        # if quant == 0:
        #    trades = pd.DataFrame(np.array([[asset, 0, None, 'BUY', 0, datetime.datetime.now()] for asset in assets]),
        #                      columns=['symbol','quantity','price','side','signal', 'order_timestamp'])
        # else:
        kdj_cross_signal = 1 if dat_1['KDJ_cross'] == 1 else 0
        trades = pd.DataFrame(np.array([[asset, quant, dat15m_1.close, signal_side, signal, datetime.datetime.now(),
                                         dat_1['MACD_Signal'], dat_1['MACD'], kdj_cross_signal, hit]]),
                              columns=['symbol', 'quantity', 'price', 'side', 'signal', 'order_timestamp',
                                       'MACD_Signal', 'MACD', 'KDJ_cross', 'signal_reason'])
        trades.to_sql('TRADES', stream, if_exists='append', index=False)
