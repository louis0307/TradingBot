import os

from config import INTERVALS, ASSET_LIST
from data.db_connection import stream
from data.preprocessing import dat_preprocess
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
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

# Layout of the dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Trading Bot Dashboard"), className="text-center mb-4")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
        ])
    ])
])

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
                interval=60*1000,  # in milliseconds (here, it updates every minute)
                n_intervals=0
        )])
    ])
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        if current_user.is_authenticated:
            return dashboard_layout
        else:
            return login_layout
    elif pathname == '/logout':
        logout_user()
        return login_layout
    return login_layout

@app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [Input('username', 'value'), Input('password', 'value')]
)
def update_output(n_clicks, username, password):
    if n_clicks > 0:
        if username in users and users[username] == password:
            user = User(username)
            login_user(user)
            return dcc.Location(pathname='/', id='redirect')
        else:
            return 'Invalid username or password'
    return ''

@app.callback(
    Output('page-content', 'children'),
    [Input('logout-button', 'n_clicks')]
)
def logout(n_clicks):
    if n_clicks > 0:
        logout_user()
        return dcc.Location(pathname='/', id='redirect')
    return dashboard_layout

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