from config import INTERVALS, ASSET_LIST
from data.db_connection import stream
from data.preprocessing import dat_preprocess
from misc.logger_config import logger
from main import start_trading_bot, stop_trading_bot
from misc.global_state import trading_thread
from misc.portfolio_value import calc_pv
from data.stats import calc_pv_total
from data.stats import compute_trade_stats

import os
import signal
import dash
from dash import dash_table
import sys
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from flask import Flask, redirect, url_for, request, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from threading import Thread
import dash_auth
from dash_auth import BasicAuth
from plotly.subplots import make_subplots


logger.info("Starting the web application")

# Flask-Login setup
secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
#dash_authentication = BasicAuth(server, '/login', '/dashboard', secret_key)

server.secret_key = secret_key
if not server.secret_key:
    raise ValueError("No SECRET_KEY set for Flask application.")
@server.before_request
def enforce_https():
    if request.path == '/health':
        return # skip authentication for health check
    if not request.is_secure and request.headers.get("X-Forwarded-Proto", "http") != "https": # X-Forwarded-Proto is there to deal with the fact that in Render reverse proxy/load balancer is used
                                                                                              # and that nevertheless we can see whether the request is http or https
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code = 301)

users = {username: password}
auth = dash_auth.BasicAuth(app, users)

def handle_shutdown(signal, frame):
    logger.info("Shutting down gracefully...")
    stop_trading_bot()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

@server.route("/health")
def health_check():
    return 'OK', 200

# Load complete history for each asset at startup
data_dict = {}
for asset in ASSET_LIST:
    try:
        query = f'SELECT * FROM "public"."{asset}"'
        dat = pd.read_sql(query, stream)
        dat.set_index('dateTime', inplace=True)
        dat_hist = dat[dat['Symbol'] == asset + INTERVALS]
        dat_hist = dat_preprocess(dat_hist)
        data_dict[asset] = dat_hist
        logger.info(f"Historical data for {asset} loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading data for {asset}: {e}")
        data_dict[asset] = pd.DataFrame({'Date': [], 'Price': []})

card_style = {
    "textAlign": "center",
    "padding": "1rem",
    "backgroundColor": "#0d1b2a",  # Dark navy blue
    "color": "#f8f9fa",  # Light text
    "borderRadius": "12px",
    "boxShadow": "0 4px 10px rgba(0, 0, 0, 0.3)"
}

def create_tile(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title", style={"color": "#adb5bd"}),  # muted text
            html.H2(value, className="card-text", style={"fontWeight": "bold"})
        ]),
        style=card_style
    )

app.layout = dbc.Container([
    dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Img(src="/assets/logo.png", height="55px"), width="auto"),  # Add your logo
                dbc.Col(html.H2("Trading Bot Dashboard", className="text-white ms-3",
                                style={"fontWeight": "bold", "margin": 0}), width="auto")
            ], align="center", className="g-0"),
        ]),
        color="#0d1b2a",
        dark=True,
        fixed="top",
        className="mb-4",
        style={
            "height": "80px",          # total navbar height
            "paddingTop": "10px",      # spacing inside
            "paddingBottom": "50px"
        }
    ),
    dbc.Row([
        dbc.Col(create_tile("Cash", "$12,500"), md=4, lg=2),
        dbc.Col(create_tile("Crypto", "$7,200"), md=4, lg=2),
        dbc.Col(create_tile("Stocks", "$14,000"), md=4, lg=2),
        dbc.Col(create_tile("ETF", "$8,750"), md=4, lg=2),
        dbc.Col(create_tile("Total", "$42,450"), md=4, lg=2),
    ], className="g-4 justify-content-center"),
    dbc.Row([
        html.Div(id="pv-total-display", style={
            "marginTop": "160px",
            "textAlign": "center",
            "fontSize": "20px",
            "marginBottom": "20px",
            "fontWeight": "bold",
            "border": "2px solid #ccc",
            "borderRadius": "10px",
            "padding": "10px",
            "width": "30%",
            "margin": "30px auto 30px auto",
            "boxShadow": "0 4px 8px rgba(181, 179, 179, 0.3)",
            "backgroundColor": "#1e2f4f",  # deeper blue for card
            "color": "white",
        })
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(
                "Total Portfolio Value Over Time",
                id="title-pv-chart",
                style={
                    "textAlign": "center",
                    "fontSize": "24px",
                    "fontWeight": "bold",
                    "color": "#ffffff",
                    "border": "2px solid #ccc",
                    "borderRadius": "3px",
                    "padding": "15px 20px",
                    "width": "auto",
                    "margin": "0 auto 30px auto",  # top: 0, right: auto, bottom: 30px, left: auto
                    "backgroundColor": "#2e2e2e",
                    "boxShadow": "0 6px 12px rgba(181, 179, 179, 0.3)",
                }
            ),
            dcc.Graph(id='total-pv-chart')
        ], width=12)
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
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(
                "Table of Trades",
                id="title-table-trades",
                style={
                    "textAlign": "center",
                    "fontSize": "24px",
                    "fontWeight": "bold",
                    "color": "#ffffff",
                    "border": "2px solid #ccc",
                    "borderRadius": "3px",
                    "padding": "15px 20px",
                    "width": "auto",
                    "margin": "0 auto 30px auto",  # top: 0, right: auto, bottom: 30px, left: auto
                    "backgroundColor": "#2e2e2e",
                    "boxShadow": "0 6px 12px rgba(181, 179, 179, 0.3)",
                }
            ),
            html.Div(id='table'),
            html.Div(id='table-stats')
        ], width=12),
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
                interval=1000*60,  # in milliseconds
                n_intervals=0
            ),
            dcc.Interval(
                id='interval-pv',
                interval=1000*60,  # in milliseconds
                n_intervals=0
            )
        ])
    ])
],
fluid=True,
style={
    "backgroundColor": "#0b1d3a",  # dark blue
    "minHeight": "100vh",          # full height
    "padding": "20px"
})

