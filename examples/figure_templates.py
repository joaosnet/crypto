import dash_chart_editor as dce
from dash import Dash, html, Output, Input, dcc, no_update
import plotly.express as px
import plotly.io as pio


app = Dash(
    __name__, external_scripts=['https://cdn.plot.ly/plotly-2.18.2.min.js']
)

df = px.data.gapminder()


default_fig = px.scatter(
    df.query('year==2007'),
    x='gdpPercap',
    y='lifeExp',
    size='pop',
    color='continent',
    log_x=True,
    size_max=60,
)

default_fig['data'][0]['xsrc'] = 'gpdPercap'
default_fig['data'][0]['ysrc'] = 'lifeExp'

dropdown = dcc.Dropdown(
    id='template',
    options=[
        'plotly',
        'plotly_white',
        'plotly_dark',
        'ggplot2',
        'seaborn',
        'simple_white',
        'none',
    ],
    placeholder='Select a Figure Template',
    style={'marginBottom': 20, 'maxWidth': 430},
)

app.layout = html.Div([
    html.H4('Dash Chart Editor Demo with the Plotly Gapminder dataset'),
    dropdown,
    dce.DashChartEditor(
        dataSources=df.to_dict('list'),
        id='chartEditor',
        loadFigure=default_fig,
    ),
])


@app.callback(
    Output('chartEditor', 'loadFigure'),
    Input('template', 'value'),
    Input('chartEditor', 'figure'),
)
def setTemplate(v, figure):
    if v:
        default_fig = px.scatter(
            df.query('year==2007'),
            x='gdpPercap',
            y='lifeExp',
            size='pop',
            color='continent',
            log_x=True,
            size_max=60,
            template=pio.templates[v],
        )
        # figure['layout'].update({'template': pio.templates[v]})
        return default_fig
    return no_update


if __name__ == '__main__':
    app.run_server(debug=True, port=1234)
