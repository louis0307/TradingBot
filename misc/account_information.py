# Importing libraries
import time
from misc.login import client
import pandas as pd
import nest_asyncio
nest_asyncio.apply()
from binance import ThreadedWebsocketManager
from misc.login import test_api_key, test_secret_key

def createMatrix(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:, ['s', 'E', 'p']]  # s=symbol, E=timestamp, p=price
    df.columns = ['Symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df


def total_amount_usdt(assets, values, token_usdt):
    """
    Function to calculate total portfolio value in USDT
    :param assets: Assets list
    :param values: Assets quantity
    :param token_usdt: Token pair price dict
    :return: total value in USDT
    """
    total_amount = 0
    for i, token in enumerate(assets):
        if token != 'USDT':
            total_amount += float(values[i]) * float(token_usdt[token + 'USDT'])
        else:
            total_amount += float(values[i]) * 1
    return total_amount


def amount_usdt(assets, values, token_usdt):
    """
    Function to calculate asset value in USDT
    :param assets: Assets list
    :param values: Assets quantity
    :param token_usdt: Token pair price dict
    :return: value in USDT
    """
    total_amount = []
    for i, token in enumerate(assets):
        if token != 'USDT':
            total_amount.append(float(values[i]) * float(token_usdt[token + 'USDT']))
        else:
            total_amount.append(float(values[i]) * 1)
    return total_amount


def total_amount_eth(assets, values, token_usdt):
    """
    Function to calculate total portfolio value in BTC
    :param assets: Assets list
    :param values: Assets quantity
    :param token_usdt: Token pair price dict
    :return: total value in BTC
    """
    total_amount = 0
    for i, token in enumerate(assets):
        if token != 'BTC' and token != 'USDT':
            total_amount += float(values[i]) \
                            * float(token_usdt[token + 'USDT']) \
                            / float(token_usdt['ETHUSDT'])
        if token == 'BTC':
            total_amount += float(values[i]) * 1
        else:
            total_amount += float(values[i]) / float(token_usdt['ETHUSDT'])
    return round(total_amount)


def assets_usdt(assets, values, token_usdt):
    """
    Function to convert all assets into equivalent USDT value
    :param assets: Assets list
    :param values: Assets quantity
    :param token_usdt: Token pair price dict
    :return: total value in USDT
    """
    assets_in_usdt = []
    for i, token in enumerate(assets):
        if token != 'USDT':
            assets_in_usdt.append(float(values[i]) * float(token_usdt[token + 'USDT']))
        else:
            assets_in_usdt.append(float(values[i] * 1))
    return assets_in_usdt


def handle_futures_message(msg):
    """Handles incoming futures account updates."""
    positions = msg.get("data", {}).get("B", [])  # List of position details
    open_positions = {pos["s"]: float(pos["pa"]) for pos in positions if float(pos["pa"]) != 0}
    return open_positions

def get_binance_futures_position():
    try:
        twm = ThreadedWebsocketManager(api_key=test_api_key, api_secret=test_secret_key)
        twm.start()
        open_positions = {}
        precision_data = {}

        def handle_exchange_info(msg):
            """Handles incoming exchange information updates."""
            nonlocal precision_data
            symbols_info = msg.get("data", {}).get("symbols", [])
            precision_data = {
                symbol["symbol"]: symbol["quantityPrecision"]
                for symbol in symbols_info
            }
        def handle_futures_message(msg):
            """Handles incoming futures account updates."""
            positions = msg.get("data", {}).get("B", [])  # List of position details
            nonlocal open_positions
            open_positions = {pos["s"]: float(pos["pa"]) for pos in positions if float(pos["pa"]) != 0}

        # Subscribe to futures account updates
        twm.start_user_socket(handle_futures_message)
        time.sleep(1)
        twm.start_futures_market_socket(handle_exchange_info)

        # Allow time for data retrieval
        time.sleep(5)

        # Stop WebSocket after retrieving positions
        twm.stop()

        return open_positions, precision_data
    except Exception as e:
        print(f"Error fetching position: {e}")
        return 0