@app.callback(
    [Output('total-pv-chart', 'figure'),
     Output('pv-total-display', 'children')],
    Input('interval-pv', 'n_intervals')
)
def update_total_pv_chart(n_intervals):
    try:
        pvs_all = pd.read_sql('SELECT * FROM "public"."PORTFOLIO_VALUES"', stream)
        pvs_all["timestamp"] = pd.to_datetime(pvs_all["timestamp"])
        pvs_all = pvs_all.sort_values("timestamp")

        pv_total = calc_pv_total()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pv_total["timestamp"],
            y=pv_total["portfolio_value"],
            mode="lines",
            name="Total PV",
            line=dict(width=2),
            yaxis="y1"
        ))

        colors = px.colors.qualitative.Plotly

        for i, symbol in enumerate(pvs_all["symbol"].unique()):
            df_symbol = pvs_all[pvs_all["symbol"] == symbol]
            fig.add_trace(go.Scatter(
                x=df_symbol["timestamp"],
                y=df_symbol["portfolio_value"],
                mode="lines",
                name=symbol,
                line=dict(width=1, color=colors[i % len(colors)]),
                yaxis="y2",
                hovertemplate=f"Symbol: {symbol}<br>Time: %{{x}}<br>Value: %{{y}}<extra></extra>",
                opacity=0.8
            ))

        fig.update_layout(
            title="",
            xaxis_title="Time",
            template='plotly_dark',
            yaxis=dict(title="Total Portfolio Value", side="left", showgrid=True),
            yaxis2=dict(title="Individual Symbol Value", overlaying="y", side="right", showgrid=False),
            legend_title="Legend"
        )

        total_pv_display = ""
        if not pv_total.empty:
            current_total_pv = pv_total["portfolio_value"].iloc[-1]
            total_pv_display = f"Current Total Portfolio Return: ${current_total_pv:,.2f}"
        return fig, total_pv_display
    except Exception as e:
        logger.error(f"Error updating total portfolio chart: {e}")
        return go.Figure(), "Error loading total portfolio value"

