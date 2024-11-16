import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import pytz
import os
import time
import yaml

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, timezone
from dash import Dash, html, dcc, Input, Output, callback
from cftc_analyser import CFTCDataAnalyzer
from zip_checker import CFTCDataDownloader
from plotly.subplots import make_subplots


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Update the date display in the title daily at midnight CET
def milliseconds_until_midnight_cet():
    cet = pytz.timezone('CET')
    now = datetime.now(tz=cet)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = next_midnight - now
    return int(delta.total_seconds() * 1000)

server = app.server

CFTC = CFTCDataAnalyzer()
CFTC_D = CFTCDataDownloader()

three_years_ago = datetime.now() - relativedelta(years=3)
one_year_ago = datetime.now() - relativedelta(years=1)
three_months_ago = datetime.now() - relativedelta(months=3)
six_months_ago = datetime.now() - relativedelta(months=6)
name_list, date_list, interest_list, non_comm_long_list, non_comm_short_list, comm_long_list, comm_short_list  = CFTC.getLists()
cftc_df_non_comm, cftc_metrics_non_comm, n_entries_non_comm = CFTC.get_cftc_dataframe(name_list, date_list, non_comm_long_list, non_comm_short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago)
cftc_df_comm, cftc_metrics_comm, n_entries_comm = CFTC.get_cftc_dataframe(name_list, date_list, comm_long_list, comm_short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago)

# Dash callback to update the date in the title daily
@app.callback(
    Output("date-display", "children"),
    Input("daily-interval", "n_intervals")
)
def update_date(n):
    cet = pytz.timezone("CET")
    current_date = datetime.now(cet).strftime('%Y-%m-%d')
    return f"CFTC Analysis {current_date}"

# Dash callback to update the date in the title daily
@app.callback(
    Output("date-display-non-comm", "children"),
    Input("daily-interval-non-comm", "n_intervals")
)
def update_date(n):
    cet = pytz.timezone("CET")
    current_date = datetime.now(cet).strftime('%Y-%m-%d')
    return f"Non-commercial Positioning {current_date}"

@app.callback(
    Output('cftc_datatable_non_comm', 'children'),
    [Input('cftc_input_df', 'value')]
)
def get_CFTC_df_selection(value):
    return dbc.Table.from_dataframe(
        cftc_df_non_comm.loc[value, :],
        bordered=True)

