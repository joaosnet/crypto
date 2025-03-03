"""
This demos saving the figure edited in dash-chart-editor
and displaying the figure code
"""

import dash_bootstrap_components as dbc
import dash_chart_editor as dce
import pandas as pd
from dash import Dash, Input, Output, html, no_update
from numpy import array

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/solar.csv'
)

app = Dash(
    __name__,
    external_scripts=['https://cdn.plot.ly/plotly-2.18.2.min.js'],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

default_figure = {
    'data': [
        {
            'connectgaps': True,
            'fill': 'tonext',
            'hoverinfo': 'r+theta',
            'hoveron': 'fills',
            'line': {'shape': 'spline', 'smoothing': 1.3},
            'mode': 'lines',
            'r': array(
                [
                    'California',
                    'Arizona',
                    'Nevada',
                    'New Mexico',
                    'Colorado',
                    'Texas',
                    'North Carolina',
                    'New York',
                ],
                dtype=object,
            ),
            'rsrc': 'State',
            'theta': array(
                [
                    'California',
                    'Arizona',
                    'Nevada',
                    'New Mexico',
                    'Colorado',
                    'Texas',
                    'North Carolina',
                    'New York',
                ],
                dtype=object,
            ),
            'thetasrc': 'State',
            'type': 'scatterpolar',
        }
    ],
    'layout': {
        'autosize': True,
        'mapbox': {'style': 'open-street-map'},
        'modebar': {'orientation': 'h'},
        'polar': {
            'angularaxis': {'type': 'category'},
            'radialaxis': {
                'autorange': True,
                'range': [0, 7],
                'type': 'category',
            },
        },
        'showlegend': False,
        'template': 'plotly',
        'uniformtext': {'minsize': 0, 'mode': False},
        'xaxis': {'autorange': True, 'range': [-1, 6]},
        'yaxis': {'autorange': True, 'range': [-1, 4]},
    },
}

chart_editor = dbc.Card(
    dce.DashChartEditor(
        id='chart-editor',
        loadFigure=default_figure,
        dataSources=df.to_dict('list'),
    )
)

code = dbc.Card(
    [
        dbc.CardHeader(dbc.Button('Update Code', id='save')),
        dbc.CardBody(html.Pre(id='output'), style={'minHeight': 200}),
    ],
    className='my-4',
)

app.layout = dbc.Container(
    [
        html.H4(
            'Dash Chart Editor Demo with the Plotly Solar dataset',
            className='text-center p-2',
        ),
        chart_editor,
        code,
    ],
)


@app.callback(Output('chart-editor', 'saveState'), Input('save', 'n_clicks'))
def save_figure(n):
    return True


@app.callback(
    Output('output', 'children'),
    Input('chart-editor', 'figure'),
)
def send_fig_to_dcc(figure):
    if figure:
        # cleaning data output for unnecessary columns
        figure = dce.cleanDataFromFigure(figure)

        # create Figure object from dash-chart-editor figure
        figure = dce.chartToPython(figure, df)
        return str(figure)
    return no_update


if __name__ == '__main__':
    app.run_server(debug=True)
