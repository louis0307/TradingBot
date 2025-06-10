# Importing libraries
import time
from threading import Event
import pandas as pd
import nest_asyncio
nest_asyncio.apply()

from binance import ThreadedWebsocketManager
from misc.login import test_api_key, test_secret_key
from misc.logger_config import logger
from misc.login import client

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


def get_binance_futures_position():
    twm = ThreadedWebsocketManager(api_key=test_api_key, api_secret=test_secret_key)
    open_positions = {}
    precision_data = {}
    done_event = Event()

    def handle_futures_message(msg):
        if msg.get("e") == "ACCOUNT_UPDATE":
            balances = msg["a"]["P"]  # Position updates
            for pos in balances:
                symbol = pos["s"]
                position_amt = float(pos["pa"])
                if position_amt != 0:
                    open_positions[symbol] = position_amt
            done_event.set()

    try:
        twm.start()
        twm.start_futures_user_socket(callback=handle_futures_message)

        # Wait for update or timeout
        done_event.wait(timeout=10)

        # Get precision data from REST endpoint
        exchange_info = client.futures_exchange_info()
        time.sleep(1)
        for symbol_info in exchange_info["symbols"]:
            symbol = symbol_info["symbol"]
            precision_data[symbol] = symbol_info.get("quantityPrecision")

        # Access response headers
        used_weight = client.response.headers.get('X-MBX-USED-WEIGHT-1M')
        logger.info(f"Used weight in the last minute: {used_weight}")
        logger.info(f"Open positions: {open_positions}")
        logger.info(f"Quantity precision: {precision_data}")

        return open_positions, precision_data

    except Exception as e:
        logger.error(f"Error: {e}")
        return {}, {}

    finally:
        twm.stop()