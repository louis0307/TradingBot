import os

from config import INTERVALS, ASSET_LIST
from data.db_connection import stream
from data.preprocessing import dat_preprocess
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from flask import Flask, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Flask-Login setup
secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

server.secret_key = secret_key
login_manager = LoginManager()
login_manager.init_app(server)

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
users = {username: password}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# load data for illustration purposes
data_dict = {asset: pd.DataFrame({'Date': [], 'Price': []}) for asset in ASSET_LIST}

login_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Please Log In"), className="text-center mb-4")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='username', type='text', placeholder='Username'),
            dcc.Input(id='password', type='password', placeholder='Password'),
            html.Button('Login', id='login-button', n_clicks=0),
            html.Div(id='login-output', style={'color': 'red'})
        ], width=12)
    ])
])

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
            html.Button('Logout', id='logout-button', n_clicks=0)
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Interval(
                id='interval-component',
                interval=60*200,  # in milliseconds (here, it updates every minute)
                n_intervals=0
            )
        ])
    ])
])

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content'),
    dcc.Input(id='username', type='text', placeholder='Username', style={'display': 'none'}),
    dcc.Input(id='password', type='password', placeholder='Password', style={'display': 'none'}),
    html.Button('Login', id='login-button', n_clicks=0, style={'display': 'none'}),
    html.Button('Logout', id='logout-button', n_clicks=0, style={'display': 'none'})
])
@app.callback(
    [Output('page-content', 'children'),
     Output('login-output', 'children')],
    [Input('url', 'pathname'),
     Input('login-button', 'n_clicks'),
     Input('logout-button', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')]
)
def display_page(pathname, login_clicks, logout_clicks, username, password):
    ctx = dash.callback_context

    # Initialize content and message
    content = login_layout
    message = ''

    # Determine which button was clicked
    if ctx.triggered:
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger == 'login-button' and login_clicks > 0:
            print(f"Login attempt with username: {username} and password: {password}")
            if username in users and users[username] == password:
                user = User(username)
                login_user(user)
                print("Login successful")
                content = dashboard_layout
                message = dcc.Location(pathname='/', id='redirect')
            else:
                print("Login failed")
                message = 'Invalid username or password'

        elif trigger == 'logout-button' and logout_clicks > 0:
            logout_user()
            print("Logout successful")
            content = login_layout

    if current_user.is_authenticated and (pathname == '/' or pathname == '/login'):
        print("User is authenticated, showing dashboard")
        content = dashboard_layout

    print(f"Content: {content}, Message: {message}")
    return content, message

# Callback to update the chart based on selected asset
@app.callback(
    Output('price-chart', 'figure'),
    [Input('asset-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graph(selected_asset, n_intervals):
    try:
        dat = pd.read_sql(selected_asset, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == selected_asset + INTERVALS]
        dat_hist = dat_preprocess(dat_hist)
        data_dict[selected_asset] = dat_hist
    except Exception as e:
        print(f"Data not yet available: {e}")
    df = data_dict[selected_asset]
    if df.empty:
        figure = {'data': [],
                  'layout': go.Layout(title=f'No Data for {selected_asset}', xaxis={'title': 'Date'},
                                      yaxis={'title': 'Price'})
        }
    else:
        new_price = df['close'].iloc[-1]
        new_row = pd.DataFrame({'Date': [df['dateTime'].iloc[-1] + pd.Timedelta(minutes=15)], 'Price': [new_price]})
        data_dict[selected_asset] = pd.concat([df, new_row], ignore_index=True)
        figure = {
            'data': [go.Scatter(x=data_dict[selected_asset]['dateTime'], y=data_dict[selected_asset]['close'], mode='lines')],
            'layout': go.Layout(title=f'Price Over Time: {selected_asset}', xaxis={'title': 'Date'}, yaxis={'title': 'Price'})
        }
    return figure

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=10000)