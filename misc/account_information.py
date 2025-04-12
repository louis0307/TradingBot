# Importing libraries
from misc.login import client
import pandas as pd
import nest_asyncio
nest_asyncio.apply()

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



def get_binance_futures_position(asset):
    try:
        positions = client.futures_position_information(symbol=asset.upper())
        for pos in positions:
            pos_amt = float(pos['positionAmt'])
            if pos_amt != 0:
                return pos_amt  # return the current open position (positive or negative)
        return 0
    except Exception as e:
        print(f"Error fetching position for {asset}: {e}")
        return 0