@app.callback(
    Output('cftc_graph', 'figure'),
    [Input('cftc_input', 'value')]
)
def create_z_score_plot(value):
    num_of_entries = len(name_list)
    weeks = []
    for i in range(0,156):
        weeks.append(datetime.now() - relativedelta(weeks=i))
    weeks.reverse()
    with open("res/metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)

    for asset_class in metrics:
        for metric in metrics[asset_class]:
            if metric == value:
                list_of_i_and_date = CFTC.get_list_of_i_and_date_for_metric(metrics[asset_class][metric], date_list, name_list)

    diff_non_comm = [(a - b) for a, b in zip(non_comm_long_list, non_comm_short_list)]
    z_score_list_one_year_non_comm = CFTC.get_list_of_z_scores(list_of_i_and_date, 1, diff_non_comm)
    z_score_list_three_year_non_comm = CFTC.get_list_of_z_scores(list_of_i_and_date, 3, diff_non_comm)
    z_score_list_one_year_non_comm.reverse()
    z_score_list_three_year_non_comm.reverse()

    diff_comm = [(a - b) for a, b in zip(comm_long_list, comm_short_list)]
    z_score_list_one_year_comm = CFTC.get_list_of_z_scores(list_of_i_and_date, 1, diff_comm)
    z_score_list_three_year_comm = CFTC.get_list_of_z_scores(list_of_i_and_date, 3, diff_comm)
    z_score_list_one_year_comm.reverse()
    z_score_list_three_year_comm.reverse()

    z_score_list_one_year_open_interest = CFTC.get_list_of_z_scores(list_of_i_and_date, 1, interest_list)
    z_score_list_three_year_open_interest = CFTC.get_list_of_z_scores(list_of_i_and_date, 3, interest_list)
    z_score_list_one_year_open_interest.reverse()
    z_score_list_three_year_open_interest.reverse()

    non_comm_net_positioning_list = CFTC.get_list_of_net_positioning(list_of_i_and_date, three_years_ago, diff_non_comm)
    comm_net_positioning_list = CFTC.get_list_of_net_positioning(list_of_i_and_date, three_years_ago, diff_comm)
    net_open_interest_list = CFTC.get_list_of_net_positioning(list_of_i_and_date, three_years_ago, interest_list)
    
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    fig = make_subplots(rows=3, cols=2,
                        subplot_titles=("z-scores non-commercial",
                                        "z-scores commercial",
                                        "net positioning non-commercial",
                                        "net positioning commercial",
                                        "z-scores open interest,",
                                        "open interest"))

    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_non_comm, name='1y (non_comm)', line=dict(color=color_palette[0])),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_non_comm, name='3y (non_comm)', line=dict(color=color_palette[1])),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_comm, name='2y (comm)', line=dict(color=color_palette[0])),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_comm, name='3y (comm)', line=dict(color=color_palette[1])),
                  row=1, col=2)
    fig.add_trace(go.Bar(x=weeks, y=non_comm_net_positioning_list, name="net Pos (non_comm)", marker_color=color_palette[2]),
                  row=2, col=1)
    fig.add_trace(go.Bar(x=weeks, y=comm_net_positioning_list, name="net Pos (comm)", marker_color=color_palette[2]),
                  row=2, col=2)
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_open_interest, name='1y (OI)', line=dict(color=color_palette[0])),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_open_interest, name='3y (OI)', line=dict(color=color_palette[1])),
                  row=3, col=1)
    fig.add_trace(go.Bar(x=weeks, y=net_open_interest_list, name="OI", marker_color=color_palette[2]),
                  row=3, col=2)

    fig.update_xaxes(title_text="date")
    fig.update_yaxes(title_text="z_score", row=1, col=1)
    fig.update_yaxes(title_text="z_score", row=1, col=2)
    fig.update_yaxes(title_text="net contracts", row=2, col=1)
    fig.update_yaxes(title_text="net_contracts", row=2, col=2)
    fig.update_yaxes(title_text="z_score", row=3, col=1)
    fig.update_yaxes(title_text="net_contracts", row=3, col=2)

    fig.update_layout(
        xaxis_title="date",
        yaxis_title="z-score",
        template="plotly_white",
        showlegend=True,
        legend=dict(orientation="h"),
        height=1200,
        width=1450,
    )
    return fig

