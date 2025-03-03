import dash_chart_editor as dce
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objs as go
from dash import ALL, Dash, Input, Output, Patch, State, ctx, dcc, no_update


class ChartEditor:
    def __init__(  # noqa: PLR0913, PLR0917
        self,
        app,
        data_source=None,
        container_id='pattern-match-container',
        modal_size='85%',
        default_figures=None,
        figure_titles=None,  # Novo parâmetro para títulos específicos
        default_title='Figure',  # Renomeado de figure_title para default_title
        card_size=400,
        initial_cards=0,
    ):
        """
        Inicializa o editor de gráficos

        Args:
            app: Instância do Dash app
            data_source: Dicionário com os dados para o editor
            container_id: ID do container onde os cards serão renderizados
            modal_size: Tamanho do modal
            default_figures: Lista de figuras padrão para os cards.
            Se None ou lista menor que necessário,
            usa go.Figure() para completar
            figure_titles: Lista de títulos específicos para cada figura
            default_title: Título padrão quando não há título específico
            card_size: Tamanho dos cards em pixels
            initial_cards: Número de cards para criar inicialmente
        """
        self.app = app
        self.container_id = container_id
        self.card_size = card_size
        self.df1 = data_source
        self.data_source = data_source.to_dict(
            'list'
        ) or px.data.iris().to_dict('list')
        # Converter entrada única em lista se necessário
        if default_figures and not isinstance(default_figures, list):
            default_figures = [default_figures]
        self.default_figures = default_figures or [go.Figure()]

        # Inicializa os títulos
        if figure_titles and not isinstance(figure_titles, list):
            figure_titles = [figure_titles]
        self.figure_titles = figure_titles or []
        self.default_title = default_title
        self.initial_cards = initial_cards

        # Cria os componentes
        self.modal = self._create_modal(modal_size)
        self.store = dcc.Store(id=f'{container_id}-oldSum', data=0)

        # Registra as callbacks
        self._register_callbacks()

    def _create_modal(self, size):
        return dmc.Modal(
            children=[
                dmc.Group(
                    [
                        dmc.Title(
                            'Editando Gráfico com Identificador', order=3
                        ),
                        dmc.NumberInput(
                            id=f'{self.container_id}-chartId',
                            variant='unstyled',
                            min=0,
                            size='xl',
                            w='5%',
                        ),
                    ],
                    justify='center',
                    mt='md',
                ),
                dce.DashChartEditor(
                    dataSources=self.data_source,
                    id=f'{self.container_id}-editor',
                    style={'height': '60vh'},
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            'Reset', id=f'{self.container_id}-resetEditor'
                        ),
                        dmc.Button(
                            'Save', id=f'{self.container_id}-saveEditor'
                        ),
                        dmc.Button(
                            'Save & Close',
                            id=f'{self.container_id}-saveCloseEditor',
                            variant='outline',
                        ),
                    ],
                    justify='flex-end',
                    mt='md',
                ),
            ],
            id=f'{self.container_id}-editorMenu',
            size=size,
            opened=False,
        )

    def make_card(self, n_clicks):
        click_number = 0 if n_clicks is None else n_clicks
        # Seleciona figura padrão e título
        fig_index = click_number % len(self.default_figures)
        default_fig = self.default_figures[fig_index]

        # Seleciona título específico se disponível, senão usa o padrão
        if fig_index < len(self.figure_titles):
            title = self.figure_titles[fig_index]
        else:
            title = f'{self.default_title} {click_number + 1}'

        return dmc.Card(
            children=[
                dmc.CardSection(
                    dmc.Group(
                        [
                            dmc.Text(
                                title,  # Usa o título selecionado
                                fw=500,
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        'Editar ?',
                                        id={
                                            'type': f'{self.container_id}'
                                            + '-dynamic-edit',
                                            'index': n_clicks,
                                        },
                                        variant='light',
                                        size='sm',
                                    ),
                                    dmc.Button(
                                        'X',
                                        id={
                                            'type': f'{self.container_id}'
                                            + '-dynamic-delete',
                                            'index': n_clicks,
                                        },
                                        variant='subtle',
                                        color='red',
                                        size='sm',
                                    ),
                                ],
                                gap='xs',
                            ),
                        ],
                        justify='space-between',
                    ),
                    withBorder=True,
                    inheritPadding=True,
                    py='xs',
                ),
                dmc.CardSection(
                    dcc.Graph(
                        id={
                            'type': f'{self.container_id}-dynamic-output',
                            'index': n_clicks,
                        },
                        style={'height': 400},
                        figure=default_fig,  # Usa a figura selecionada
                    )
                ),
            ],
            withBorder=True,
            shadow='sm',
            radius='md',
            w=self.card_size,
            style={'width': 400, 'display': 'inline-block'},
            m='xs',
            id={
                'type': f'{self.container_id}-dynamic-card',
                'index': n_clicks,
            },
        )

    def _register_callbacks(self):
        @self.app.callback(
            Output(self.container_id, 'children'),
            Input(f'{self.container_id}-add-chart', 'n_clicks'),
        )
        def add_card(n_clicks):
            if n_clicks is None:
                return no_update
            patched_children = Patch()
            new_card = self.make_card(n_clicks)
            patched_children.append(new_card)
            return patched_children

        @self.app.callback(
            Output(self.container_id, 'children', allow_duplicate=True),
            Input(
                {'type': f'{self.container_id}-dynamic-delete', 'index': ALL},
                'n_clicks',
            ),
            State(
                {'type': f'{self.container_id}-dynamic-card', 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def remove_card(_, ids):
            cards = Patch()
            trigger_value = ctx.triggered[0].get('value')
            if trigger_value is not None and trigger_value > 0:
                for i in range(len(ids)):
                    if ids[i]['index'] == ctx.triggered_id['index']:
                        del cards[i]
                        return cards
            return no_update

        @self.app.callback(
            Output(f'{self.container_id}-editorMenu', 'opened'),
            Output(f'{self.container_id}-editor', 'loadFigure'),
            Output(f'{self.container_id}-chartId', 'value'),
            Output(f'{self.container_id}-oldSum', 'data'),
            Input(
                {'type': f'{self.container_id}-dynamic-edit', 'index': ALL},
                'n_clicks',
            ),
            State(
                {'type': f'{self.container_id}-dynamic-output', 'index': ALL},
                'figure',
            ),
            State(f'{self.container_id}-oldSum', 'data'),
            State(
                {'type': f'{self.container_id}-dynamic-card', 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def edit_card(edit, figs, oldSum, ids):
            edit_sum = sum(x or 0 for x in edit)
            oldSum = min(oldSum, edit_sum)
            if edit_sum > 0 and edit_sum > oldSum:
                oldSum = edit_sum
                if ctx.triggered[0]['value'] > 0:
                    for i in range(len(ids)):
                        if ids[i]['index'] == ctx.triggered_id['index']:
                            if figs[i]['data']:
                                return (
                                    True,
                                    figs[i],
                                    ctx.triggered_id['index'],
                                    oldSum,
                                )
                            return (
                                True,
                                {'data': [], 'layout': {}},
                                ctx.triggered_id['index'],
                                oldSum,
                            )
            return no_update, no_update, no_update, oldSum

        @self.app.callback(
            Output(
                f'{self.container_id}-editor',
                'loadFigure',
                allow_duplicate=True,
            ),
            Input(f'{self.container_id}-resetEditor', 'n_clicks'),
            State(
                {'type': f'{self.container_id}-dynamic-output', 'index': ALL},
                'figure',
            ),
            State(f'{self.container_id}-chartId', 'value'),
            State(
                {'type': f'{self.container_id}-dynamic-card', 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def reset_figure(n_clicks, figs, chartId, ids):
            if n_clicks is None:
                return no_update

            for i in range(len(ids)):
                if ids[i]['index'] == chartId:
                    if figs[i].get('data'):
                        return figs[i]
            return {'data': [], 'layout': {}}

        @self.app.callback(
            Output(f'{self.container_id}-editor', 'saveState'),
            Input(f'{self.container_id}-saveEditor', 'n_clicks'),
            Input(f'{self.container_id}-saveCloseEditor', 'n_clicks'),
        )
        def save_figure(n, n1):
            if n or n1:
                return True

        @self.app.callback(
            Output(
                f'{self.container_id}-editorMenu',
                'opened',
                allow_duplicate=True,
            ),
            Input(f'{self.container_id}-saveCloseEditor', 'n_clicks'),
            prevent_initial_call=True,
        )
        def close_editor(n):
            if n:
                return False
            return no_update

        @self.app.callback(
            Output(self.container_id, 'children', allow_duplicate=True),
            Output('code-highlight', 'code'),
            Input(f'{self.container_id}-editor', 'figure'),
            State(f'{self.container_id}-chartId', 'value'),
            State(
                {'type': f'{self.container_id}-dynamic-card', 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def save_to_card(f, v, ids):
            if f:
                figs = Patch()

                for i in range(len(ids)):
                    if ids[i]['index'] == v:
                        figs[i]['props']['children'][1]['props']['children'][
                            'props'
                        ]['figure'] = f
                        figure = dce.chartToPython(f, self.df1)
                        return figs, str(figure)
            return no_update, no_update

    def get_layout(self):
        # Criar cards iniciais
        initial_children = (
            [self.make_card(i) for i in range(self.initial_cards)]
            if self.initial_cards > 0
            else []
        )

        return dmc.Container(
            [
                self.store,
                dmc.Button(
                    'Adicionar Novo Gráfico?',
                    id=f'{self.container_id}-add-chart',
                    variant='filled',
                    n_clicks=self.initial_cards,
                ),
                dmc.Group(
                    id=self.container_id,
                    children=initial_children,
                    className='mt-4',
                ),
                self.modal,
            ],
            fluid=True,
            px=0,
            py=0,
        )


if __name__ == '__main__':
    import plotly.express as px
    from dash import _dash_renderer  # noqa: PLC2701

    _dash_renderer._set_react_version('18.2.0')

    app = Dash(__name__)

    # Criar múltiplas figuras padrão de exemplo
    df = px.data.iris()
    default_figs = [
        px.scatter(df, x='sepal_length', y='sepal_width', color='species'),
        px.box(df, x='species', y='petal_length'),
        px.histogram(df, x='sepal_width', color='species'),
    ]

    # Definir títulos específicos para cada figura
    figure_titles = [
        'Scatter Plot - Sepal Length vs Width',
        'Box Plot - Petal Length by Species',
        'Histogram - Sepal Width Distribution',
    ]

    # Usar o editor com múltiplas figuras e títulos
    editor = ChartEditor(
        app,
        data_source=df,
        default_figures=default_figs,
        figure_titles=figure_titles,  # Passa os títulos específicos
        default_title='Iris Chart',  # Título padrão caso necessário
        card_size=400,
        initial_cards=3,  # Criar 3 cards iniciais com diferentes visualizações
    )

    app.layout = dmc.MantineProvider(
        [editor.get_layout()],
        id='mantine-provider',
        forceColorScheme='light',
    )

    app.run_server(debug=True, port=1234)
