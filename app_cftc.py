import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import yaml

from dateutil.relativedelta import relativedelta
from datetime import datetime
from dash import Dash, html, dcc
from cftc_analyser import get_values, get_asset_lists, getLists, get_CFTC_Dataframe, \
    get_list_of_i_and_date_for_metric, get_list_of_z_scores, get_list_of_net_positioning
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots



dash_app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

three_years_ago = datetime.now() - relativedelta(years=3)
one_year_ago = datetime.now() - relativedelta(years=1)
three_months_ago = datetime.now() - relativedelta(months=3)
six_months_ago = datetime.now() - relativedelta(months=6)
name_list, date_list, interest_list, non_comm_long_list, non_comm_short_list, comm_long_list, comm_short_list  = getLists()
cftc_df_non_comm, cftc_metrics_non_comm, n_entries_non_comm = get_CFTC_Dataframe(name_list, date_list, non_comm_long_list, non_comm_short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago)
cftc_df_comm, cftc_metrics_comm, n_entries_comm = get_CFTC_Dataframe(name_list, date_list, comm_long_list, comm_short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago)

@dash_app.callback(
    Output('cftc_datatable_non_comm', 'children'),
    [Input('cftc_submit_df', 'n_clicks')],
    [State('cftc_input_df', 'value')]
)
def get_CFTC_df_selection(n_clicks, MULTP_ASSETS):
    return dbc.Table.from_dataframe(
        cftc_df_non_comm.loc[MULTP_ASSETS, :],
        bordered=True)

@dash_app.callback(
    Output('cftc_datatable_comm', 'children'),
    [Input('cftc_submit_df', 'n_clicks')],
    [State('cftc_input_df', 'value')]
)
def get_CFTC_df_selection(n_clicks, MULTP_ASSETS):
    return dbc.Table.from_dataframe(
        cftc_df_comm.loc[MULTP_ASSETS, :],
        bordered=True)

@dash_app.callback(
    Output('cftc_graph', 'figure'),
    [Input('cftc_submit', 'n_clicks')],
    [State('cftc_input', 'value')]
)
def create_z_score_plot(n_clicks, TICKER):
    num_of_entries = len(name_list)
    weeks = []
    for i in range(0,156):
        weeks.append(datetime.now() - relativedelta(weeks=i))
    weeks.reverse()
    with open("metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)

    for asset_class in metrics:
        for metric in metrics[asset_class]:
            if metric == TICKER:
                list_of_i_and_date = get_list_of_i_and_date_for_metric(metrics[asset_class][metric], num_of_entries, date_list, name_list)

    diff_non_comm = [(a - b) for a, b in zip(non_comm_long_list, non_comm_short_list)]
    z_score_list_one_year_non_comm = get_list_of_z_scores(list_of_i_and_date, 1, diff_non_comm)
    z_score_list_three_year_non_comm = get_list_of_z_scores(list_of_i_and_date, 3, diff_non_comm)
    z_score_list_one_year_non_comm.reverse()
    z_score_list_three_year_non_comm.reverse()

    diff_comm = [(a - b) for a, b in zip(comm_long_list, comm_short_list)]
    z_score_list_one_year_comm = get_list_of_z_scores(list_of_i_and_date, 1, diff_comm)
    z_score_list_three_year_comm = get_list_of_z_scores(list_of_i_and_date, 3, diff_comm)
    z_score_list_one_year_comm.reverse()
    z_score_list_three_year_comm.reverse()

    z_score_list_one_year_open_interest = get_list_of_z_scores(list_of_i_and_date, 1, interest_list)
    z_score_list_three_year_open_interest = get_list_of_z_scores(list_of_i_and_date, 3, interest_list)
    z_score_list_one_year_open_interest.reverse()
    z_score_list_three_year_open_interest.reverse()

    non_comm_net_positioning_list = get_list_of_net_positioning(list_of_i_and_date, three_years_ago, diff_non_comm)
    comm_net_positioning_list = get_list_of_net_positioning(list_of_i_and_date, three_years_ago, diff_comm)
    net_open_interest_list = get_list_of_net_positioning(list_of_i_and_date, three_years_ago, interest_list)

    fig = make_subplots(rows=3, cols=2,
                        subplot_titles=("Z-scores non_comm",
                                        "Z-scores comm",
                                        "Net positioning non_comm",
                                        "Net positioning Comm",
                                        "Z-scores open interest,",
                                        "Open interest"))

    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_non_comm, name='1y (non_comm)'),
                  row=1, col=1,
                  ),
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_non_comm, name='3y (non_comm)'),
                  row=1, col=1
                  )

    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_comm, name='1y (comm)'),
                  row=1, col=2,
                  ),
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_comm, name='3y (comm)'),
                  row=1, col=2
                  )

    fig.add_trace(go.Bar(x=weeks, y=non_comm_net_positioning_list, name="Net Pos (non_comm)"),
                  row=2, col=1
                  )
    fig.add_trace(go.Bar(x=weeks, y=comm_net_positioning_list, name="Net Pos (comm)"),
                  row=2, col=2
                  )

    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_one_year_open_interest, name='1y (OI)'),
                  row=3, col=1,
                  ),
    fig.add_trace(go.Scatter(x=weeks, y=z_score_list_three_year_open_interest, name='3y (OI)'),
                  row=3, col=1,
                  ),
    fig.add_trace(go.Bar(x=weeks, y=net_open_interest_list, name="OI"),
                  row=3, col=2
                  )

    fig.update_xaxes(title_text="date")
    fig.update_yaxes(title_text="z_score", row=1, col=1)
    fig.update_yaxes(title_text="z_score", row=1, col=2)
    fig.update_yaxes(title_text="net contracts", row=2, col=1)
    fig.update_yaxes(title_text="net_contracts", row=2, col=2)
    fig.update_yaxes(title_text="z_score", row=3, col=1)
    fig.update_yaxes(title_text="net_contracts", row=3, col=2)

    fig.update_layout(
        width=1200,
        height=1250)
    return fig