@app.callback(
    Output('cftc_positioning', 'children'),
    [Input('cftc_input', 'value')]
)
def get_cftc_positioning(value):
    num_of_entries = len(name_list)
    weeks = []
    for i in range(0, 156):
        weeks.append(datetime.now() - relativedelta(weeks=i))
    weeks.reverse()
    with open("res/metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)

    df = pd.DataFrame()
    done = False
    for asset_class in metrics:
        for metric in metrics[asset_class]:
            if metric == value:
                list_of_i_and_date = CFTC.get_list_of_i_and_date_for_metric(metrics[asset_class][metric], date_list, name_list)

                investor = 'Open interest'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, z_score_three_years = CFTC.get_values(
                    list_of_i_and_date, interest_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago,)
                df[investor] = [investor, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg, maximum, minimum, z_score_one_year, z_score_three_years]

                investor = 'Non_commercial'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
                z_score_three_years = CFTC.get_values(list_of_i_and_date, non_comm_long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, non_comm_short_list)

                df[investor] = [investor, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg, maximum, minimum, z_score_one_year, z_score_three_years]

                investor = 'Commercial'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
                z_score_three_years = CFTC.get_values(list_of_i_and_date, comm_long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, comm_short_list)

                df[investor] = [investor, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg, maximum, minimum, z_score_one_year, z_score_three_years]
                done = True
                break
        if done:
            break

    df = df.T
    df.columns = ['class', 'latest', 'w/w change', '3m ave', '6m ave', '1y ave', '3y ave', '3y max', '3y min', '1y zscore', '3y zscore']
    for column in df.iloc[:, 1:]:
        df[column] = df[column].astype(float)
    return dbc.Table.from_dataframe(
        df.round(2), bordered=True)

graphs_layout = html.Div([
    dbc.Container([
        # Date Display and Latest Update
        html.H2(id='date-display', style={'textAlign': 'center', "text-decoration": "underline"}),
        html.P(f"Latest update: {CFTC_D.latest_update_timestamp}", style={'textAlign': 'center', 'fontSize': 'small'}),
        dcc.Interval(id="daily-interval", interval=milliseconds_until_midnight_cet(), n_intervals=0),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dcc.Loading(
                    type="circle",
                    children=[
                        dcc.Dropdown(
                            id='cftc_input',
                            options=[{'label': x, 'value': x} for x in cftc_metrics_non_comm],
                            value='SPX',
                            placeholder='Select security',
                            multi=False,
                            style={'textAlign': 'center'}
                        )
                    ]
                )
            ])
        ], width={'size': 8, 'offset': 2})
    ], align='center'),

    html.Br(),

    # Row for CFTC positioning table for selected base ticker
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                type="circle",
                children=[
                    html.Div(id='cftc_positioning')
                ],
                style={"textAlign": "center"}
            )
        ], width={'size': 8, 'offset': 2})  # Centering the column
    ], align='center'),

    # Row for the CFTC graph
    dbc.Row(
        dbc.Col(
            dcc.Loading(
                type="circle",
                children=[dcc.Graph(id='cftc_graph')]
            ),
            width=12,  # Full width column
            style={"display": "flex", "justifyContent": "center"}  # Centering the graph
        ),
        align='center',
    )
])

datatable_layout = html.Div([
    dbc.Container([
        html.H2(id='date-display-non-comm', style={'textAlign': 'center', "text-decoration": "underline"}),
        html.P(f"Latest update: {CFTC_D.latest_update_timestamp}", style={'textAlign': 'center', 'fontSize': 'small'}),
        dcc.Interval(id="daily-interval-non-comm", interval=milliseconds_until_midnight_cet(), n_intervals=0),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dcc.Loading(
                    type="circle",
                    children=[
                        dcc.Dropdown(
                            id='cftc_input_df',
                            options=[{'label': x, 'value': x} for x in CFTC.get_asset_lists()],
                            value=CFTC.get_asset_lists(),
                            placeholder='Select security',
                            multi=True,
                            style={'textAlign': 'center'}
                        )
                    ])
                ])
        ], width={'size': 8, 'offset': 2})  # Centering the column
    ], align='center'),

    html.Br(),

    dbc.Row([
        dbc.Col([
            dcc.Loading(
                type="circle",
                children=[
                    html.Div(id='cftc_datatable_non_comm')
                ],
                style={"textAlign": "center"}
            )], width={'size': 8, 'offset': 2})  # Centering the column
    ], align='center')
])


sidebar = html.Div(
    [
        html.H2("CFTC Report", className="display-4"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Graphs", href="/graphs", id="graphs-link", active="exact"),
                dbc.NavLink("Datatable", href="/datatable", id="datatable-link", active="exact")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    },
)

content = html.Div(id="page-content", style={"margin-left": "18rem", "padding": "2rem 1rem"})

# Main layout with navigation
app.layout = html.Div([dcc.Location(id='url', refresh=False), sidebar, content])

# Callback to control page navigation
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/datatable':
        return datatable_layout
    elif pathname == '/graphs'or pathname is None or pathname == '/':
        return graphs_layout
    else:
        return graphs_layout 

# Callback to update active state of navigation links
@app.callback(
    [Output('graphs-link', 'active'), Output('datatable-link', 'active')],
    Input('url', 'pathname')
)
def update_active_links(pathname):
    return pathname == '/graphs' or pathname == '/' or pathname is None, pathname == '/datatable'

