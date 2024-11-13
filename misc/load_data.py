from login import client
import pandas as pd
import numpy as np

def job(interval):
    assets = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT','DOGEUSDT',
          'SHIBUSDT','AVAXUSDT','DOTUSDT','LINKUSDT','LTCUSDT','MATICUSDT',
          'FARMUSDT','TNSRUSDT','LEVERUSDT','MEMEUSDT','PEPEUSDT','DODOUSDT',
          'SAGAUSDT','THETAUSDT','FTMUSDT','ALGOUSDT','AAVEUSDT','CHZUSDT',
          'MANAUSDT','IOTAUSDT','WLDUSDT','ONGUSDT']
    for asset in assets:
        candle = client.get_klines(symbol=asset, interval=interval, limit=1)
        latest_candle = [candle[-1]]
        # open time
        # open
        # high
        # low
        # close
        # volume
        # close time
        # quote asset volume
        # number of trades
        # taker buy base asset volume
        # taker buy quote asset volume
        # ignore
        # convert into data frame and saving as csv
        coin_df = pd.DataFrame(latest_candle, columns=["dateTime", "open", "high", "low", "close", "volume", "closeTime", "quoteAssetVolume", "numberOfTrades", "takerBuyBaseVol", "takerBuyQuoteVol", "ignore"])
        coin_df.dateTime = pd.to_datetime(coin_df.dateTime, unit='ms')
        coin_df.closeTime = pd.to_datetime(coin_df.closeTime, unit='ms')
        coin_df["Symbol"] = asset+interval
        new_dtypes = {"open":np.float64, "high":np.float64, "low":np.float64, "close":np.float64, "volume":np.float64}
        coin_df = coin_df.astype(new_dtypes)
        #print(coin_df.tail(10))
        # store data
        coin_df.to_sql(asset, stream, if_exists='append', index=False) # if_exists = 'replace' / 'append'