@app.callback(
    [Output('price-chart', 'figure'),
     Output('table', 'children'),
     Output('table-stats', 'children')],
    [Input('asset-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)

def update_graphs(selected_asset, n_intervals):
    try:
        dat_dict = {}
        trades = {}
        query = f'SELECT * FROM "public"."{selected_asset}"'
        query2 = 'SELECT * FROM "public"."TRADES"'
        query3 = 'SELECT * FROM "public"."INDICATORS"'
        query4 = 'SELECT * FROM "public"."WINS_LOSSES"'

        dat = pd.read_sql(query, stream)
        dat.set_index('dateTime', inplace=True)

        dat2 = pd.read_sql(query2, stream)
        dat_hist = dat[dat['Symbol'] == selected_asset + INTERVALS]
        dat_hist2 = dat2[dat2['symbol'] == selected_asset]

        dat_hist1 = dat_preprocess(dat_hist)
        dat_dict[selected_asset] = dat_hist1
        trades[selected_asset] = dat_hist2
        dat_ind = pd.read_sql(query3, stream)
        dat_ind.set_index('dateTime', inplace=True)
        dat_ind_hist = dat_ind[dat_ind['Symbol'] == selected_asset+'1h']
        dat_ind_hist = dat_ind_hist.sort_index()

        dat4 = pd.read_sql(query4, stream)
        trade_stats = dat4[dat4['symbol'] == selected_asset]
        trade_stats.set_index('timestamp', inplace=True)
        trade_stats = trade_stats.sort_index()
        trade_stats_asset = compute_trade_stats(trade_stats)

    except Exception as e:
        print(f"Data not yet available: {e}")
    try:
        df = dat_dict[selected_asset]
        df = df.sort_index()
        tab = trades[selected_asset]
        tab["order_timestamp"] = pd.to_datetime(tab["order_timestamp"])
        tab = tab.sort_values(by='order_timestamp')

        if df.empty:
            figure = {'data': [],
                      'layout': go.Layout(title=f'No Data for {selected_asset}', xaxis={'title': 'Date'},
                                          yaxis={'title': 'Price'})
            }

            table_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close'])
            table = dash_table.DataTable(
                id='table',
                columns=[{'name': col, 'id': col} for col in table_data.columns],
                data=table_data.to_dict('records'),
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center', 'backgroundColor': '#132743', 'color': 'white'},
                style_header={
                    'backgroundColor': '#1a2a45',
                    'fontWeight': 'bold',
                    'color': 'white'
                }
            )
        else:
            figure = make_subplots(
                rows=3, cols=1,  # Two rows, one column
                shared_xaxes=True,  # Sync x-axes
                row_heights=[0.6, 0.2, 0.2],  # Adjust row height ratio
                vertical_spacing=0.1  # Space between plots
            )
            figure.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color='green',  # Optional, color for increasing candles
                    decreasing_line_color='red'  # Optional, color for decreasing candles
                ),
                row=1, col=1
            )
            figure.add_trace(
                go.Scatter(x=dat_ind_hist.index, y=dat_ind_hist["MACD"], mode="lines", name="MACD",
                           line=dict(color="blue", width=0.8)),
                row=2, col=1
            )

            # Add MACD Signal Line (Second Row)
            figure.add_trace(
                go.Scatter(x=dat_ind_hist.index, y=dat_ind_hist["MACD_Signal"], mode="lines", name="MACD Signal",
                           line=dict(color="red", width=0.8)),
                row=2, col=1
            )

            # Add MACD Histogram as Bars (Second Row)
            figure.add_trace(
                go.Bar(x=dat_ind_hist.index, y=dat_ind_hist["MACD_Hist"], name="MACD Histogram",
                       marker=dict(color="white")),
                row=2, col=1
            )

            figure.add_trace(
                go.Scatter(x=dat_ind_hist.index, y=dat_ind_hist["K"], mode="lines", name="K",
                           line=dict(color="blue", width=0.8)),
                row=3, col=1
            )
            figure.add_trace(
                go.Scatter(x=dat_ind_hist.index, y=dat_ind_hist["D"], mode="lines", name="D",
                           line=dict(color="green", width=0.8)),
                row=3, col=1
            )
            figure.add_trace(
                go.Scatter(x=dat_ind_hist.index, y=dat_ind_hist["J"], mode="lines", name="J",
                           line=dict(color="red", width=0.8)),
                row=3, col=1
            )

            figure.update_yaxes(range=[dat_ind_hist["MACD"].min() * 1.2, dat_ind_hist["MACD"].max() * 1.2], row=2,
                                col=1)
            figure.update_layout(
                title=f'Candlestick Chart for {selected_asset} with MACD and KDJ Indicator',
                xaxis=dict(rangeslider=dict(visible=False)),
                xaxis_title='Date',
                yaxis_title='Price',
                height=800,
                template='plotly_dark',
                legend=dict(
                    orientation='h',  # Horizontal legend
                    yanchor='bottom',
                    y=-0.3,  # Move below the chart
                    xanchor='center',
                    x=0.5  # Center it horizontally
                )
            )

            table = dash_table.DataTable(
                id='asset-table',
                columns=[{'name': col, 'id': col} for col in tab.columns],
                data=tab.to_dict('records'),
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center', 'backgroundColor': '#132743', 'color': 'white'},
                style_header={
                    'backgroundColor': '#1a2a45',
                    'fontWeight': 'bold',
                    'color': 'white'
                }
            )

            table_stats = dash_table.DataTable(
                id='stats-table',
                columns=[{'name': col, 'id': col} for col in ['Metric', 'Value']],
                data=trade_stats_asset.to_dict('records'),
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center', 'backgroundColor': '#132743', 'color': 'white'},
                style_header={
                    'backgroundColor': '#1a2a45',
                    'fontWeight': 'bold',
                    'color': 'white'
                }
            )
    except Exception as e:
        logger.error(f"Error updating graph for {selected_asset}: {e}")

        figure = {'data': [],
                  'layout': go.Layout(title=f'Error loading data for {selected_asset}', xaxis={'title': 'Date'},
                                          yaxis={'title': 'Price'})
        }

        table_data = pd.DataFrame(columns=['Error'])
        table_data = pd.concat([table_data, {'Error': 'Failed to load data for the selected asset'}], ignore_index=True)
        table = dash_table.DataTable(
            id='asset-table',
            columns=[{'name': col, 'id': col} for col in table_data.columns],
            data=table_data.to_dict('records'),
            style_table={'height': '400px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'backgroundColor': '#132743', 'color': 'white'},
            style_header={
                'backgroundColor': '#1a2a45',
                'fontWeight': 'bold',
                'color': 'white'
            }
        )
        table_stats = dash_table.DataTable(
            id='asset-table',
            columns=[{'name': col, 'id': col} for col in table_data.columns],
            data=table_data.to_dict('records'),
            style_table={'height': '400px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'backgroundColor': '#132743', 'color': 'white'},
            style_header={
                'backgroundColor': '#1a2a45',
                'fontWeight': 'bold',
                'color': 'white'
            }
        )
    return figure, table, table_stats

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
            trading_thread.join()
            trading_thread = None
            log_value += '\nTrading bot stopped.'
        else:
            log_value += '\nTrading bot is not running.'
    return log_value

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=10000)