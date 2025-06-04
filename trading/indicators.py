import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from misc.logger_config import logger

def calculate_rsi(prices, period=6, stoch_period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    rsi_min = rsi.rolling(window=stoch_period, min_periods=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period, min_periods=stoch_period).max()
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min)

    return rsi, stoch_rsi

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    # True Range components
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    # True Range
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # ATR as rolling mean of True Range
    atr = tr.rolling(window=period).mean()
    return atr

def plot_macd(dat_subset):
    # dat_subset_macd = dat_hist4h.loc['2024-02-10':'2024-02-25']
    dat_subset_macd = dat_subset
    fig = make_subplots(rows=2, cols=1)
    # price Line
    fig.append_trace(
        go.Scatter(
            x=dat_subset_macd.index,
            y=dat_subset_macd.open,
            line=dict(color='#ff9900', width=1),
            name='close',
            # showlegend=False,
            legendgroup='1',
        ), row=1, col=1
    )
    # Candlestick chart for pricing
    fig.append_trace(
        go.Candlestick(
            x=dat_subset_macd.index,
            open=dat_subset_macd.open,
            high=dat_subset_macd.high,
            low=dat_subset_macd.low,
            close=dat_subset_macd.close,
            increasing_line_color='#ff9900',
            decreasing_line_color='black',
            showlegend=False
        ), row=1, col=1
    )
    # Fast Signal (%k)
    fig.append_trace(
        go.Scatter(
            x=dat_subset_macd.index,
            y=dat_subset_macd.MACD,
            line=dict(color='#ff9900', width=2),
            name='MACD',
            # showlegend=False,
            legendgroup='2',
        ), row=2, col=1
    )
    # Slow signal (%d)
    fig.append_trace(
        go.Scatter(
            x=dat_subset_macd.index,
            y=dat_subset_macd.MACD_Signal,
            line=dict(color='#000000', width=2),
            # showlegend=False,
            legendgroup='2',
            name='signal'
        ), row=2, col=1
    )
    # Colorize the histogram values
    colors = np.where(dat_subset_macd.MACD_Hist < 0, '#000', '#ff9900')
    # Plot the histogram
    fig.append_trace(
        go.Bar(
            x=dat_subset_macd.index,
            y=dat_subset_macd.MACD_Hist,
            name='histogram',
            marker_color=colors,
        ), row=2, col=1
    )
    # Make it pretty
    layout = go.Layout(
        plot_bgcolor='#efefef',
        # Font Families
        font_family='Monospace',
        font_color='#000000',
        font_size=20,
        xaxis=dict(
            rangeslider=dict(
                visible=False
            )
        )
    )
    # Update options and show plot
    fig.update_layout(layout)
    fig.show()


