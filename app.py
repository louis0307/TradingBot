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

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# load data for illustration purposes
data_dict = {asset: pd.DataFrame({'Date': [], 'Price': []}) for asset in ASSET_LIST}

# Layout of the dashboard
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
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # in milliseconds (here, it updates every minute)
                n_intervals=0
            )
        ])
    ])
])

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