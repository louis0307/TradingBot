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

bot_thread = None
bot_running = False

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
dash_authentication = BasicAuth(server, '/login', '/dashboard', secret_key)

server.secret_key = secret_key
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
users = {username: password}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['POST'])
def login():
    usr = request.form['username']
    pwd = request.form['password']
    if username == usr and password == pwd:
        user = User(usr)
        login_user(user)
        return redirect('/dashboard')
    return 'Invalid credentials', 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    return 'Welcome to the dashboard!'

# Load complete history for each asset at startup
data_dict = {}
for asset in ASSET_LIST:
    try:
        query = f'SELECT * FROM public."{asset}"'
        dat = pd.read_sql(query, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == asset + INTERVALS]
        dat_hist = dat_preprocess(dat_hist)
        data_dict[asset] = dat_hist
        logger.info(f"Historical data for {asset} loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading data for {asset}: {e}")
        data_dict[asset] = pd.DataFrame({'Date': [], 'Price': []})


#login_layout = dbc.Container([
#    dbc.Row([
#        dbc.Col(html.H2("Please Log In"), className="text-center mb-4")
#    ]),
#    dbc.Row([
#        dbc.Col([
#            dcc.Input(id='username', type='text', placeholder='Username'),
#            dcc.Input(id='password', type='password', placeholder='Password'),
#            html.Button('Login', id='login-button', n_clicks=0),
#            html.Div(id='login-output', style={'color': 'red'})
#        ], width=12)
#    ])
#])

dashboard_layout = dbc.Container([
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
#    dbc.Row([
#        dbc.Col([
#            html.Button('Logout', id='logout-button', n_clicks=0)
#        ])
#    ]),
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

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content'),
#    dcc.Input(id='username', type='text', placeholder='Username', style={'display': 'none'}),
#    dcc.Input(id='password', type='password', placeholder='Password', style={'display': 'none'}),
#    html.Button('Login', id='login-button', n_clicks=0, style={'display': 'none'}),
#    html.Button('Logout', id='logout-button', n_clicks=0, style={'display': 'none'}),
    html.Button('Start Tradingbot', id='start-bot-button', n_clicks=0, style={'display': 'none'}),
    html.Button('Stop Tradingbot', id='stop-bot-button', n_clicks=0, style={'display': 'none'}),
    #html.Div(id='login-output', style={'display': 'none'}),
    dcc.Textarea(id='log-textarea', value='', style={'width': '100%', 'height': 200, 'display': 'none'}, readOnly=True)
])

@app.callback(
    [Output('page-content', 'children'),
#     Output('login-output', 'children'),
     Output('log-textarea', 'value')],
    [Input('url', 'pathname'),
#     Input('login-button', 'n_clicks'),
#     Input('logout-button', 'n_clicks'),
     Input('start-bot-button', 'n_clicks'),
     Input('stop-bot-button', 'n_clicks')],
    [#State('username', 'value'),
     #State('password', 'value'),
     State('log-textarea', 'value')]
)
#def display_page(pathname, login_clicks, logout_clicks, start_bot_clicks , username, password, stop_bot_clicks, log_value):
    # global bot_thread, bot_running
#    ctx = dash.callback_context
#    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Initialize content and message
    #content = login_layout
    #message = ''
    #log_update = log_value

    # Determine which button was clicked
    #if not ctx.triggered:
    #    raise PreventUpdate

    #trigger = ctx.triggered[0]['prop_id'].split('.')[0]

#    if trigger == 'login-button' and login_clicks > 0:
#        print(f"Login attempt with username: {username} and password: {password}")
#        if username in users and users[username] == password:
#            user = User(username)
#            login_user(user)
#            print("Login successful")
#            content = dashboard_layout
#            message = dcc.Location(pathname='/', id='redirect')
#        else:
#            print("Login failed")
#            message = 'Invalid username or password'

#    elif trigger == 'logout-button' and logout_clicks > 0:
#        logout_user()
#        print("Logout successful")
#        content = login_layout
#        log_update += '\nUser logged out.'

#    if current_user.is_authenticated and (pathname == '/' or pathname == '/login'):
#        print("User is authenticated, showing dashboard")
#        content = dashboard_layout
#    else:
#        if pathname == '/':
#            content = login_layout
#    print(f"Content: {content}, Message: {message}")
#    return content, message, log_update

# Callback to update the chart based on selected asset
@app.callback(
    Output('price-chart', 'figure'),
    [Input('asset-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graph(selected_asset, n_intervals):
    try:
        query = f'SELECT * FROM public."{selected_asset}"'
        dat = pd.read_sql(query, stream)
        dat.set_index('dateTime', inplace=True)
        logger.info(f"Asset {selected_asset} loaded with {len(dat)} rows.")
        dat_hist = dat[dat['Symbol'] == selected_asset + INTERVALS]
        dat_hist = dat_preprocess(dat_hist)
        data_dict[selected_asset] = dat_hist
        logger.info(f"Asset {selected_asset} loaded with {len(data_dict[selected_asset])} rows.")
    except Exception as e:
        print(f"Data not yet available: {e}")
    try:
        df = data_dict[selected_asset]
        logger.info(f"Asset loaded with {len(df)} rows.")
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