def macd_trade(dat_1, dat_2, dat15m_1, dat15m_2, dat15m_3, signal_1):
    dat1 = dat_1
    dat2 = dat_2
    signal = 0
    hit = ""

    if dat15m_1['Symbol'] == 'ETHUSDT15m':
        atr_param = 0.005
    elif dat15m_1['Symbol'] == 'ADAUSDT15m':
        atr_param = 0.007
    elif dat15m_1['Symbol'] == 'SOLUSDT15m':
        atr_param = 0.01
    elif dat15m_1['Symbol'] == 'XRPUSDT15m':
        atr_param = 0.007
    elif dat15m_1['Symbol'] == 'AVAXUSDT15m':
        atr_param = 0.005
    elif dat15m_1['Symbol'] == 'LTCUSDT15m':
        atr_param = 0.006
    elif dat15m_1['Symbol'] == 'TNSRUSDT15m':
        atr_param = 0.01
    elif dat15m_1['Symbol'] == 'LEVERUSDT15m':
        atr_param = 0.003
    elif dat15m_1['Symbol'] == 'MEMEUSDT15m':
        atr_param = 0.006
    elif dat15m_1['Symbol'] == 'SAGAUSDT15m':
        atr_param = 0.007
    elif dat15m_1['Symbol'] == 'THETAUSDT15m':
        atr_param = 0.005
    elif dat15m_1['Symbol'] == 'ALGOUSDT15m':
        atr_param = 0.005
    elif dat15m_1['Symbol'] == 'AAVEUSDT15m':
        atr_param = 0.008
    elif dat15m_1['Symbol'] == 'CHZUSDT15m':
        atr_param = 0.004
    elif dat15m_1['Symbol'] == 'MANAUSDT15m':
        atr_param = 0.008
    elif dat15m_1['Symbol'] == 'IOTAUSDT15m':
        atr_param = 0.009
    elif dat15m_1['Symbol'] == 'WLDUSDT15m':
        atr_param = 0.008
    elif dat15m_1['Symbol'] == 'HBARUSDT15m':
        atr_param = 0.006
    elif dat15m_1['Symbol'] == 'SUIUSDT15m':
        atr_param = 0.006
    elif dat15m_1['Symbol'] == 'VETUSDT15m':
        atr_param = 0.007
    else:
        atr_param = 0.006

    atr_threshold = dat15m_1['close'] * atr_param
    # --- ATR Filter: Skip trades in low volatility environments ---
    if dat15m_1['ATR'] < atr_threshold and signal_1 == 0:
        return 0, "1.0"  # skip signal
    if dat2['MACD'] > dat2['MACD_Signal'] and dat1['MACD'] < dat1['MACD_Signal'] and dat1['MACD'] > 0:  # bearish crossing
        signal = -1
        hit = "1.1"
    elif dat2['MACD'] < dat2['MACD_Signal'] and dat1['MACD'] < dat1['MACD_Signal']:  # bearish continuation
        if (dat1['KDJ_cross'] == 1 and dat1['J'] > dat1['D'] and dat1['MACD'] < 0) or signal_1 == 1:
            signal = 1
            hit = "2.1"
        else:
            signal = -1
            hit = "2.2"
        #if (dat15m_3['log_returns'] + dat15m_2['log_returns'] + dat15m_1['log_returns']) / 3 > 0:
        #    signal = 0
        #    hit = "2.3"
            # Filter: avoid long entries if StochRSI is high (not oversold)
        if dat1['stoch_rsi'] is not None and signal == 1 and dat1['stoch_rsi'] > 0.2:
            signal = 0
            hit = "2.4"
    elif dat2['MACD'] > dat2['MACD_Signal'] and dat1['MACD'] > dat1['MACD_Signal']:  # bullish continuation
        if (dat1['KDJ_cross'] == 1 and dat1['J'] < dat1['D'] and dat1['MACD'] > 0) or signal_1 == -1:
            signal = -1
            hit = "3.1"
        else:
            signal = 1
            hit = "3.2"
        #if (dat15m_3['log_returns'] + dat15m_2['log_returns'] + dat15m_1['log_returns']) / 3 < 0:  # or signal_1 == 0
        #    signal = 0
        #    hit = "3.3"
            # Filter: avoid short entries if StochRSI is low (not overbought)
        if dat1['stoch_rsi'] is not None and signal == -1 and dat1['stoch_rsi'] < 0.8:
            signal = 0
            hit = "3.4"
    elif dat2['MACD'] < dat2['MACD_Signal'] and dat1['MACD'] > dat1['MACD_Signal'] and dat1['MACD'] < 0:  # bullish crossing
        signal = 1
        hit = "4.1"
    return signal, hit


def kdj(data):
    dat = data.copy()
    low_min = dat['low'].rolling(window=9, min_periods=1).min()
    high_max = dat['high'].rolling(window=9, min_periods=1).max()
    dat['RSV'] = (dat['close'] - low_min) / (high_max - low_min) * 100
    dat['K'] = dat['RSV'].ewm(com=2, adjust=False).mean()
    dat['D'] = dat['K'].ewm(com=2, adjust=False).mean()
    dat['J'] = 3 * dat['K'] - 2 * dat['D']
    diff_kd_t = dat['K'] - dat['D']
    diff_kj_t = dat['K'] - dat['J']
    diff_dj_t = dat['D'] - dat['J']
    diff_kd_t_1 = diff_kd_t.shift(1)
    diff_kj_t_1 = diff_kj_t.shift(1)
    diff_dj_t_1 = diff_dj_t.shift(1)
    crossings_kd = (diff_kd_t * diff_kd_t_1 < 0).astype(int)
    crossings_kj = (diff_kj_t * diff_kj_t_1 < 0).astype(int)
    crossings_dj = (diff_dj_t * diff_dj_t_1 < 0).astype(int)
    crossings = (crossings_kd & crossings_kj & crossings_dj).astype(bool)
    dat['KDJ_cross'] = crossings
    return dat
