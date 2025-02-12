from config import INTERVALS, ASSET_LIST
from data.db_connection import stream
from data.preprocessing import dat_preprocess
from misc.logger_config import logger
from main import start_trading_bot, stop_trading_bot

import os
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from flask import Flask, redirect, url_for, request, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from threading import Thread
import dash_auth
from dash_auth import BasicAuth


logger.info("Starting the web application")

# Flask-Login setup
secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

trading_thread = None

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
#dash_authentication = BasicAuth(server, '/login', '/dashboard', secret_key)

server.secret_key = secret_key
if not server.secret_key:
    raise ValueError("No SECRET_KEY set for Flask application.")
@server.before_request
def enforce_https():
    if not request.is_secure and request.headers.get("X-Forwarded-Proto", "http") != "https": # X-Forwarded-Proto is there to deal with the fact that in Render reverse proxy/load balancer is used
                                                                                              # and that nevertheless we can see whether the request is http or https
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code = 301)

users = {username: password}
auth = dash_auth.BasicAuth(app, users)

# Load complete history for each asset at startup
data_dict = {}
for asset in ASSET_LIST:
    #try:
    query = f'SELECT * FROM "public"."{asset}"'
    dat = pd.read_sql(query, stream)
    print(dat)
    dat.set_index('dateTime', inplace=True)
    logger.info(f"Initial Asset {asset} loaded with {len(dat[asset])} rows.")
    dat_hist = dat[dat['Symbol'] == asset + INTERVALS]
    logger.info(f"Initial Asset {asset} loaded with {len(dat_hist[asset])} rows.")
    dat_hist = dat_preprocess(dat_hist)
    logger.info(f"Initial Asset {asset} loaded with {len(dat_hist[asset])} rows.")
    data_dict[asset] = dat_hist
    logger.info(f"Historical data for {asset} loaded successfully.")
    #except Exception as e:
        #logger.error(f"Error loading data for {asset}: {e}")
        #data_dict[asset] = pd.DataFrame({'Date': [], 'Price': []})

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Trading Bot Dashboard"), className="text-center mb-4")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='asset-dropdown',
                options=[{'label': asset, 'value': asset} for asset in ASSET_LIST],
                value=ASSET_LIST[0],
                clearable=False
            ),
            dcc.Graph(id='price-chart')
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Button('Start Trading Bot', id='start-bot-button', n_clicks=0),
            html.Button('Stop Trading Bot', id='stop-bot-button', n_clicks=0),
            dcc.Textarea(id='log-textarea',
                         value='',
                         style={'width': '100%', 'height': 200},
                         readOnly=True
                         )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Interval(
                id='interval-component',
                interval=1000*60*15,  # in milliseconds (updates every 15 minutes)
                n_intervals=0
            )
        ])
    ])
])

@app.callback(
    Output('price-chart', 'figure'),
    [Input('asset-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)

def update_graph(selected_asset, n_intervals):
    try:
        data_dict = {}
        query = f'SELECT * FROM "public"."{selected_asset}"'
        dat = pd.read_sql(query, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == selected_asset + INTERVALS]
        dat_hist1 = dat_preprocess(dat_hist)
        data_dict[selected_asset] = dat_hist1
        #logger.info(f"Asset {selected_asset} loaded with {len(data_dict[selected_asset])} rows.")
    except Exception as e:
        print(f"Data not yet available: {e}")
    try:
        df = data_dict[selected_asset]
        #print(df)
        if df.empty:
            figure = {'data': [],
                      'layout': go.Layout(title=f'No Data for {selected_asset}', xaxis={'title': 'Date'},
                                          yaxis={'title': 'Price'})
            }
        else:
            figure = {
                'data': [go.Scatter(x=df['dateTime'], y=df['close'], mode='lines')],
                'layout': go.Layout(title=f'Price Over Time: {selected_asset}', xaxis={'title': 'Date'}, yaxis={'title': 'Price'})
            }
    except Exception as e:
        logger.error(f"Error updating graph for {selected_asset}: {e}")
        figure = {'data': [],
                  'layout': go.Layout(title=f'Error loading data for {selected_asset}', xaxis={'title': 'Date'},
                                          yaxis={'title': 'Price'})
        }
    return figure

@app.callback(
    Output('log-textarea', 'value'),
    [Input('start-bot-button', 'n_clicks'),
     Input('stop-bot-button', 'n_clicks')],
    [State('log-textarea', 'value')]
)
def run_trading_bot(start_bot_clicks, stop_bot_clicks, log_value):
    global trading_thread
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if log_value is None:
        log_value = ''

    if trigger == 'start-bot-button' and start_bot_clicks > 0:
        if trading_thread is None or not trading_thread.is_alive():
            trading_thread = Thread(target=start_trading_bot, daemon=True)
            trading_thread.start()
            log_value += '\nTrading bot started.'
        else:
            log_value += '\nTrading bot is already running.'

    elif trigger == 'stop-bot-button' and stop_bot_clicks > 0:
        if trading_thread and trading_thread.is_alive():
            stop_trading_bot()
            trading_thread.join()  # Wait for the thread to terminate
            trading_thread = None
            log_value += '\nTrading bot stopped.'
        else:
            log_value += '\nTrading bot is not running.'
    return log_value

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=10000)