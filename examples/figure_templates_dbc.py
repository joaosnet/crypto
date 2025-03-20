import dash_chart_editor as dce
from dash import Dash, html, Output, Input, dcc, no_update
import plotly.express as px
import plotly.io as pio
from dash_bootstrap_templates import load_figure_template


templates = [
    'bootstrap',
    'cerulean',
    'cosmo',
    'cyborg',
    'darkly',
    'flatly',
    'journal',
    'litera',
    'lumen',
    'lux',
    'materia',
    'minty',
    'morph',
    'pulse',
    'quartz',
    'sandstone',
    'simplex',
    'sketchy',
    'slate',
    'solar',
    'spacelab',
    'superhero',
    'united',
    'vapor',
    'yeti',
    'zephyr',
]


# This loads all the figure template from dash-bootstrap-templates library,
# adds the templates to plotly.io and makes the first item the default figure template.
load_figure_template(templates)

dropdown = dcc.Dropdown(
    id='template',
    options=templates
    + [
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


app = Dash(
    __name__
)

df = px.data.gapminder()
dff = df[df.year == 1982]

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

app.layout = html.Div(
    [
        html.H4(
            'Dash Chart Editor Demo with Bootstrap Themed Figure Templates'
        ),
        dropdown,
        dce.DashChartEditor(dataSources=df.to_dict('list'), id='chartEditor', loadFigure=default_fig),
    ],
)


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
        return default_fig
    return no_update


if __name__ == '__main__':
    app.run(debug=True)
