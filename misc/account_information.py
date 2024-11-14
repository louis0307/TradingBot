# Importing libraries
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