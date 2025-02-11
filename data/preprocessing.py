from trading.indicators import calculate_rsi, kdj
import numpy as np
from misc.logger_config import logger

def dat_preprocess(dat_in):
    dat = dat_in.copy()
    dat['log_returns'] = np.log(dat.close) - np.log(dat.close.shift(1))
    dat['volume_change'] = np.log(dat.volume) - np.log(dat.volume.shift(1))
    dat['volume_change_perc'] = dat.volume / dat.volume.shift(1) - 1
    dat['vol_ma10'] = dat.volume.rolling(10).mean()
    dat['ema_50'] = dat.close.ewm(span=50, adjust=False).mean()
    dat['ema_200'] = dat.close.ewm(span=200, adjust=False).mean()
    dat['rsi_14'] = calculate_rsi(dat.close, period=14)
    dat['volatility'] = dat.log_returns.rolling(window=10).std()
    dat['MACD'] = dat.close.ewm(span=12, adjust=False).mean() - dat.close.ewm(span=26, adjust=False).mean()
    dat['MACD_Signal'] = dat['MACD'].ewm(span=9, adjust=False).mean()
    dat['MACD_Hist'] = dat['MACD'] - dat['MACD_Signal']
    dat = kdj(dat)
    #dat = dat.dropna(axis=0)
    ret = dat.replace([np.inf, -np.inf], 0, inplace=False)
    return ret