@dash_app.callback(
    Output('cftc_positioning', 'children'),
    [Input('cftc_submit', 'n_clicks')],
    [State('cftc_input', 'value')]
)
def get_cftc_positioning(n_clicks, TICKER):
    num_of_entries = len(name_list)
    weeks = []
    for i in range(0, 156):
        weeks.append(datetime.now() - relativedelta(weeks=i))
    weeks.reverse()
    with open("metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)

    df = pd.DataFrame()
    done = False
    for asset_class in metrics:
        for metric in metrics[asset_class]:
            if metric == TICKER:
                list_of_i_and_date = get_list_of_i_and_date_for_metric(metrics[asset_class][metric], num_of_entries, date_list, name_list)

                investor = 'Open interest'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, z_score_three_years = get_values(
                    list_of_i_and_date, interest_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago,)
                df[investor] = [investor, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg, maximum, minimum, z_score_one_year, z_score_three_years]

                investor = 'Non_commercial'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
                z_score_three_years = get_values(list_of_i_and_date, non_comm_long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, non_comm_short_list)

                df[investor] = [investor, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg, maximum, minimum, z_score_one_year, z_score_three_years]

                investor = 'Commercial'
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
                z_score_three_years = get_values(list_of_i_and_date, comm_long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, comm_short_list)

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

dash_app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H4('Base Ticker'),
                    dcc.Dropdown(
                        id='cftc_input',
                        options=[{'label':x, 'value':x} for x in cftc_metrics_non_comm],
                        value='SPX',
                        placeholder='Select security',
                        multi=False
                    ),
                    html.Br(),
                    dbc.Button(
                        'Get chart',
                        id='cftc_submit'
                    ),
                ])
            ),
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col([
                html.H4('CFTC positioning'),
                html.Div(
                    id='cftc_positioning'
                )
            ])
        ]),
        html.Br(),
        dbc.Row([
            dcc.Graph(
                id='cftc_graph'
            )
        ]),
        dbc.Row(
            dbc.Col([
                html.Div([
                    html.Br(),
                    dcc.Dropdown(
                        id='cftc_input_df',
                        options=[{'label': x, 'value': x} for x in get_asset_lists()],
                        value=['SPX', 'VIX', 'Russel 2000', 'Dow Jones', 'Nasdaq', 'Nikkei Index',  '10Y UST', '2Y UST', '5Y UST', 'UST Bonds', '30D Fed Funds', '3M Eurodollar', 'Gold', 'USD', 'JPY', 'EUR', 'GBP', 'BTC',
                               'Crude Oil', 'Copper', 'Nat Gas', 'RBOB Gasoline', 'Silver', 'Platinum', 'Corn', 'Soybeans', 'Wheat', 'Live Cattle', 'Lean Hogs', 'Sugar', 'Cotton', 'Coffee', 'Cocoa', 'Orange Juice'],
                        placeholder='Select security',
                        multi=True
                    ),
                    html.Br(),
                    dbc.Button(
                        'Get CFTC datatable',
                        id='cftc_submit_df'
                    )
                ])
            ])
        ),
        html.Br(),
        html.Br(),
        dbc.Row([
            dbc.Col([
                html.H4("CFTC non-commercial positioning {}".format(datetime.today().date())),
                html.Br(),
                html.Div(
                    id='cftc_datatable_non_comm'
                ),
                html.Br(),
            ]),
            dbc.Col([
                html.H4("CFTC commercial positioning {}".format(datetime.today().date())),
                html.Br(),
                html.Div(
                    id='cftc_datatable_comm'
                )
            ])
        ])
    ])
])

if __name__ == '__main__':
    dash_app.run_server(debug=False)




