import threading

ASSET_LIST_DATA = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT','DOGEUSDT',
          'SHIBUSDT','AVAXUSDT','DOTUSDT','LINKUSDT','LTCUSDT',
          'FARMUSDT','TNSRUSDT','LEVERUSDT','MEMEUSDT','PEPEUSDT','DODOUSDT',
          'SAGAUSDT','THETAUSDT','ALGOUSDT','AAVEUSDT','CHZUSDT',
          'MANAUSDT','IOTAUSDT','WLDUSDT','ONGUSDT','HBARUSDT', 'SUIUSDT']
ASSET_LIST = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT',
          'AVAXUSDT','LTCUSDT','TNSRUSDT','LEVERUSDT','MEMEUSDT',
          'SAGAUSDT','THETAUSDT','ALGOUSDT','AAVEUSDT','CHZUSDT',
          'MANAUSDT','IOTAUSDT','WLDUSDT','ONGUSDT','HBARUSDT']
INTERVALS = '15m'

stop_event = threading.Event()